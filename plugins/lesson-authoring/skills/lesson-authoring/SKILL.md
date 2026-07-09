---
name: lesson-authoring
description: Generate, curate, or revise bridge lessons from PBN deal files. Use this skill whenever the user asks to create a lesson, generate homework, curate deals, build a lesson set, select boards for a class, write bidding quizzes, or produce any student-facing material from PBN files — even if they don't say "lesson" explicitly. Also use when reviewing or fixing an existing generated lesson.
---

# Bridge Lesson Authoring

Generate student-facing bridge lessons from PBN deal repositories. The output of
this skill is teaching material for real students — mostly beginners at a
retirement community or on Zoom — so pedagogical quality matters more than
technical completeness. A lesson that confuses a beginner is worse than no
lesson.

**These rules are pedagogical defaults, not hard gates.** Apply them when
authoring, and flag violations when reviewing — but when a rule and good
judgment conflict, surface the tension to the user and let them decide. Never
refuse to deliver a lesson, and never silently drop or alter a deal, solely
because a rule wasn't met. The point is to raise quality and make problems
visible, not to block work.

## Workflow

Follow these steps in order for every lesson generation task:

1. **Read the source deals.** Parse the PBN file(s) the user points at. Confirm
   the deal count and any lesson topic/theme before generating.
2. **Establish the audience level.** Ask if not stated: beginner, intermediate,
   or advanced. Most lessons here are BEGINNER. The disambiguation rule below
   depends on this.
3. **Select and repair deals** (see Deal Selection and Disambiguation).
4. **Rate each deal's difficulty** using `references/difficulty-rubric.md` —
   the topic's base tier plus the per-board gradient (contract level, shape,
   competition, length). `scripts/difficulty.py` computes the gradient and flags
   outliers. Record the rating in your working notes and in the lesson metadata
   if the output format supports it.
5. **Order the lesson** (see Difficulty Ordering).
6. **Write student prompts** (see Leak-Free Prompts). This is the step that has
   historically gone wrong most often — slow down here.
7. **Survey before delivering.** Run `scripts/lint_lesson.py` on the lesson —
   or on a whole collection directory. It surveys the coaching PBN for
   `[ACCEPT]` alternate-call markers (the ambiguity signal) and flags beginner
   boards that carry one. Freshly authored lessons usually have none, so this
   matters most when reviewing the existing base or issue-resolution edits (see
   "Reviewing an existing lesson base"). Treat findings as advisory: address
   clear problems, surface judgment calls to the user, and never withhold the
   lesson over them. Leak-freedom and difficulty ordering are judgment calls for
   your own review, not things this script checks.

## Deal Selection and Disambiguation

**For beginner lessons, each deal should have exactly one correct call at the
decision point being taught**, judged by the bidding system of the lesson
(default: Standard American with the conventions covered so far in the course).
Treat this as a strong default, not an absolute bar.

When a candidate deal is ambiguous — two or more defensible calls — prefer not
to keep the deal and annotate alternate allowable bids. Beginners struggle to
process "both 1NT and 2♣ are acceptable here"; it can undermine the rule being
taught. The preferred fix is to **repair the deal by exchanging cards between
hands until the ambiguity disappears**, then re-verify. If a clean repair isn't
worth it, flag the ambiguity to the user and let them decide rather than
blocking the lesson:

- Exchange the minimum number of cards needed. Prefer swapping low cards or
  adjusting a single honor between the problem hand and a hand not involved in
  the teaching point.
- After any exchange, re-check ALL FOUR hands and the full expected auction, not
  just the decision point you fixed. A card swap can create a new ambiguity or
  break an earlier call in the auction.
- Preserve the deal's teaching point. If repair would require gutting the hand,
  discard the deal and pick another from the repository instead.
