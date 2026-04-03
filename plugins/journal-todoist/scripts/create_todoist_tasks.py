#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""
Create Todoist tasks in the Action Items project.
Usage: uv run scripts/create_todoist_tasks.py tasks.json

tasks.json should be a JSON array:
  [{"content": "Task title", "description": "optional detail", "due_string": "optional"}]
"""

import json
import os
import sys
import requests

API_TOKEN = os.environ.get("TODOIST_API_TOKEN")
PROJECT_ID = "6gHcF84w23gCPxgP"  # Action Items project

if not API_TOKEN:
    print("ERROR: TODOIST_API_TOKEN environment variable not set", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: uv run scripts/create_todoist_tasks.py tasks.json", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1]) as f:
    tasks = json.load(f)

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

created = []
failed = []

for task in tasks:
    payload = {"content": task["content"], "project_id": PROJECT_ID}
    if task.get("description"):
        payload["description"] = task["description"]
    if task.get("due_string"):
        payload["due_string"] = task["due_string"]

    resp = requests.post(
        "https://api.todoist.com/api/v1/tasks",
        headers=headers,
        json=payload,
    )
    if resp.status_code in (200, 201, 204):
        created.append(task["content"])
    else:
        failed.append({"task": task["content"], "error": resp.text})

print(json.dumps({"created": created, "failed": failed}, indent=2))
