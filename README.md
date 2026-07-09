# bridge-craftwork Claude Code plugins

Shared Claude Code plugins for Bridge Classroom deal curation and lesson
authoring. Maintained jointly; changes flow to all installed machines via the
plugin marketplace update mechanism.

## One-time setup (per person, per machine)

Inside Claude Code:

```
/plugin marketplace add bridge-craftwork/claude-bridge-plugins
/plugin install lesson-authoring@bridge-craftwork
```

The repo can stay private — Claude Code uses your normal git credentials, so
if `git clone` works in your terminal, installation works.

### Enable auto-update

Run `/plugin`, go to the **Marketplaces** tab, select `bridge-craftwork`, and
enable **Auto-update**. After an update lands, Claude Code will prompt you to
run `/reload-plugins` — no restart needed. (Without auto-update, pull changes
manually with `/plugin marketplace update bridge-craftwork`.)

## Updating the skill (the training loop)

The skill is just versioned markdown. When lesson generation misbehaves:

1. Identify the correction ("don't annotate alternate bids for beginners —
   exchange cards instead").
2. Commit it to the appropriate file:
   - Policy/rules → `plugins/lesson-authoring/skills/lesson-authoring/SKILL.md`
   - New leaky-prompt example → `.../examples/prompt-dos-and-donts.md`
   - Difficulty calibration → `.../references/difficulty-rubric.md`
   - Mechanically checkable rule → `.../scripts/lint_lesson.py`
3. Push (or PR, for anything the other maintainer should review).
4. Everyone else picks it up automatically (auto-update) or via
   `/plugin marketplace update bridge-craftwork`.

Tip: while actively iterating, you can also add your local clone as a second
marketplace (`/plugin marketplace add ./path/to/claude-plugins`) so SKILL.md
edits can be tested without a push/update round-trip.

## Adaptation TODOs

- [x] `scripts/lint_lesson.py` — now parses the real coaching PBN format
      (`[show]`/`[BID]`/`[ACCEPT]`) and surveys a file or whole collection for
      `[ACCEPT]` alternate-call markers, flagging beginner boards. Point it at a
      collection dir: `python lint_lesson.py path/to/coaching-non-rotated`.
      (Leak/ordering checks were dropped — they false-positive on this guided
      walk-through format; those stay judgment calls in review.)
- [ ] SKILL.md assumes Standard American as the default system. Adjust if the
      classes teach something else.
- [ ] Optionally add `docs/deal-repo-settings.json` (see below) to each deal
      repo so new clones are prompted to install the marketplace.

## Auto-registering in deal repos (optional)

Add this as `.claude/settings.json` in each deal repo (a copy lives at
`docs/deal-repo-settings.json`). When someone trusts the repo folder, Claude
Code offers to install the marketplace for them:

```json
{
  "extraKnownMarketplaces": {
    "bridge-craftwork": {
      "source": {
        "source": "github",
        "repo": "bridge-craftwork/claude-bridge-plugins"
      }
    }
  }
}
```

## Repo layout

```
.claude-plugin/marketplace.json        the catalog Claude Code reads
plugins/lesson-authoring/
  .claude-plugin/plugin.json           plugin metadata
  skills/lesson-authoring/
    SKILL.md                           the policy layer (loads when triggered)
    examples/prompt-dos-and-donts.md   before/after leaky prompt pairs
    references/difficulty-rubric.md    base tier + per-board gradient rubric
    scripts/lint_lesson.py             surveys coaching PBN for [ACCEPT] alternates
    scripts/difficulty.py              scores board difficulty, flags outliers
```

Both scripts parse the real coaching PBN format and take a file **or a whole
collection directory** — e.g. `python difficulty.py path/to/coaching-non-rotated`.

Future plugins (deal curation, PBN validation, homework analytics, ...) get
their own directory under `plugins/` and an entry in `marketplace.json`.
