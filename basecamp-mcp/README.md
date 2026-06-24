# Basecamp MCP — Staff Setup Guide

This repo explains how to connect **Basecamp** to an AI assistant (Claude Desktop and/or
Claude Code) on a Mac, using the open-source
[Basecamp-MCP-Server](https://github.com/georgeantonopoulos/Basecamp-MCP-Server).

Once it's set up, you can ask your assistant things like *"Show me all my Basecamp projects,"*
*"Create a todo called Review PR in todolist 987654,"* or *"Search Basecamp for the launch date."*
It exposes ~79 Basecamp tools (projects, todos, message boards, card tables, documents, search, and more).

> **This repo contains documentation only — no passwords, tokens, or secrets.**
> Your credentials stay on your own machine.

---

## Two ways to install

| | Best for |
|---|---|
| **[Let an AI agent do it](AGENT_INSTALL.md)** | If you already use **Claude Code** (the CLI/desktop coding agent). Paste one prompt and it walks you through everything, asking for your credentials when needed. |
| **Manual steps (below)** | If you'd rather run the commands yourself, or you're not using Claude Code. |

Either way, the one thing only *you* can do is the Basecamp login — see **Step 1**.

---

## Before you start

- A **Mac** (these instructions are macOS-specific; the underlying server also runs on Linux/Windows).
- **[Homebrew](https://brew.sh)** installed. Check with `brew --version`.
- A **Basecamp 3 / Basecamp 4 account** you can log into.
- About **10 minutes**.

You do **not** need Python pre-installed — we use [`uv`](https://docs.astral.sh/uv/), which fetches
its own Python.

---

## Step 1 — Get Basecamp OAuth credentials

The server logs into Basecamp on your behalf using OAuth. That needs three values:

- **Client ID**
- **Client Secret**
- **Account ID** — the number in your Basecamp URL: `https://3.basecamp.com/{ACCOUNT_ID}/projects`

There are two ways to obtain the Client ID/Secret. **Pick one:**

### Option A — Use the shared church OAuth app (simplest)

Our IT admin has registered **one** Basecamp OAuth app for the church. Ask them for the
**Client ID** and **Client Secret** (they'll send it privately — these are never posted in this repo
or any chat). You'll still do your own Basecamp login in Step 4, so your access stays tied to *your*
account.

You just need: Client ID, Client Secret (from the admin) + your own Account ID.

### Option B — Register your own OAuth app

1. Go to <https://launchpad.37signals.com/integrations> and click **Register a new application**.
2. Fill the form. **This is where people get stuck — read carefully:**

   | Field | What to enter |
   |---|---|
   | Name of your application | Anything, e.g. `Basecamp MCP (Your Name)` |
   | Company / product name | e.g. `The Ark Church` |
   | Company / product **website** | A **real `https://` URL**, e.g. `https://www.thearkchurch.com`. **This field rejects `localhost`** — that's the #1 validation error. |
   | Products | Check **Basecamp 4** (or **Basecamp 3** if that's your account). |
   | **Redirect URI** | `http://localhost:8000/auth/callback` — `localhost` **is** allowed here. |

3. **If you get "not a valid URI":**
   - You almost certainly have a **stray space** pasted into the box. Clear the field and *type* the
     URL with no leading/trailing space.
   - If the redirect URI is still rejected, use the loopback IP instead:
     `http://127.0.0.1:8000/auth/callback` (and tell the installer/agent you used `127.0.0.1` so the
     config matches).
4. Submit → you'll get your **Client ID** and **Client Secret**.

> The **Redirect URI you register must match your `.env` exactly**, character for character, or the
> login will fail in Step 4.

---

## Step 2 — Install tooling and the server

```bash
# Install uv (manages Python + virtualenv). Skip if you already have it.
brew install uv

# Clone the server
git clone https://github.com/georgeantonopoulos/Basecamp-MCP-Server.git
cd Basecamp-MCP-Server

# Create a Python 3.12 virtual environment and install dependencies
uv venv --python 3.12 venv
uv pip install --python venv -r requirements.txt
```

Sanity check (should print a number around 79):

```bash
printf '%s\n%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | ./venv/bin/python basecamp_fastmcp.py 2>/dev/null \
  | ./venv/bin/python -c "import sys,json; [print('tools:',len(json.loads(l).get('result',{}).get('tools',[]))) for l in sys.stdin if '\"tools\"' in l]"
```

---

## Step 3 — Create the `.env`

In the `Basecamp-MCP-Server` folder, create a file named `.env`:

```bash
BASECAMP_CLIENT_ID=your-client-id
BASECAMP_CLIENT_SECRET=your-client-secret
BASECAMP_ACCOUNT_ID=your-account-id
BASECAMP_REDIRECT_URI=http://localhost:8000/auth/callback
USER_AGENT=The Ark Church (your-email@example.com)
FLASK_SECRET_KEY=paste-a-random-string-here
```

- `BASECAMP_REDIRECT_URI` **must match** what you registered in Step 1 (use `127.0.0.1` here if you
  registered `127.0.0.1`).
- Generate a random `FLASK_SECRET_KEY` with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `.env` is already git-ignored by the server repo — **never commit it.**

---

## Step 4 — Log into Basecamp (the part only you can do)

```bash
./venv/bin/python oauth_app.py
```

Then open **<http://localhost:8000>** in your browser, click to authorize, and approve access.
You'll be redirected back and see "authenticated." Your tokens are saved locally to
`oauth_tokens.json` (file permissions `600`).

Stop the server with **Ctrl-C** when done — it's only needed for this login step.

> ⚠️ `oauth_tokens.json` contains a long-lived login token. Treat it like a password. It's
> git-ignored; don't share or commit it.

---

## Step 5 — Connect it to your assistant

The server runs locally; your client launches it on demand. Paths below assume you cloned into your
home folder — adjust if not.

### Claude Desktop

From the `Basecamp-MCP-Server` folder:

```bash
./venv/bin/python generate_claude_desktop_config.py
```

Then **fully quit Claude Desktop** (Cmd-Q, not just close the window) and reopen it.

**Where to find the tools:** Basecamp will **not** appear under *Settings → Connectors* (that list is
for hosted/remote connectors only). Instead, in a conversation click the **tools icon** in the
message box and you'll see **basecamp** with its tools — toggle them on.

### Claude Code (CLI)

If the `claude` command is available:

```bash
claude mcp add basecamp -- \
  /full/path/to/Basecamp-MCP-Server/venv/bin/python \
  /full/path/to/Basecamp-MCP-Server/basecamp_fastmcp.py
```

If `claude` isn't on your PATH, add it to `~/.claude.json` by hand instead. Inside the top-level
`"mcpServers"` object, add (use **absolute** paths):

```json
"basecamp": {
  "command": "/full/path/to/Basecamp-MCP-Server/venv/bin/python",
  "args": ["/full/path/to/Basecamp-MCP-Server/basecamp_fastmcp.py"],
  "env": {
    "PYTHONPATH": "/full/path/to/Basecamp-MCP-Server",
    "VIRTUAL_ENV": "/full/path/to/Basecamp-MCP-Server/venv",
    "BASECAMP_ACCOUNT_ID": "your-account-id"
  }
}
```

Back up the file first (`cp ~/.claude.json ~/.claude.json.bak`) and keep the JSON valid. Restart
Claude Code to pick it up.

---

## Step 6 — Verify

Ask your assistant: **"Show me all my Basecamp projects."** You should get your real project list back.

---

## Troubleshooting

- **"not a valid URI" when registering the app** → stray space in the field, or `localhost` in the
  *website* box. See Step 1, item 3.
- **Login fails / redirect error** → `BASECAMP_REDIRECT_URI` in `.env` doesn't match what you
  registered. They must be identical (including `localhost` vs `127.0.0.1`).
- **Tools don't show in Claude Desktop** → you didn't fully **Cmd-Q** quit, or you're looking under
  *Settings → Connectors*. Use the **tools icon in the message box** instead. Logs:
  `~/Library/Logs/Claude/mcp-server-basecamp.log`.
- **Manual `tools/list` smoke test hangs or returns nothing** → a tool call needs the server's stdin
  to stay open while it makes its HTTP request. For test scripts, keep stdin open briefly
  (e.g. append `; sleep 10`) so the async response can come back before the process exits.
- **`get_projects` says the result is too large** → that's success — it just returned a lot of data.
- **Token expired later** → re-run `./venv/bin/python oauth_app.py` and re-authorize at
  <http://localhost:8000>. (Auto-refresh usually handles this for you.)

---

## Security notes

- Never commit `.env` or `oauth_tokens.json`. Both are git-ignored by the server repo.
- The tokens in `oauth_tokens.json` are long-lived — keep them on your own machine only.
- If you used the shared church OAuth app, the Client Secret should reach you privately
  (e.g. a password manager or DM), never in a repo, ticket, or group chat.
- This server is for **local** use by your own MCP client. Don't expose it on a network.

---

## Credits

Built on [georgeantonopoulos/Basecamp-MCP-Server](https://github.com/georgeantonopoulos/Basecamp-MCP-Server)
(MIT). This repo just documents installing and connecting it for our staff.
