# Agent Install Prompt

If you use **Claude Code** (or a similar coding agent on your Mac), copy the entire block below into
a new session. The agent will do the install, pausing to ask you for your Basecamp credentials and to
have you complete the browser login.

Before you start, have ready (see [README](README.md) Step 1):
- **Client ID** and **Client Secret** — from our IT admin (shared church app) *or* from your own app
  at <https://launchpad.37signals.com/integrations>.
- **Account ID** — the number in `https://3.basecamp.com/{ACCOUNT_ID}/projects`.

---

````text
You are setting up the Basecamp MCP server on my Mac and connecting it to my AI assistant.
Work step by step, run the commands yourself, and stop to ask me whenever you need a secret or a
browser action. Do not put any secret into a file that could be committed.

GOAL
Install https://github.com/georgeantonopoulos/Basecamp-MCP-Server, authenticate it to my Basecamp
account, and register it with the MCP client(s) I choose (Claude Desktop and/or Claude Code CLI).

STEPS

1. Check prerequisites: `brew --version`, and whether `uv` exists (`uv --version`). If `uv` is
   missing, install it with `brew install uv`. (Do NOT rely on system Python — it may be too old;
   uv will fetch Python 3.12.)

2. Clone the repo into my home directory and create the environment:
     git clone https://github.com/georgeantonopoulos/Basecamp-MCP-Server.git
     cd Basecamp-MCP-Server
     uv venv --python 3.12 venv
     uv pip install --python venv -r requirements.txt
   Then smoke-test that the server loads ~79 tools over stdio. IMPORTANT: when sending a tools/call
   over stdio for testing, keep stdin open briefly (e.g. `; sleep 10`) or the async HTTP response is
   cancelled when stdin hits EOF.

3. Ask me for my Basecamp OAuth credentials: Client ID, Client Secret, Account ID, and which redirect
   host I registered (`localhost` or `127.0.0.1`). If I haven't registered an app yet, walk me through
   https://launchpad.37signals.com/integrations and warn me about the two gotchas:
     - the *website* field needs a real https URL (not localhost),
     - "not a valid URI" almost always means a stray space pasted into a field; the redirect URI
       `http://localhost:8000/auth/callback` is valid (use `127.0.0.1` if localhost is rejected).

4. Write `.env` in the repo folder (it is git-ignored — confirm that before writing):
     BASECAMP_CLIENT_ID=...
     BASECAMP_CLIENT_SECRET=...
     BASECAMP_ACCOUNT_ID=...
     BASECAMP_REDIRECT_URI=http://localhost:8000/auth/callback   # match the host I registered
     USER_AGENT=The Ark Church (my-email@example.com)
     FLASK_SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
   Do not echo my Client Secret back to me in plain text.

5. Run the OAuth flow: start `./venv/bin/python oauth_app.py` in the background, confirm it's
   listening on http://localhost:8000, then tell me to open that URL and authorize. Wait for me to
   confirm. Verify `oauth_tokens.json` was written (mode 600) and stop the OAuth server.

6. Verify end-to-end by calling the `get_projects` tool through the server and showing me my real
   project list. (If the result is too large to return, that's still success — just summarize it.)

7. Ask me which client(s) to wire in, then configure:
     - Claude Desktop: run `./venv/bin/python generate_claude_desktop_config.py`, then tell me to
       fully quit (Cmd-Q) and reopen Claude Desktop, and that the tools appear under the tools icon
       in the message box (NOT under Settings → Connectors).
     - Claude Code CLI: if the `claude` binary is on PATH, use `claude mcp add basecamp -- <venv
       python> <basecamp_fastmcp.py>`. If `claude` is not found, back up `~/.claude.json` and add a
       "basecamp" entry to its top-level "mcpServers" object, using ABSOLUTE paths to the venv python
       and basecamp_fastmcp.py, with env { PYTHONPATH, VIRTUAL_ENV, BASECAMP_ACCOUNT_ID }. Keep the
       JSON valid.

8. Summarize what you did, where the files live, the restart step I still need to do, and remind me
   that `.env` and `oauth_tokens.json` are secrets that must never be committed or shared.

Notes you should rely on:
- basecamp_fastmcp.py loads .env by absolute path, so the server's working directory at launch time
  does not matter for token refresh.
- The redirect URI in .env must match the registered one exactly.
- Treat oauth_tokens.json as a long-lived credential.
````
