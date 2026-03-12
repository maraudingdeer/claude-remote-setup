# Paper Review Plugin

Interactive paper review workflow for Claude Code with reMarkable annotation extraction, Bloom's taxonomy quizzing, SM-2 spaced repetition, and GitHub Issues integration.

## What It Does

Two slash commands:

- **`/paper-review [name-or-URL]`** — Full 5-stage review: extract annotations from reMarkable, quiz you on the paper using Bloom's taxonomy, resolve citations, create action items as GitHub issues, update spaced repetition database, and commit everything to git.
- **`/sr-review`** — Standalone spaced repetition session. Reviews papers due today using targeted questions on your weak areas, updates SM-2 scheduling, and commits.

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| [Claude Code](https://claude.com/claude-code) | CLI agent | `npm install -g @anthropic-ai/claude-code` |
| [uv](https://docs.astral.sh/uv/) | Python script runner | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [gh](https://cli.github.com/) | GitHub CLI (for action items) | `brew install gh` / `apt install gh` |
| [rmapi](https://github.com/ddvk/rmapi) | reMarkable Cloud API | `go install github.com/ddvk/rmapi@latest` |
| Git | Version control | Already installed on most systems |

**Optional:**
- A **reMarkable tablet** for annotation extraction. Without one, you can still review papers from URLs — the plugin works with web content directly.
- `pyobjc-framework-Vision` (macOS only) — enables OCR on handwritten notes. On Linux, the plugin falls back to Claude's visual transcription.

## Setup

### Step 1: Create Your Data Repo

The plugin stores reviews, paper data, and spaced repetition state in a **separate git repo**. This keeps your review history versioned independently from the plugin code.

```bash
mkdir -p ~/paper-review/{reviews,papers}
cd ~/paper-review
git init

# Create the database file
cat > database.json << 'EOF'
{
  "version": 1,
  "papers": []
}
EOF

# Create the project CLAUDE.md
cat > CLAUDE.md << 'CLAUDEEOF'
# Paper Review Data Repo

This repo stores paper reviews, metadata, and the spaced repetition database.

## Structure

- `reviews/` — Markdown review files (`YYYY-MM-DD-paper-slug.md`)
- `papers/` — Downloaded PDFs and extracted data (gitignored)
- `database.json` — Paper database with metadata, quiz results, and spaced repetition scheduling

## Conventions

- Paper slugs are lowercase-hyphenated titles (e.g., `ai-control-improving-safety`)
- Each review file contains: highlights, quiz results, key insights, and action items
- `database.json` is the source of truth for spaced repetition state

## SM-2 Spaced Repetition Fields (per paper in database.json)

- `easiness_factor` (float, default 2.5) — SM-2 EF, minimum 1.3
- `interval_days` (int, default 0) — current interval between reviews
- `repetition_number` (int, default 0) — consecutive successful reviews
- `quality_history` (array of int) — SM-2 quality scores (0-5) from each review session
- `next_review` (ISO date) — computed from last review + interval_days
CLAUDEEOF

# Gitignore large binary files
cat > .gitignore << 'EOF'
papers/**/*.pdf
papers/**/*.zip
papers/**/*.rm
papers/**/*.png
papers/**/*.rmdoc
papers/**/*.content
papers/**/*.metadata
papers/**/*.pagedata
EOF

git add -A
git commit -m "Initial paper-review data repo"
```

Optionally push to GitHub:
```bash
gh repo create paper-review --private --source=. --push
```

### Step 2: Install the Plugin

If using the custom-plugins marketplace:
```bash
claude plugin install paper-review@custom-plugins
```

Or manually add the plugin directory to your Claude Code configuration.

### Step 3: Configure Paths (Required)

You **must** update hardcoded paths in three files. Do a global find-and-replace of `/Users/titus/pyg/paper-review` with your data repo path (e.g., `/home/yourname/paper-review`):

**Files to update:**

1. **`CLAUDE.md`** — One reference on line 8
2. **`commands/paper-review.md`** — ~15 references throughout (the Constants section + all stage instructions)
3. **`commands/sr-review.md`** — ~5 references (Constants section + commit commands)

Quick way to do it:
```bash
cd /path/to/paper-review-plugin/
sed -i '' 's|/Users/titus/pyg/paper-review|/home/yourname/paper-review|g' \
  CLAUDE.md commands/paper-review.md commands/sr-review.md
```

### Step 4: Configure GitHub Issues (Optional)

The plugin creates GitHub issues for action items from papers. In `commands/paper-review.md`, find:
```bash
gh issue create --repo tbuckworth/tasks
```
Replace `tbuckworth/tasks` with your own GitHub repo (e.g., `yourname/tasks`). This repo should exist and have labels set up:

**Required labels** (create these in your repo):
- `source:claude`, `section:work`
- `action:look-into`, `action:email`, `action:call`, `action:manual`, `action:buy`
- `list:tasks`, `list:to-read`, `list:philosophy`
- `priority:high`, `priority:medium`, `priority:low`

If you don't want GitHub issue integration, just skip this — the plugin will still work for everything else.

### Step 5: Configure reMarkable Folders (Optional)

The plugin looks for papers in two reMarkable folders:
- **`To Quiz`** — general reading queue
- **`Apollo Interview Prep/Done`** — secondary folder (specific to original author)

To customize:
- Search for `"To Quiz"` and `"Apollo Interview Prep/Done"` in `commands/paper-review.md`
- Replace with your own folder names, or remove the secondary folder references
- The `"Archive"` folder is where reviewed papers get moved — create it on your reMarkable or change the name

**No reMarkable?** No problem. Pass a URL instead:
```
/paper-review https://arxiv.org/abs/2412.04984
```

### Step 6: Authenticate Tools

```bash
# GitHub CLI
gh auth login

# reMarkable Cloud (if using — follow prompts on first run)
rmapi
```

## Usage

### Review a New Paper

```
# Pick from reMarkable (shows available documents)
/paper-review

# Specific document on reMarkable
/paper-review Sleeper Agents

# Review from a URL (blog post, arXiv, etc.)
/paper-review https://arxiv.org/abs/2412.04984
```

The plugin walks you through 5 stages:

1. **Understanding** (~5 min) — Presents your highlights and handwritten notes grouped by theme, answers questions you annotated, Feynman technique on 2 key concepts
2. **Quiz** (~8 min) — 6 free-response questions across Bloom's taxonomy (Remember → Create), with carry-forward feedback
3. **Wrap Up** (~3 min) — Resolves top citations, asks for action items (creates GitHub issues), writes review markdown, computes SM-2 score, archives on reMarkable, git commits
4. **Spaced Repetition** (5-15 min) — Reviews previously studied papers due today, targeted questions on weak areas
5. **Plan Tomorrow** (~1 min) — Suggests next paper based on citation overlap and queue age

### Run a Standalone Spaced Repetition Session

```
/sr-review
```

Reviews all papers where `next_review <= today`, ordered by SM-2 priority. You can stop at any time by selecting "Done for today."

## Data Model

### database.json

Each paper entry:

```json
{
  "id": "paper-slug",
  "title": "Paper Title",
  "authors": ["Author 1"],
  "url": "https://arxiv.org/abs/...",
  "arxiv_id": "2412.04984",
  "type": "paper",
  "status": "reviewed",
  "date_added": "2026-03-12",
  "date_read": "2026-03-12",
  "summary": "One-paragraph summary",
  "key_insights": ["Insight 1", "Insight 2"],
  "tags": ["alignment", "scheming"],
  "quiz_results": {
    "total_asked": 6,
    "total_correct": 4,
    "by_level": {
      "remember": [1, 1],
      "understand": [1, 0.5],
      "apply": [1, 1],
      "analyze": [1, 0.5],
      "evaluate": [1, 1],
      "create": [1, 0]
    }
  },
  "review_dates": ["2026-03-12"],
  "easiness_factor": 2.5,
  "interval_days": 1,
  "repetition_number": 1,
  "quality_history": [4],
  "next_review": "2026-03-13",
  "review_file": "reviews/2026-03-12-paper-slug.md",
  "remarkable_path": "To Quiz/Paper Title",
  "linked_papers": [
    {"id": "other-paper", "relationship": "cites"}
  ]
}
```

### SM-2 Algorithm

Quiz percentage maps to quality score (0-5):

| Quiz Score | Quality | Meaning |
|-----------|---------|---------|
| 90-100% | 5 | Perfect recall |
| 70-89% | 4 | Correct with hesitation |
| 50-69% | 3 | Correct with difficulty |
| 30-49% | 2 | Incorrect but familiar |
| 10-29% | 1 | Incorrect, vague memory |
| 0-9% | 0 | Complete blackout |

- **Pass** (q >= 3): interval grows — 1 day, then 6 days, then `interval * EF`
- **Fail** (q < 3): reset to 1-day interval, start over

## File Structure

```
plugin/                              # This directory (installed by Claude Code)
  .claude-plugin/plugin.json         # Plugin manifest
  CLAUDE.md                          # Plugin architecture (read by Claude)
  README.md                          # This file (for humans)
  commands/
    paper-review.md                  # Main 5-stage review command
    sr-review.md                     # Standalone SR session command
  scripts/
    extract_annotations.py           # Parse reMarkable .rm files -> JSON
    extract_citations.py             # Extract references from PDF
    resolve_citation.py              # Look up citation metadata (Semantic Scholar)
    sr_priority.py                   # Compute SM-2 priority queue
  skills/
    learning-science/
      SKILL.md                       # Learning science techniques reference
      references/
        blooms-taxonomy.md           # Question stem templates per Bloom's level

data-repo/                           # Your separate git repo (Step 1)
  database.json                      # Paper database + SM-2 state (source of truth)
  CLAUDE.md                          # Data repo conventions
  reviews/                           # Markdown review summaries
    2026-03-12-paper-slug.md
  papers/                            # Downloaded PDFs + extracted data (gitignored)
    paper-slug/
      *.pdf
      annotations.json
```
