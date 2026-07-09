# Board Difficulty — two systems

Difficulty has two independent parts. Keep them separate; conflating them is
what makes ordering go wrong.

1. **Base tier — the topic's inherent band.** A squeeze lesson is advanced; a
   count-your-tricks lesson is easy. This is roughly **constant within a
   lesson**, so it *places the lesson* but cannot order boards inside it.
2. **Gradient — how one board compares to others in the same lesson.** Built
   only from factors that **vary board to board**, so difficulty can rise
   easy→hard *within* a fixed tier. This is what you sort on, and what
   `scripts/difficulty.py` computes.

Rate relative to the lesson's AUDIENCE, not to an expert.

## Gradient factors (mechanical — `difficulty.py` reads these)

**Both lesson types**

- **Contract level** is the anchor: partscore `0` · game `+1` · slam `+3`.
  A slam is a large jump; a slam in a beginner lesson almost never belongs.

**Bidding boards, add**

- **Competition** — opponents enter the auction: `+1`.
- **Length** — each South decision beyond the first: `+1` (cap `+3`). Longer
  auctions ask more of the student.
- **Shape** — balanced `0` · unbalanced `+1` · wild or two-suited `+2`.
  Balanced hands are easier to bid: strength is narrowly defined by the opening
  or rebid (12–14, 15–17, 18–19). Unbalanced hands must spend bids showing shape
  and can't pin strength down as tightly (Robert Todd).

**Cardplay boards, add**

- **Defense / opening lead** (`[ROLE leader]`): `+1` — reading declarer's hidden
  hand is harder than playing with dummy in view.
- **Length** — play stages beyond the standard four: `+1` (cap `+2`).
- **Preparation** — the line needs a setup move (duck, strip, eliminate, rectify
  the count, hold-up, endplay) before the theme: `+1`.

The gradient is calibrated: across ~2,700 human-tagged boards its mean rises
monotonically with the `[Difficulty]` label (beginner < intermediate <
advanced). Trust it for *ordering and outlier detection*, not as an absolute
truth about a single board.

## Judgment factors (a human's call — not scored)

HCP sitting exactly on a range boundary (a good 14 vs a bad 14); which of
several conventions applies; inference from the auction; deception. Weigh these
when the mechanical score feels wrong for a board, and say so.

## Cardplay base tier (topic band)

Set from the lesson's technique, not per board:

| Tier | Techniques |
|---|---|
| 1 | count / cash top tricks, simple finesse, hold-up |
| 2 | double / repeated / ruffing finesse, suit promotion, side-suit ruff timing |
| 3 | two-way finesse, choice of finesses, "to finesse or not", rectify the count |
| 4 | strip-and-endplay, simple squeeze |
| 5 | double squeeze, show-up squeeze, squeeze-endplay |

Within an advanced tier you still grade with the gradient — a textbook automatic
squeeze is the opener; one that needs the count rectified first, or reads a
defender's distribution, comes later.

## Sequencing rules

- Order boards so difficulty **generally rises toward the end**. Open with the
  lesson's easiest boards; a slight "stretch" board may close it.
- Beginner lessons: the first third should be the lowest-gradient boards; avoid
  slams entirely.
- **Prefer representative hands over variety for its own right.** A board whose
  gradient sits well above the rest of the lesson (`difficulty.py` flags score ≥
  the lesson's median + 2) is usually an *outlier the "add variety" instinct
  pulled in* — drop it or move it to a harder lesson rather than keeping it for
  contrast. Variety in *theme* is good; variety in *difficulty* that spikes a
  beginner is not.
- If a lesson's gradient comes out flat, that's fine — a tightly-scoped lesson
  can be uniformly easy. Don't manufacture a hard board to force a slope.

Run `python scripts/difficulty.py <lesson.pbn | collection-dir>` to see the
per-board scores, the calibration table, and the outlier flags.
