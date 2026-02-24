# item

Stupidly simple Google Tasks CLI.

## Install

```bash
pip install -e .
```

## Setup

### 1. Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown → **New Project** → give it a name → **Create**

### 2. Enable the Tasks API

1. **APIs & Services → Library**
2. Search "Google Tasks API" → click it → **Enable**

### 3. Configure the OAuth consent screen

1. **APIs & Services → OAuth consent screen**
2. Choose **External** → **Create**
3. Fill in app name and your email → **Save and Continue** through all steps
4. Under **Test users**, add your own Google account

### 4. Create credentials

1. **APIs & Services → Credentials**
2. **+ Create Credentials → OAuth client ID**
3. Application type: **Desktop app** → **Create**
4. Click the download icon on the newly created credential

### 5. Place the credentials file

```bash
mkdir -p ~/.config/item
mv ~/Downloads/client_secret_*.json ~/.config/item/credentials.json
```

The first time you run any `item` command, a browser window will open for Google sign-in. After that, the token is cached at `~/.config/item/token.json` and you won't be prompted again.

## Usage

```
item id                     list all task lists
item use LIST_ID            set the default task list
item mk "text" [--due DATE] create a task (date format: YYYY-MM-DD)
item ed KEY "new title"     replace a task's title
item ls [-a] [-m]           list tasks (-a: include done, -m: markdown output)
item mv SRC DST             reorder tasks (SRC becomes position DST)
item rm KEY                 mark a task complete (visible with ls -a)
item rm -f KEY              hard delete an open task (gone permanently)
item rm -fa KEY             hard delete a completed task (KEY matches ls -a numbering)
item mklist "name"          create a new task list
item rmlist [LIST_ID]       delete a task list (defaults to current)
```

Tasks are identified by hierarchical keys:

```
1, 2, 3, ...        top-level tasks
1a, 1b, ..., 1z     subtasks of task 1
1aa, 1ab, ...       subtasks 27+ of task 1
```

The active list is stored in `~/.config/item/config.json`.
