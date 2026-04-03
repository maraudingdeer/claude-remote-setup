---
description: Extract action items from reMarkable Journal entries and add them to Todoist
argument-hint: "[document-name or leave blank for all]"
allowed-tools: [Read, Write, Bash, Glob, AskUserQuestion]
model: claude-opus-4-6
---

# Journal → Todoist

Scan journal entries from the reMarkable `Journal` folder, identify action items in natural language, confirm with the user, and create them as tasks in Todoist's **Action Items** project.

## Setup paths

- Plugin scripts: `${CLAUDE_PLUGIN_ROOT}scripts/`
- Temp working dir: `/tmp/journal-todoist/`

## Step 1 — List the Journal folder

```bash
export PATH="$HOME/go/bin:$PATH"
rmapi ls "/Journal"
```

If an argument was provided, filter to that document name only. If the folder is empty, tell the user and stop.

## Step 2 — Download journal entries

For each document (or the specified one):

```bash
export PATH="$HOME/go/bin:$PATH"
mkdir -p /tmp/journal-todoist
cd /tmp/journal-todoist
rmapi get "/Journal/<document-name>"
```

Unzip the downloaded `.zip` or `.rmdoc` to access the PDF and `.rm` annotation files.

## Step 3 — Extract text and handwriting

```bash
uv run --python 3.12 --with rmscene,PyMuPDF,Pillow \
  "${CLAUDE_PLUGIN_ROOT}scripts/extract_annotations.py" /tmp/journal-todoist/<doc-dir>
```

Read the output JSON:
- `highlights` — highlighted text
- `handwritten_notes` — ink clusters with `surrounding_text` and `ink_on_white_path` PNG paths

View each `ink_on_white_path` PNG to read the handwriting visually. Also read `surrounding_text` for context.

## Step 4 — Identify action items

Read all extracted content and identify things that need doing:
- Explicit to-dos: "I need to...", "must...", "should...", "remember to...", "don't forget..."
- Implied tasks: plans, commitments, follow-ups, calls, purchases, people to contact
- Questions to investigate

For each action item produce:
- `content`: concise task title starting with an imperative verb (e.g. "Call dentist to book appointment")
- `description`: brief journal context if useful (optional, keep short)
- `due_string`: only if a specific date was mentioned (e.g. "tomorrow", "Friday")

## Step 5 — Confirm with user

Show the identified action items numbered and ask:

> "I found X action items in your journal. Here's the list — shall I add all of them to Todoist, or would you like to remove or edit any first?"

Wait for approval. Apply any edits or removals the user requests.

## Step 6 — Create Todoist tasks

Write approved tasks to a temp file and run the script:

```bash
cat > /tmp/journal_tasks.json << 'EOF'
[
  {"content": "Task title", "description": "optional context", "due_string": "optional"}
]
EOF

source ~/.zshrc
uv run --python 3.12 --with requests \
  "${CLAUDE_PLUGIN_ROOT}scripts/create_todoist_tasks.py" /tmp/journal_tasks.json
```

## Step 7 — Clean up

```bash
rm -rf /tmp/journal-todoist /tmp/journal_tasks.json
```

Tell the user how many tasks were added to Todoist.