- Record what was changed (e.g., "swapped ♥Q West↔♠4 North to make 1NT the
  unique opening") in an internal comment or commit note so a human can audit
  the repair. Never surface repair notes to students.

**When resolving a reported issue on an existing beginner board, prefer to
rework the deal over adding an `[ACCEPT]` alternate.** Marking a second call
acceptable is the easy patch, but it quietly turns a single-answer board into an
ambiguous one — the exact thing the beginner rule guards against, and a
recurring shortcut worth resisting. Repair the deal so the intended call is
unique. Only fall back to `[ACCEPT]` when reworking would gut the teaching
point, and when you do, say so explicitly to the user rather than adding it
silently. `scripts/lint_lesson.py` surveys a collection for boards where this
shortcut was taken, so the pattern is auditable after the fact.

For intermediate/advanced lessons, mild ambiguity may itself be the teaching
point — but only when the user explicitly frames the lesson that way. Default
to the beginner rule when in doubt.

## Leak-Free Prompts

The question shown to the student must never reveal or hint at the answer. This
is the most chronic failure mode — check every prompt against this list:

- **No answer words in the question.** The correct call (e.g., "2♥", "Pass",
  "Double") must not appear anywhere in the prompt text, including in
  parenthetical asides, hand commentary, or the lesson's intro paragraph for
  that board.
- **No evaluative framing.** Do not write "With this strong hand..." or "Holding
  such good support...". Describe nothing about the hand's quality — the
  student sees the cards; evaluation IS the exercise.
- **No partner/opponent hand information** the student wouldn't legitimately
  have at that point in the auction.
- **No leading auction context.** Presenting the auction so far is fine;
  characterizing it ("partner has shown a strong hand, so...") is not, unless
  interpreting that call is a previously-taught skill being assumed.
- **No structural leaks.** If every "should you invite?" question in a lesson
  has the answer "yes," the lesson leaks structurally. Mix in deals where the
  correct answer is the less exciting call (Pass is a bid too).

**The re-read test:** after writing each prompt, re-read it as a student who
has not yet decided on a bid. If anything in the text nudges toward the answer,
rewrite. See `examples/prompt-dos-and-donts.md` for concrete before/after
pairs — read that file whenever writing or reviewing prompts.

Answers and explanations belong ONLY in the answer/solution section, never in
the question. The explanation there should teach the reasoning, not just state
the call.

## Difficulty Ordering

Order boards so difficulty generally rises toward the end. Avoid opening a
lesson with its hardest board — early failure discourages beginners, and early
success builds the confidence needed for the harder boards later. Score with the
two-system rubric in `references/difficulty-rubric.md` (base tier + per-board
gradient) BEFORE sequencing; `scripts/difficulty.py` computes the gradient.

- The first third of a beginner lesson should be its lowest-gradient boards; no
  slams in a beginner lesson at all.
- The final board may be a slight "stretch" (a notch above the lesson's center
  of gravity) if it reinforces the theme.
- **Don't over-reach for variety.** The instinct to "include a variety of hands"
  is the recurring cause of a beginner lesson picking up a slam or a wild
  two-suiter that scores far above the rest. Variety in *theme* is good; a board
  whose gradient sits well above its lesson (`difficulty.py` flags score ≥ the
  lesson median + 2) is usually an outlier to **drop or move up**, not keep for
  contrast. Prefer representative hands.
- A flat gradient is acceptable for a tightly-scoped lesson — don't manufacture
  a hard board to force a slope. If deals genuinely cluster and you need a
  gradient, say so and suggest sourcing more, rather than jamming in an outlier.

## Reviewing an existing lesson base

The user may point this skill at lessons already authored (potentially hundreds)
and ask how they measure up against these standards. Treat this as a read-only
audit, not a rewrite:

- **Report, don't mutate.** Produce findings; do not edit, repair, or delete any
  existing lesson unless the user explicitly asks you to change specific ones.
  These are already-shipped materials — the default is to surface issues, not
  silently "fix" them.
- **Start with the mechanical survey.** Run `scripts/lint_lesson.py` on the
  collection to list every board carrying an `[ACCEPT]` alternate, beginner
  boards first. That is the one signal a script can find reliably in this
  guided-walk-through format — it pinpoints where ambiguity was papered over
  instead of repaired.
- **Then apply judgment for what a script can't see.** Leak-freedom in
  particular is a judgment call here: the coaching prose is *meant* to name and
  justify each call, and the first call is often the given premise (e.g. the
  1NT opening in a transfer lesson), not the answer — so a naive "answer word
  appears" check is almost all false positives. Read the intro chunk (shown
  before the student's decision) and ask whether it nudges toward the taught
  call.
- **Work in batches** for a large corpus. Summarize counts ("X of Y beginner
  boards annotate an alternate call"), then list specifics, so the user can
  triage rather than drown in a flat list.
- **Distinguish "wrong" from "stylistically different."** A lesson authored
  under older conventions is not automatically a defect; call out genuine
  student-facing problems and note where something merely diverges from the
  current default.

Offer the user a concrete next step after the audit (e.g., "want me to fix the
12 clear leaks?") rather than acting on the findings unprompted.

## Iterating on this skill

This skill is jointly maintained and is expected to evolve. When the user
corrects a behavior during a session ("don't do X, prefer Y"), offer to encode
the correction into this SKILL.md (or its reference files) as a candidate
change they can commit to the plugin repo, so both maintainers benefit.
