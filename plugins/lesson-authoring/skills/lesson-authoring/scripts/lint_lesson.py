#!/usr/bin/env python3
"""Surface annotated *alternate acceptable calls* in coaching-PBN lessons.

These lessons are guided walk-throughs (PBN + `[show]`/`[BID]`/`[ACCEPT]`
coaching blocks), not blind bidding quizzes. In that format the coaching prose
is *meant* to name and justify each call, so a generic "answer must not appear
in the question" leak check produces almost all false positives (the first call
is often the given premise — e.g. the 1NT opening in a transfer lesson — not the
decision being taught). Judgment-heavy quality review is therefore left to the
skill's human/Claude review pass.

The ONE signal that is mechanically reliable here is the `[ACCEPT xxx]` marker:
a board that explicitly accepts a second call at a decision point. For BEGINNER
lessons the skill's default is exactly one correct call per decision, so every
beginner board carrying an alternate is worth a human's eyes — either tighten
the deal so the call is unique, or consciously accept the ambiguity.

This is an ADVISORY surfacer, not a gate: it reports, it does not veto.

Usage:
    python lint_lesson.py <file.pbn | directory> [more paths ...]

A directory is scanned for *.pbn; a sibling toc.json (if present) supplies each
lesson's difficulty when a board has no [Difficulty] tag of its own.

Exit status: 0 = no alternates found, 1 = alternates reported, 2 = bad input.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field

SEATS = ["N", "E", "S", "W"]  # clockwise
CALL_RE = re.compile(r"^(?:Pass|X|XX|AP|[1-7](?:NT?|[SHDC]))$", re.IGNORECASE)
TAG_RE = re.compile(r'\[(\w+)\s+"([^"]*)"\]')


@dataclass
class Alternate:
    lesson: str
    board: str
    beginner: bool
    primary: str | None   # the coached call this alternate attaches to
    alt: str              # the accepted alternate call/play


@dataclass
class Board:
    lesson: str
    number: str
    difficulty: str | None
    auction_seat: str | None
    calls: list[str] = field(default_factory=list)
    south_calls: list[str] = field(default_factory=list)
    alternates: list[tuple[str | None, str]] = field(default_factory=list)


def _south_calls(seat: str | None, calls: list[str]) -> list[str]:
    if not seat or seat not in SEATS:
        return []
    start = SEATS.index(seat)
    return [c for k, c in enumerate(calls) if SEATS[(start + k) % 4] == "S"]


def _extract_alternates(comment: str) -> list[tuple[str | None, str]]:
    """Pair each [ACCEPT x] with the [BID y] chunk it sits in (None if intro)."""
    parts = re.split(r"\[BID\s+([^\]]+)\]", comment)
    out: list[tuple[str | None, str]] = []
    # parts[0] is the intro chunk; then (call, prose) pairs follow.
    for alt in re.findall(r"\[ACCEPT\s+([^\]]+)\]", parts[0], re.IGNORECASE):
        out.append((None, alt.strip()))
    for k in range(1, len(parts), 2):
        call = parts[k].strip()
        prose = parts[k + 1] if k + 1 < len(parts) else ""
        for alt in re.findall(r"\[ACCEPT\s+([^\]]+)\]", prose, re.IGNORECASE):
            out.append((call, alt.strip()))
    return out


def parse_file(path: str) -> list[Board]:
    """Parse a coaching PBN into boards. Robust to [Play] sections and to a
    single unclosed comment brace (bounded at the next board boundary)."""
    text = open(path, encoding="utf-8").read()
    lesson_default = os.path.splitext(os.path.basename(path))[0]
    boards: list[Board] = []
    cur: dict | None = None
    cur_lesson = lesson_default
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = TAG_RE.match(line.strip())
        if m:
            tag, val = m.group(1), m.group(2)
            if tag == "Event":
                cur_lesson = val or lesson_default
            elif tag == "Board":
                if cur:
                    boards.append(_finish(cur))
                cur = {"lesson": cur_lesson, "number": val, "difficulty": None,
                       "auction_seat": None, "calls": [], "comment": ""}
            elif cur is not None and tag == "Difficulty":
                cur["difficulty"] = val
            elif cur is not None and tag == "Auction":
                cur["auction_seat"] = val
                j = i + 1
                while j < len(lines):
                    s = lines[j].strip()
                    if not s or s.startswith("[") or s.startswith("{"):
                        break
                    cur["calls"].extend(t for t in s.split() if CALL_RE.match(t))
                    j += 1
                i = j - 1
            i += 1
            continue
        if cur is not None and line.lstrip().startswith("{"):
            buf: list[str] = []
            depth = 0
            while i < len(lines):
                l = lines[i]
                if buf and re.match(r'\s*\[(Board|Event)\b', l):
                    i -= 1
                    break
                depth += l.count("{") - l.count("}")
                buf.append(l)
                if depth <= 0 and "}" in l:
                    break
                i += 1
            cur["comment"] = "\n".join(buf).strip().lstrip("{").rstrip("}")
        i += 1
    if cur:
        boards.append(_finish(cur))
    return boards


def _finish(d: dict) -> Board:
    b = Board(lesson=d["lesson"], number=d["number"], difficulty=d["difficulty"],
              auction_seat=d["auction_seat"], calls=d["calls"])
    b.south_calls = _south_calls(d["auction_seat"], d["calls"])
    b.alternates = _extract_alternates(d["comment"])
    return b


def load_toc(path: str) -> dict[str, str]:
    """Map lesson id -> difficulty from a toc.json, if one sits alongside."""
    toc: dict[str, str] = {}
    if os.path.isfile(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            return toc
        for cat in data.get("categories", []):
            for les in cat.get("lessons", []):
                if "id" in les:
                    toc[les["id"]] = (les.get("difficulty") or "").lower()
    return toc


def collect(paths: list[str]) -> tuple[list[Board], dict[str, str]]:
    files: list[str] = []
    toc: dict[str, str] = {}
    for p in paths:
        if os.path.isdir(p):
            files.extend(sorted(glob.glob(os.path.join(p, "*.pbn"))))
            toc.update(load_toc(os.path.join(p, "toc.json")))
        elif p.endswith(".pbn"):
            files.append(p)
            toc.update(load_toc(os.path.join(os.path.dirname(p), "toc.json")))
    boards: list[Board] = []
    for f in files:
        boards.extend(parse_file(f))
    return boards, toc


def find_alternates(boards: list[Board], toc: dict[str, str]) -> list[Alternate]:
    out: list[Alternate] = []
    for b in boards:
        if not b.alternates:
            continue
        diff = (b.difficulty or toc.get(b.lesson, "")).lower()
        beginner = diff == "beginner"
        for primary, alt in b.alternates:
            out.append(Alternate(b.lesson, b.number, beginner, primary, alt))
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    boards, toc = collect(argv[1:])
    if not boards:
        print("No boards parsed. Point at a .pbn file or a directory of them.")
        return 2
    alts = find_alternates(boards, toc)
    beg = [a for a in alts if a.beginner]
    nlessons = len({b.lesson for b in boards})
    print(f"Scanned {len(boards)} boards across {nlessons} lessons.")
    print(f"Alternate-call annotations: {len(alts)} "
          f"({len(beg)} on beginner lessons).\n")
    if not alts:
        print("Clean: no [ACCEPT] alternates. (Quality/leak review is the "
              "skill's judgment pass, not this script.)")
        return 0
    if beg:
        print("Beginner boards with an alternate accepted call "
              "(default is one correct call — tighten the deal or accept the "
              "ambiguity deliberately):")
        for a in beg:
            anchor = f" after {a.primary}" if a.primary else ""
            print(f"  ✗ {a.lesson} #{a.board}{anchor}: also accepts {a.alt!r}")
    other = [a for a in alts if not a.beginner]
    if other:
        print(f"\nNon-beginner boards with alternates ({len(other)}) — "
              "usually fine; listed for completeness:")
        for a in other:
            anchor = f" after {a.primary}" if a.primary else ""
            print(f"  · {a.lesson} #{a.board}{anchor}: also accepts {a.alt!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
