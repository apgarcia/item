# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`item` is a stupidly simple Google Tasks CLI. It is currently **unimplemented** — only a `spec` file exists describing the desired behavior.

## Spec Summary

### Hierarchy-Aware Numbering

Tasks use positional keys:
- Top-level: `1`, `2`, `3`, ...
- Subtasks: `1a`, `1b`, `1c`, ...
- Deeper levels: `1aa`, `1ab`, ...

### Commands

```
item ls [-a] [-m]          # list tasks; -a includes completed, -m outputs Markdown checklist
item mk "text" [--due YYYY-MM-DD]   # create task
item rm KEY                # mark task completed (e.g. 2, 1a)
item rm -f KEY             # hard delete task
item ed KEY "title"        # replace task title
item mv SRC DST            # reorder open tasks by key
item id                    # list all Google Task lists
item use LIST_ID           # set the default task list
```

### List Selection

The active list is read from `~/.config/item/config.json`.

## Setup & Install

```bash
pip install -e .          # install in editable mode (exposes the `item` command)
python -m item            # alternative entry point without installing
```

First-run auth:
1. Download OAuth 2.0 credentials (Desktop app) from Google Cloud Console
2. Save as `~/.config/item/credentials.json`
3. Run any command — a browser window will open for Google sign-in
4. Token is cached at `~/.config/item/token.json`

## Architecture

```
item/
  keys.py    — bijective base-26 key parsing/formatting (no deps)
  config.py  — CONFIG_DIR, get_list_id(), set_default_list()
  auth.py    — OAuth2 credential management (token cache, refresh, flow)
  cli.py     — all Click commands; _build_tree() reconstructs the task
               hierarchy from the flat DFS-ordered list returned by the API
```

## Implementation Notes

- Requires Google Tasks API credentials/OAuth.
- Configuration lives at `~/.config/item/config.json`.
- `item use LIST_ID` saves the list ID to config.
- `tasks().list()` returns tasks in DFS order; `_build_tree()` buckets by `task['parent']` to reconstruct the hierarchy.
- `item mv SRC DST` moves SRC so it **becomes** position DST in the result (not "insert before DST").
- `item ls` fetches the list title via `tasklists().get()` and prints it as a header.
