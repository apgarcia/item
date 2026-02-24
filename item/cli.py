import click
from googleapiclient.discovery import build

from .auth import get_credentials
from .config import get_list_id, set_default_list
from .keys import format_key, parse_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _service():
    return build("tasks", "v1", credentials=get_credentials(), cache_discovery=False)


def _get_tasks(svc, list_id: str, *, include_completed: bool = False) -> list[dict]:
    """Fetch all tasks from the list, handling pagination."""
    items: list[dict] = []
    page_token: str | None = None
    while True:
        resp = (
            svc.tasks()
            .list(
                tasklist=list_id,
                showCompleted=include_completed,
                showHidden=include_completed,
                maxResults=100,
                pageToken=page_token,
            )
            .execute()
        )
        items.extend(resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def _build_tree(tasks: list[dict]) -> list[tuple[dict, list[dict]]]:
    """Convert the flat task list into [(parent, [children]), ...], sorted by position."""
    children: dict[str, list[dict]] = {}
    top: list[dict] = []
    for t in tasks:
        pid = t.get("parent")
        if pid:
            children.setdefault(pid, []).append(t)
        else:
            top.append(t)
    top.sort(key=lambda t: t.get("position", ""))
    for kids in children.values():
        kids.sort(key=lambda t: t.get("position", ""))
    return [(t, children.get(t["id"], [])) for t in top]


def _require_list() -> str:
    lid = get_list_id()
    if not lid:
        raise SystemExit(
            "No task list selected.\n"
            "Run 'item id' to see available lists, then 'item use LIST_ID'."
        )
    return lid


def _resolve(tree: list[tuple[dict, list[dict]]], key: str) -> dict:
    """Return the task dict for key, or raise SystemExit on bad input."""
    try:
        ti, si = parse_key(key)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}")

    if ti >= len(tree):
        raise SystemExit(
            f"error: {key!r} out of range ({len(tree)} top-level task(s))"
        )
    parent, subs = tree[ti]
    if si is None:
        return parent
    if si >= len(subs):
        raise SystemExit(
            f"error: {key!r} out of range (task {ti + 1} has {len(subs)} subtask(s))"
        )
    return subs[si]


def _print_row(key: str, title: str, done: bool, depth: int, markdown: bool) -> None:
    indent = "  " * depth
    if markdown:
        box = "x" if done else " "
        print(f"{indent}- [{box}] {title}")
    else:
        tag = " [done]" if done else ""
        print(f"{indent}{key}  {title}{tag}")


def _move_to(
    svc,
    list_id: str,
    task_id: str,
    parent_id: str | None,
    dst_idx: int,
    peers: list[dict],
) -> None:
    """Move task_id to position dst_idx (0-based) among peers at the destination level.

    peers: tasks already at that level, with task_id removed if it was there.
    parent_id: None → top level; task ID → subtask of that parent.
    """
    dst_idx = max(0, min(dst_idx, len(peers)))
    previous: str | None = peers[dst_idx - 1]["id"] if dst_idx > 0 else None

    kwargs: dict = {"tasklist": list_id, "task": task_id}
    if parent_id:
        kwargs["parent"] = parent_id
    if previous:
        kwargs["previous"] = previous
    svc.tasks().move(**kwargs).execute()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """Stupidly simple Google Tasks CLI."""


@cli.command("ls")
@click.option("-a", "--all", "show_all", is_flag=True, help="Include completed items.")
@click.option("-m", "--markdown", is_flag=True, help="Output as Markdown checklist.")
def ls(show_all: bool, markdown: bool) -> None:
    """List tasks."""
    list_id = _require_list()
    svc = _service()

    list_info = svc.tasklists().get(tasklist=list_id).execute()
    list_title = list_info.get("title", list_id)
    tree = _build_tree(_get_tasks(svc, list_id, include_completed=show_all))

    if markdown:
        print(f"- {list_title}")
        task_depth = 1
    else:
        print(list_title)
        print("-" * len(list_title))
        task_depth = 0

    for ti, (parent, subs) in enumerate(tree):
        if not show_all and parent.get("status") == "completed":
            continue
        done = parent.get("status") == "completed"
        _print_row(format_key(ti), parent["title"], done, task_depth, markdown)

        for si, sub in enumerate(subs):
            if not show_all and sub.get("status") == "completed":
                continue
            sub_done = sub.get("status") == "completed"
            _print_row(
                format_key(ti, si), sub["title"], sub_done, task_depth + 1, markdown
            )


