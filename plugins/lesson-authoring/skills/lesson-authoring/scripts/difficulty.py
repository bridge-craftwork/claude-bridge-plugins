#!/usr/bin/env python3
"""Estimate per-board difficulty and flag outliers that hurt lesson ordering.

Two independent systems (see references/difficulty-rubric.md):

  * BASE TIER — the topic's inherent band (a squeeze lesson is advanced, a
    top-tricks lesson is easy). Roughly CONSTANT within a lesson, so it can't
    order boards inside one. It's editorial; this script does not compute it.

  * GRADIENT — a per-board score from board-VARYING mechanical factors, used to
    order boards easy->hard WITHIN a lesson and to spot outliers. Computed here.

GRADIENT FACTORS (all mechanical, read straight from the PBN):

  both:      contract level      partscore 0 · game +1 · slam +3
  bidding:   + competition (opponents bid)                     +1
             + extra South decisions (beyond the first), cap   +3
             + hand shape   balanced 0 · unbalanced +1 · wild/two-suiter +2
               (balanced hands are easier to bid — strength is narrowly
               defined by the opening/rebid; unbalanced hands spend bids on
               shape — Robert Todd)
  cardplay:  + defense / opening-lead board                    +1
             + extra play stages beyond the standard four, cap +2
             + a preparatory technique in the prose (duck / strip / eliminate /
               rectify the count / hold-up / endplay)           +1

The score is validated: across ~2,700 human-tagged boards its mean rises
monotonically with the [Difficulty] label (beginner < intermediate < advanced).

Judgment factors it deliberately does NOT try to compute: HCP exactly at a range
boundary, which of several conventions applies, deceptive/ inference plays.
Those stay a human's call in review.

Usage:  python difficulty.py <file.pbn | directory> [more paths ...]
Exit:   0 = no outliers, 1 = outliers flagged, 2 = bad input.
"""
from __future__ import annotations
import glob, json, os, re, sys
from statistics import mean, median

CALL_RE = re.compile(r"^(?:Pass|X|XX|AP|[1-7](?:NT?|[SHDC]))$", re.IGNORECASE)
SEATS = ["N", "E", "S", "W"]
PREP = re.compile(r"\b(duck|strip|eliminat|rectif|endplay|throw[- ]?in|"
                  r"hold[- ]?up)\w*", re.IGNORECASE)


def contract_points(contract: str) -> tuple[int, str]:
    m = re.match(r"([1-7])\s*(NT?|[SHDC♠♥♦♣])", contract or "", re.IGNORECASE)
    if not m:
        return 0, "?"
    lvl = int(m.group(1)); strain = m.group(2).upper()[0]
    if lvl >= 6:
        return 3, "slam"
    game = (strain == "N" and lvl >= 3) or (strain in "HS" and lvl >= 4) \
        or (strain in "CD" and lvl >= 5)
    return (1, "game") if game else (0, "part")


def shape_points(deal: str, seat: str = "S") -> int:
    try:
        hand = deal.split(":", 1)[1].split()[SEATS.index(seat)]
    except Exception:
        return 0
    lens = sorted((len(x) for x in hand.split(".")), reverse=True)
    if len(lens) != 4:
        return 0
    if tuple(lens) in {(4, 3, 3, 3), (4, 4, 3, 2), (5, 3, 3, 2)}:
        return 0                                            # balanced
    if lens[-1] == 0 or lens[0] >= 7 or (lens[0] >= 5 and lens[1] >= 5):
        return 2                                            # wild / two-suited
    return 1                                                # mild unbalanced


def south_calls(seat, calls):
    if seat not in SEATS:
        return []
    s = SEATS.index(seat)
    return [c for k, c in enumerate(calls) if SEATS[(s + k) % 4] == "S"]


def boards_of(path):
    text = open(path, encoding="utf-8").read()
    lesson = os.path.splitext(os.path.basename(path))[0]
    for blk in re.split(r'(?=\[Board ")', text):
        if '[Board "' not in blk:
            continue
        num = int(re.search(r'\[Board "(\d+)"\]', blk).group(1))
        contract = (re.search(r'\[Contract "([^"]+)"\]', blk) or [0, ""])[1]
        diff = (re.search(r'\[Difficulty "([^"]+)"\]', blk) or [0, ""])[1].lower()
        deal = (re.search(r'\[Deal "([^"]+)"\]', blk) or [0, ""])[1]
        auc = re.search(r'\[Auction "(\w)"\]\s*\n(.*?)\n\{', blk, re.S)
        seat = auc.group(1) if auc else "?"
        calls = [t for t in (auc.group(2).split() if auc else []) if CALL_RE.match(t)]
        yield dict(
            lesson=lesson, num=num, contract=contract, diff=diff, deal=deal,
            seat=seat, calls=calls,
            cardplay=("[Play " in blk) or ("[ROLE " in blk),
            nstage=len(re.findall(r"\[STAGE ", blk)),
            defense="[ROLE leader]" in blk,
            nbid=len(re.findall(r"\[BID ", blk)),
            prep=bool(PREP.search(blk)))


