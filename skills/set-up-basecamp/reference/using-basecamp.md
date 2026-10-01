# Using Basecamp through the official MCP server

Notes from testing `basecamp mcp` (CLI v0.11.0) against The Ark's Basecamp on Wednesday, September 30, 2026.

## How the tools are shaped

There are about 15 tools, one per area: `basecamp_projects`, `basecamp_todos`, `basecamp_cards`, `basecamp_messages`, `basecamp_campfires`, `basecamp_schedules`, `basecamp_files`, `basecamp_people`, `basecamp_reports`, `basecamp_account`, and others. Each takes:

```json
{ "action": "<action name>", "params": { ... } }
```

- **Don't guess action names or fields.** Call `{"action": "describe"}` to list a tool's actions, and `{"action": "describe", "params": {"action": "create_todo"}}` to see one action's fields.
- **Lists are paged.** A response with `next_page` has more results. Request `"params": {"page": N}` until `next_page` is gone. Projects and people both run past one page.
- **IDs chain together.** For example: project → `get_project` → its `dock` lists the project's tools; the to-do set is the `todoset` entry → `list_todolists` with `todosetId` → `create_todo` with `todolistId`.
- If the person wants to look without changing anything, the server can run read-only (`basecamp mcp --read-only`).

## @mentioning someone

A mention notifies the person, so only mention someone when the staff member asks you to. Some actions have a shortcut: `basecamp_messages create_comment` takes a `mentions` list of person IDs. Everything else, including to-dos, needs the mention tag written into the rich-text field (`description` for to-dos):

1. Find the person: `basecamp_people` → `list_people`, then match the name. Page through if needed.
2. Take their `attachable_sgid`, not their `id`.
3. Put this in the HTML:
   ```html
   <div>Hey <bc-attachment sgid="ATTACHABLE_SGID" content-type="application/vnd.basecamp.mention"></bc-attachment>, can you take a look?</div>
   ```
4. Read the item back with `get_todo`. A working mention comes back with the person's avatar and name filled in.

To assign a to-do instead of mentioning someone, use `assignee_ids`, which takes plain person IDs. Assigning also notifies them.

## Before changing anything

- Confirm before creating, completing, moving, or trashing anything people will see. Say what you're about to do in one line.
- Trashing can be undone from Basecamp's trash for about 30 days. Even so, only trash what the person asked you to.
- Write everything people will read to The Ark's communication standards.
