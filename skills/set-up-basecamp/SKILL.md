---
name: set-up-basecamp
description: Connects Basecamp to Claude on an Ark staff member's Mac using the official Basecamp CLI and its built-in MCP server, with no admin rights, Homebrew, or Python needed. Use when someone says "set up Basecamp," "connect Basecamp," "install Basecamp for Claude," "update Basecamp," "Basecamp isn't working in Claude," or asks how to get Basecamp in Claude. Setup runs only in the Code tab of the Claude desktop app; after that, Basecamp works in Code, regular chat, and Cowork. Also covers how to work in Basecamp once connected, including @mentioning people.
---

# Set up Basecamp

You connect a staff member's Basecamp to Claude using 37signals' official **Basecamp CLI**. The CLI includes an MCP server (`basecamp mcp`), so there's nothing else to install. It goes into the person's home folder, so **no admin password, Homebrew, or Python** is involved. Staff don't have admin rights on their Macs, so never suggest `sudo` or Homebrew.

Most staff aren't technical. Run the commands yourself, explain each step in a sentence, and only stop when you need the person to do something, like clicking Approve in the browser.

## Step 0: Where are we?

**Setup runs only in the Code tab.** Setup done there is saved in the Claude desktop app's settings, so afterward Basecamp works in **all three places**: Code, regular chat, and Cowork.

- **Basecamp tools already available** (you can see tools like `basecamp_projects`)? It's already set up. Skip setup and help with what they asked, wherever you are.
- **In the Code tab** (Claude Code; you can run shell commands on their Mac): do the setup below.
- **In Cowork or regular chat: don't set it up.** Cowork runs commands in a temporary sandbox, so an install there disappears when the session ends and needs a new sign-in every time. Regular chat can't run commands at all. Don't try, and don't work around it. Say:

  > "Basecamp setup needs to happen in the **Code** tab, just once. Open the Claude desktop app, click **Code** at the top, start a new session, and say **"set up Basecamp."** It takes about two minutes. After that, Basecamp works here too."

## Setup (Code tab)

Run each step and check its result before moving on.

**1. Check what's already there.**
```bash
ls ~/.local/bin/basecamp 2>/dev/null && ~/.local/bin/basecamp --version && ~/.local/bin/basecamp auth status
```
If it's installed and signed in, skip to step 4. If they asked to update, run `~/.local/bin/basecamp upgrade` first.

**2. Install (no admin needed).**
```bash
curl -fsSL https://basecamp.com/install-cli | BASECAMP_NONINTERACTIVE=1 BASECAMP_SETUP_AGENT=none bash
```
It puts `basecamp` in `~/.local/bin` and checks the download's checksum. `BASECAMP_SETUP_AGENT=none` stops the installer from changing Claude's settings, because you'll do that in step 5. The installer still adds its own Basecamp skill at `~/.agents/skills/basecamp`, and it may add `~/.local/bin` to their PATH in `~/.zshrc` or `~/.profile`. Both are expected.