def gradient(b) -> tuple[int, str]:
    pts, band = contract_points(b["contract"])
    score = pts
    if b["cardplay"]:
        if b["defense"]:
            score += 1
        score += min(2, max(0, b["nstage"] - 4))
        if b["prep"]:
            score += 1
    else:
        if any(t.lower() not in ("pass", "ap") and (k % 4 in (1, 3))
               for k, t in enumerate(b["calls"])):
            score += 1
        ndec = len(south_calls(b["seat"], b["calls"])) or b["nbid"]
        score += min(3, max(0, ndec - 1))
        score += shape_points(b["deal"], b["seat"])
    return score, band


def load(paths):
    toc, files = {}, []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, "*.pbn")))
            tp = os.path.join(p, "toc.json")
            if os.path.isfile(tp):
                try:
                    d = json.load(open(tp))
                    for c in d.get("categories", []):
                        for l in c.get("lessons", []):
                            toc[l["id"]] = (l.get("difficulty") or "").lower()
                except Exception:
                    pass
        elif p.endswith(".pbn"):
            files.append(p)
    lessons = {}
    for f in files:
        for b in boards_of(f):
            b["score"], b["band"] = gradient(b)
            b["lessondiff"] = b["diff"] or toc.get(b["lesson"], "")
            lessons.setdefault(b["lesson"], []).append(b)
    return lessons


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    lessons = load(argv[1:])
    if not lessons:
        print("No boards parsed. Point at a .pbn file or a directory.")
        return 2
    nb = sum(len(v) for v in lessons.values())
    calib, slam_easy, spikes = {}, [], []
    for lesson, bs in lessons.items():
        bs.sort(key=lambda x: x["num"])
        med = median(b["score"] for b in bs) if bs else 0
        for b in bs:
            if b["lessondiff"]:
                calib.setdefault(b["lessondiff"], []).append(b["score"])
            # a slam in a beginner lesson is the clearest "left this in for
            # variety but it doesn't belong" case
            if b["band"] == "slam" and b["lessondiff"] == "beginner":
                slam_easy.append(b)
            # a board sitting well above its own lesson's level (variety
            # over-reach). 'mixed' lessons are meant to span, so skip them.
            if len(bs) >= 5 and b["lessondiff"] != "mixed" and b["score"] >= med + 2:
                spikes.append((b, med))

    print(f"Scored {nb} boards across {len(lessons)} lessons.\n")
    if calib:
        print("── Calibration: mean gradient by [Difficulty] label "
              "(should rise) ──")
        for k in ["beginner", "intermediate", "advanced", "mixed"] + \
                [x for x in calib if x not in
                 ("beginner", "intermediate", "advanced", "mixed")]:
            if k in calib:
                xs = calib[k]
                print(f"  {k:13} n={len(xs):4}  mean={mean(xs):.2f}  "
                      f"range={min(xs)}-{max(xs)}")
        print()
    print(f"── Slam contracts in beginner lessons ({len(slam_easy)}) — almost "
          "always drop or move ──")
    for b in slam_easy:
        print(f"  ✗ {b['lesson']} #{b['num']}: {b['contract']} slam "
              f"[score {b['score']}]")
    print(f"\n── Within-lesson difficulty spikes ({len(spikes)}) — score ≥ its "
          "lesson's median+2; candidates the 'add variety' guidance over-reached "
          "on ──")
    for b, med in sorted(spikes, key=lambda x: (-(x[0]['score'] - x[1]),
                                                x[0]['lesson'], x[0]['num']))[:25]:
        print(f"  ✗ {b['lesson']} #{b['num']}: score {b['score']} vs lesson "
              f"median {med:g}  ({b['contract']} {b['band']}, "
              f"lesson={b['lessondiff'] or '?'})")
    if len(spikes) > 25:
        print(f"  … +{len(spikes) - 25} more (run on one lesson to see its own)")
    return 1 if (slam_easy or spikes) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
