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

## Workflow

Follow these steps in order for every lesson generation task:

1. **Read the source deals.** Parse the PBN file(s) the user points at. Confirm
   the deal count and any lesson topic/theme before generating.
2. **Establish the audience level.** Ask if not stated: beginner, intermediate,
   or advanced. Most lessons here are BEGINNER. The disambiguation rule below
   depends on this.
3. **Select and repair deals** (see Deal Selection and Disambiguation).
4. **Rate each deal's difficulty** on the 1–5 rubric in
   `references/difficulty-rubric.md`. Record the rating in your working notes
   and in the lesson metadata if the output format supports it.
5. **Order the lesson** (see Difficulty Ordering).
6. **Write student prompts** (see Leak-Free Prompts). This is the step that has
   historically gone wrong most often — slow down here.
7. **Lint before delivering.** Run `scripts/lint_lesson.py` on the generated
   lesson and fix every finding before presenting the result. Do not present a
   lesson that fails lint.

## Deal Selection and Disambiguation

**For beginner lessons, every deal must have exactly one correct call at the
decision point being taught**, judged strictly by the bidding system of the
lesson (default: Standard American with the conventions covered so far in the
course).

When a candidate deal is ambiguous — two or more defensible calls — do NOT keep
the deal and annotate alternate allowable bids. Beginners cannot process "both
1NT and 2♣ are acceptable here"; it undermines the rule being taught. Instead,
**repair the deal by exchanging cards between hands until the ambiguity
disappears**, then re-verify:

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

Order boards by strictly non-decreasing difficulty. Never open a lesson with
its hardest board — early failure discourages beginners, and early success
builds the confidence needed for the harder boards later.

- Rate every board 1–5 using `references/difficulty-rubric.md` BEFORE
  sequencing. Do not sequence by gut feel.
- The first third of a beginner lesson must contain only boards rated 1–2.
- The final board may be a slight "stretch" board (one level above the lesson's
  center of gravity) if it directly reinforces the lesson theme.
- If the available deals cluster at one difficulty, say so and suggest sourcing
  or repairing deals to fill the gradient, rather than silently producing a
  flat or front-loaded lesson.

## Iterating on this skill

This skill is jointly maintained and is expected to evolve. When the user
corrects a behavior during a session ("don't do X, prefer Y"), offer to encode
the correction into this SKILL.md (or its reference files) as a candidate
change they can commit to the plugin repo, so both maintainers benefit.
