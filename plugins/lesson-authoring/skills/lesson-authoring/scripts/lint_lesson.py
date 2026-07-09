#!/usr/bin/env python3
"""Lint a generated bridge lesson for the two mechanically checkable rules:

  1. Answer leakage — the correct call must not appear in the question text.
  2. Difficulty ordering — board difficulty ratings must be non-decreasing,
     and (for beginner lessons) the first third must be rated <= 2.

ADAPTATION REQUIRED: this script assumes a JSON lesson format described below.
Adjust ``load_boards()`` to match the actual lesson output format used by the
deal repos (and delete this notice once done). Everything below load_boards()
is format-agnostic.

Expected default format (lesson.json):
{
  "audience": "beginner",
  "boards": [
    {
      "number": 1,
      "question": "Partner opens 1S. What is your call?",
      "answer": "3S",
      "explanation": "...",
      "difficulty": 2
    },
    ...
  ]
}

Usage:  python lint_lesson.py path/to/lesson.json
Exit status: 0 = clean, 1 = findings, 2 = could not parse input.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field


@dataclass
class Board:
    number: int
    question: str
    answer: str
    explanation: str = ""
    difficulty: int | None = None


@dataclass
class Lesson:
    audience: str
    boards: list[Board] = field(default_factory=list)


# --------------------------------------------------------------------------
# Format adapter — EDIT THIS to match the real lesson format.
# --------------------------------------------------------------------------

def load_boards(path: str) -> Lesson:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    boards = [
        Board(
            number=b.get("number", i + 1),
            question=b.get("question", ""),
            answer=b.get("answer", ""),
            explanation=b.get("explanation", ""),
            difficulty=b.get("difficulty"),
        )
        for i, b in enumerate(data.get("boards", []))
    ]
    return Lesson(audience=data.get("audience", "beginner"), boards=boards)


# --------------------------------------------------------------------------
# Checks (format-agnostic)
# --------------------------------------------------------------------------

SUIT_ALIASES = {
    "S": r"(?:S|♠|spades?)",
    "H": r"(?:H|♥|hearts?)",
    "D": r"(?:D|♦|diamonds?)",
    "C": r"(?:C|♣|clubs?)",
    "N": r"(?:NT?|no[- ]?trumps?)",
}

EVALUATIVE_PHRASES = [
    r"\bstrong hand\b", r"\bpowerful\b", r"\bexcellent\b", r"\bgreat support\b",
    r"\bgood support\b", r"\bweak hand\b", r"\bwith so many points\b",
    r"\bsuch a good\b", r"\bperfect (?:hand|shape) for\b",
]


def answer_patterns(answer: str) -> list[re.Pattern]:
    """Build regexes matching the answer call in its common spellings.

    '3S' matches '3S', '3♠', '3 spades'. 'Pass'/'Double' match as words.
    """
    answer = answer.strip()
    pats: list[re.Pattern] = []
    m = re.fullmatch(r"([1-7])\s*(NT?|[SHDC♠♥♦♣])", answer, re.IGNORECASE)
    if m:
        level, suit = m.group(1), m.group(2).upper()
        suit_key = {"♠": "S", "♥": "H", "♦": "D", "♣": "C"}.get(suit, suit[0])
        pats.append(re.compile(
            rf"\b{level}\s*{SUIT_ALIASES[suit_key]}\b", re.IGNORECASE))
    elif answer:
        pats.append(re.compile(rf"\b{re.escape(answer)}\b", re.IGNORECASE))
    return pats


def check_leakage(lesson: Lesson) -> list[str]:
    findings = []
    for b in lesson.boards:
        for pat in answer_patterns(b.answer):
            if pat.search(b.question):
                findings.append(
                    f"Board {b.number}: question text contains the answer "
                    f"'{b.answer}' (matched {pat.pattern!r}).")
        for phrase in EVALUATIVE_PHRASES:
            if re.search(phrase, b.question, re.IGNORECASE):
                findings.append(
                    f"Board {b.number}: evaluative framing in question "
                    f"(matched {phrase!r}) — describe nothing about hand "
                    f"quality; evaluation is the exercise.")
    return findings


def check_difficulty(lesson: Lesson) -> list[str]:
    findings = []
    rated = [(b.number, b.difficulty) for b in lesson.boards]
    missing = [n for n, d in rated if d is None]
    if missing:
        findings.append(
            f"Boards missing difficulty rating: {missing} — rate every board "
            f"(1-5) before sequencing.")
        rated = [(n, d) for n, d in rated if d is not None]
    for (n1, d1), (n2, d2) in zip(rated, rated[1:]):
        if d2 < d1:
            findings.append(
                f"Difficulty decreases from board {n1} (rated {d1}) to board "
                f"{n2} (rated {d2}) — order must be non-decreasing.")
    if lesson.audience.lower() == "beginner" and rated:
        first_third = rated[: max(1, len(rated) // 3)]
        hard_early = [n for n, d in first_third if d > 2]
        if hard_early:
            findings.append(
                f"Beginner lesson: boards {hard_early} in the first third are "
                f"rated above 2.")
        too_hard = [n for n, d in rated if d >= 5]
        if too_hard:
            findings.append(
                f"Beginner lesson: boards {too_hard} rated 5 — discard or "
                f"repair.")
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    try:
        lesson = load_boards(sys.argv[1])
    except Exception as exc:  # noqa: BLE001
        print(f"Could not parse {sys.argv[1]}: {exc}")
        return 2
    findings = check_leakage(lesson) + check_difficulty(lesson)
    if findings:
        print(f"{len(findings)} finding(s):\n")
        for f in findings:
            print(f"  ✗ {f}")
        return 1
    print(f"Clean: {len(lesson.boards)} boards, no leakage or ordering issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