@cli.command("mk")
@click.argument("text")
@click.option("--due", metavar="YYYY-MM-DD", default=None, help="Due date.")
def mk(text: str, due: str | None) -> None:
    """Create a task."""
    list_id = _require_list()
    svc = _service()
    body: dict = {"title": text, "status": "needsAction"}
    if due:
        body["due"] = f"{due}T00:00:00.000Z"
    svc.tasks().insert(tasklist=list_id, body=body).execute()


@cli.command("rm")
@click.argument("key")
@click.option("-f", "--force", is_flag=True, help="Hard delete instead of marking complete.")
@click.option("-a", "--all", "show_all", is_flag=True, help="Include completed tasks when resolving KEY (matches 'ls -a' numbering).")
def rm(key: str, force: bool, show_all: bool) -> None:
    """Complete or delete a task."""
    list_id = _require_list()
    svc = _service()
    tree = _build_tree(_get_tasks(svc, list_id, include_completed=show_all))
    task = _resolve(tree, key)
    if force:
        svc.tasks().delete(tasklist=list_id, task=task["id"]).execute()
    else:
        svc.tasks().patch(
            tasklist=list_id, task=task["id"], body={"status": "completed"}
        ).execute()


@cli.command("ed")
@click.argument("key")
@click.argument("title")
def ed(key: str, title: str) -> None:
    """Replace a task's title."""
    list_id = _require_list()
    svc = _service()
    tree = _build_tree(_get_tasks(svc, list_id))
    task = _resolve(tree, key)
    svc.tasks().patch(
        tasklist=list_id, task=task["id"], body={"title": title}
    ).execute()


@cli.command("mv")
@click.argument("src")
@click.argument("dst")
def mv(src: str, dst: str) -> None:
    """Reorder tasks: move SRC to position DST.

    Works across levels: 'item mv 4 3a' makes task 4 the first subtask of task 3;
    'item mv 2a 3' promotes subtask 2a to top-level position 3.
    """
    list_id = _require_list()
    svc = _service()

    try:
        src_ti, src_si = parse_key(src)
        dst_ti, dst_si = parse_key(dst)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}")

    tree = _build_tree(_get_tasks(svc, list_id))
    tops = [t for t, _ in tree]

    # Resolve source task.
    if src_ti >= len(tree):
        raise SystemExit(f"error: {src!r} out of range ({len(tree)} top-level tasks)")
    if src_si is None:
        src_task = tree[src_ti][0]
    else:
        _, src_subs = tree[src_ti]
        if src_si >= len(src_subs):
            raise SystemExit(
                f"error: {src!r} out of range (task {src_ti + 1} has {len(src_subs)} subtask(s))"
            )
        src_task = src_subs[src_si]

    if dst_si is None:
        # Destination: top level.
        peers = [t for t in tops if t["id"] != src_task["id"]]
        _move_to(svc, list_id, src_task["id"], None, dst_ti, peers)
    else:
        # Destination: subtask of task dst_ti.
        if dst_ti >= len(tree):
            raise SystemExit(
                f"error: {dst!r} — no parent task at position {dst_ti + 1}"
            )
        dst_parent, dst_subs = tree[dst_ti]
        peers = [t for t in dst_subs if t["id"] != src_task["id"]]
        _move_to(svc, list_id, src_task["id"], dst_parent["id"], dst_si, peers)


@cli.command("id")
def id_cmd() -> None:
    """List all task lists."""
    svc = _service()
    resp = svc.tasklists().list(maxResults=100).execute()
    for tl in resp.get("items", []):
        print(f"{tl['title']:<30} {tl['id']}")


@cli.command("use")
@click.argument("list_id")
def use(list_id: str) -> None:
    """Set the default task list."""
    set_default_list(list_id)


@cli.command("mklist")
@click.argument("name")
def mklist(name: str) -> None:
    """Create a new task list."""
    svc = _service()
    result = svc.tasklists().insert(body={"title": name}).execute()
    print(f"{result['title']:<30} {result['id']}")


@cli.command("rmlist")
@click.argument("list_id", required=False)
def rmlist(list_id: str | None) -> None:
    """Delete a task list (defaults to the current list)."""
    if list_id is None:
        list_id = _require_list()
    svc = _service()
    info = svc.tasklists().get(tasklist=list_id).execute()
    title = info.get("title", list_id)
    svc.tasklists().delete(tasklist=list_id).execute()
    print(f"Deleted: {title}")
    if get_list_id() == list_id:
        set_default_list(None)