If this fails, look at the error. A network block often shows up as a vague error, such as "Could not determine latest version," rather than a clear connection error. See [Network blocks](#network-blocks).

**3. Sign in.** Run this in the background, because it waits for the person:
```bash
~/.local/bin/basecamp auth login
```
It opens their browser to a Basecamp approval page automatically. Keep that behavior; don't add `--no-browser`. It also prints a link and a code.

**Before you wait for approval, send a chat message with the link and code. Don't skip this, even if you expect the browser to open.** The browser tab can open behind other windows or in a window they aren't looking at, and without the link in chat, a non-technical person just sees Claude go quiet. Read the output (wait a second or two for the link to appear), then send:

> "A Basecamp page just opened in your browser. If you don't see it, click this link: <link>. The code is **<code>**. Sign in if it asks, then click **Approve**."

Only after that message is sent, check the output every 3–5 seconds for `Authentication successful!`, and say so as soon as it appears. Approval usually lands within seconds of their click. The code expires in 10 minutes. If it expires, or they approved and nothing happened after about 30 seconds, stop that login and start a new one. The login is saved in their Mac's Keychain, so there's no password or token file to manage. Ignore the CLI's "Connect it to Basecamp: basecamp setup claude" tip; step 5 handles that.

**4. Pick the default account. Required: without it, the MCP server won't start** ("Account ID required").
```bash
~/.local/bin/basecamp accounts list
```
If there's one account, set it. If there are several, ask which to use. The Ark's account may be named **"Media - The Ark Church"** even though the whole staff uses it.
```bash
~/.local/bin/basecamp config set account_id <ACCOUNT_ID> --global
```

**5. Connect Claude.** Always use the **full path** `/Users/<username>/.local/bin/basecamp`, because the Claude app doesn't see Terminal's PATH. Get it with `echo $HOME/.local/bin/basecamp`.

- **Claude desktop app (regular chat and Cowork):** edit `~/Library/Application Support/Claude/claude_desktop_config.json`. Back it up first (`cp` it with a `.bak` suffix). Then add or replace this entry inside `"mcpServers"`, keeping all other entries and keeping the JSON valid. Create the file as `{"mcpServers": {...}}` if it doesn't exist.
  ```json
  "basecamp": { "command": "/Users/<username>/.local/bin/basecamp", "args": ["mcp"] }
  ```
- **Claude Code:** `claude mcp add -s user basecamp -- /Users/<username>/.local/bin/basecamp mcp`. If `claude` isn't found, back up `~/.claude.json` and add the same entry to its top-level `"mcpServers"` object.
- If there's an existing `basecamp` entry pointing at `Basecamp-MCP-Server` (the old, retired Python setup), replace it. That old setup's folder (usually `~/Basecamp-MCP-Server`) holds an old Basecamp login and the church's retired app credentials in its `.env` file. Offer to move the whole folder to the Trash, and do it once they say yes.

**6. Test it.**
```bash
~/.local/bin/basecamp projects list --json | head -c 400
```
You should see their projects. Then tell them:

> "You're all set! **Right now, fully quit the Claude app (Cmd-Q) and reopen it.** After that, Basecamp works in regular chat, in Cowork, and in new Code sessions. Try asking, 'What's on my Basecamp to-do list?'"

Make sure they quit **right away**. While it's open, the Claude app keeps its own copy of its settings and sometimes saves that copy back over `claude_desktop_config.json`, which erases the entry you just added. Quitting promptly makes the app load your edit when it reopens. The Basecamp tools won't appear in the Code session you're in now; they load in sessions started after the restart.

**7. If Basecamp is missing after the restart** (no Basecamp tools in a new session), check that the `basecamp` entry is still in `claude_desktop_config.json`. If the app erased it, add it again (step 5) and have them quit right away. If the entry is there but the tools still don't load, run `~/.local/bin/basecamp auth status` and the step 6 test to find which part failed.

## Network blocks

If the install or sign-in can't connect, the church network may be blocking an address. Don't try workarounds. Tell the person to send this to Jonathan (IT), with the exact error:

> "Basecamp setup was blocked. It needs access to: basecamp.com, app.basecamp.com, launchpad.37signals.com, 3.basecampapi.com, github.com, api.github.com, raw.githubusercontent.com, release-assets.githubusercontent.com."

## Updating and removing

- **Update:** `~/.local/bin/basecamp upgrade`. It checks the download's signature and checksum and restores the old version if anything fails. Suggest it if tools act strangely or it's been a few months. Updating also happens in the Code tab.
- **Sign out:** `~/.local/bin/basecamp auth logout`.
- **Remove:** sign out, delete the `basecamp` entries from the two Claude config files above, then delete `~/.local/bin/basecamp`, `~/.config/basecamp/`, `~/.cache/basecamp/`, and `~/.agents/skills/basecamp/`.

## Working in Basecamp once connected

See [reference/using-basecamp.md](reference/using-basecamp.md) for how the tools work, including **@mentions**, which need a special tag. Write every to-do, message, and comment to The Ark's communication standards.
