item - stupidly simple Google Tasks CLI

Hierarchy-aware numbering:

  Top-level items: 1, 2, 3, ...
  Subtasks:        1a, 1b, 1c, ...
  (Deeper levels, if any): 1aa, 1ab, etc.

Commands:

  item ls [-a] [-m]
      -a, --all      Include completed items
      -m, --markdown Output as a Markdown checklist

  item mk "text" [--due YYYY-MM-DD]
  item rm KEY          # mark as completed (e.g. 2, 1a)
  item rm -f KEY       # hard delete from list
  item ed KEY "title"  # replace title
  item mv SRC DST      # reorder open items by key
  item id              # show task lists
  item use LIST_ID     # set the default task list
  item mklist "name"   # create a new task list
  item rmlist [LIST_ID] # delete a task list (defaults to current)

List selection:

- If $ITEM_LIST is set, that list is used.
- Otherwise, a default is stored in ~/.config/item/config.json
