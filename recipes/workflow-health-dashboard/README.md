# Workflow Health Dashboard — a Rock RMS recipe

A drop-in **Workflow Health dashboard** for any Rock RMS instance: one admin page of live
KPIs and one-click actions, a filterable instances grid, JSON endpoints for AI agents, and
daily trend metrics — all fed by a single `workflow-health` Lava application so admins and
agents always see the same numbers.

It answers the questions every Rock admin eventually asks about the workflow engine:

- How many workflows are **active**, and of how many types?
- Is anything **stuck** (flagged `IsProcessing` for over an hour, so the engine won't retry it)?
- What's been **running too long** (90+ days) and is a candidate to expire?
- Is the **Process Workflows** job healthy, and is **Complete Workflows** actually running?
- What's driving **table growth** — `WorkflowLog` rows and completed instances kept forever?

…and then lets you *act*: expire a runaway instance, clear a stuck flag, set a log-retention
period, or sweep an entire type's stale instances — each action audited to the signed-in admin.

This recipe creates **new** pages and objects; it never edits or deletes anything you already
have. Everything is idempotent and discovered by name, so it's safe to run and re-run.

> **Requirements:** Rock **v17+** (Lava Applications were introduced in v17; verified on
> **19.3.1**). A REST key whose person is in an admin security role, with the v2 REST Execute
> grants (see [`DEPLOY.md`](DEPLOY.md) Phase 0). No plugins required — everything is core Rock.

## What gets created

| Piece | What it is |
|---|---|
| Lava application `workflow-health` | 5 GET endpoints (`summary`, `types`, `instances`, `engine`, `logs`) serving HTML fragments by default and agent JSON with `?format=json`, plus POST `action-sweep` (guarded bulk expire) |
| Dashboard page | A **new** page created under a parent you choose — a Lava Application Content block: KPI strip + lazy-loaded HTMX panels + action buttons (`dashboard-block.lava`) |
| Instances grid page | A **new** child page: Page Parameter Filter block (Person / WorkflowTypeId / MinAgeDays / StuckOnly) above a classic Dynamic Data grid (`dd-instances-query.sql`, `dd-grid-header.html`) |
| Trend metrics | Category "Workflow Health" + 4 daily SQL metrics (active, stuck, log rows, completed kept forever) |

Person filtering matches workflows a person **initiated or is currently assigned to** (any of
their aliases). "Stuck" everywhere means `IsProcessing = 1` for over an hour.

## Files

- `provision.py` — one idempotent script that discovers, creates, secures, and pushes everything
- `dashboard-block.lava` — the dashboard shell (Lava Application Content block template)
- `endpoints/ep-*.lava` — the six endpoint templates (tokens: `__WFH_DASHBOARD_PAGE_ID__`, `__WFH_INSTANCES_PAGE_ID__`, `__WFH_JOBS_PAGE_ID__` — the provisioner substitutes them)
- `dd-instances-query.sql`, `dd-grid-header.html` — the instances-grid block settings
- `DEPLOY.md` — **the step-by-step deployment guide, with screenshots — read this first**
- `images/` — screenshots referenced by `DEPLOY.md`

No file in this folder contains an instance-specific id: page links use `__WFH_*__` tokens
resolved at push time, and every other id is discovered by name/path/guid at run time.

## Quick start (scripted)

By default the dashboard page is created under the stock **Power Tools** page (found by its
well-known Rock GUID, so it works on any instance). To put it somewhere else, set
`WFH_PARENT_PAGE_ID` to the id of the page you want it under — you decide where it lives.

```bash
export WFH_BASE_URL="https://rock.example.org"     # your Rock base URL
export WFH_API_KEY="<REST key in your admin role>"
# export WFH_PARENT_PAGE_ID=123                    # optional — defaults to stock Power Tools
python3 provision.py
```

The script prints a full inventory of what it found and created, and aborts with a clear
message if any name-based discovery doesn't match exactly one row (so it never guesses). Full
prerequisites, options, verification, and rollback are in **[`DEPLOY.md`](DEPLOY.md)** — which
also has a UI-only path if you'd rather build it by hand with no API key.

There is no scripted "undo," and nothing here needs one: because it only *adds* named objects,
rollback is deleting what it created. `DEPLOY.md` has the exact list.

## Optional settings

| Variable | Default | Meaning |
|---|---|---|
| `WFH_PARENT_PAGE_ID` | stock Power Tools page | Id of the page to create the dashboard **under** — set it to place the dashboard anywhere in your admin tree |
| `WFH_LAYOUT_ID` | parent page's layout | Layout for the new pages |
| `WFH_ADMIN_ROLE` | `RSR - Rock Administration` | Security role NAME granted full access (Rock's built-in admin role; change to yours if different) |
| `WFH_JOBS_PAGE_ID` | discovered via route `admin/system/jobs` | Your Jobs Administration page id |
| `WFH_METRIC_SCHEDULE` | `Daily 3 AM Metric` | An existing daily schedule's name (must exist), or set `WFH_SKIP_METRICS=1` |
| `WFH_DASHBOARD_ROUTE` / `WFH_INSTANCES_ROUTE` | `admin/workflow-health[/instances]` | Pretty-URL routes; blank to skip |
| `WFH_SKIP_METRICS` | — | `1` to skip the metrics phase |

## Gotchas worth knowing (learned building this)

These bit during development; they'll save you time on any Lava-application work:

- `LavaApplication.ConfigurationRiggingJson` **must not be NULL** — the controller deserializes
  it unconditionally (HTTP 500). The provisioner sets `{}`; the admin UI does this for you.
- Every Lava-application request needs the **`X-Helix-CSRF-Protection: true`** header unless CSRF
  is disabled per endpoint — the 401 happens *before* auth, so it looks like an auth failure.
- The public endpoint URL is `/api/v2/lava-app/1/{app-slug}/{endpoint-slug}` — the `1` is the
  **route version**, not the application id (so it's the same on every instance).
- v2 `PATCH` on `lavaendpoints` **400s if you send immutable fields** — PATCH only
  `codeTemplate` / `description` / `enabledLavaCommands`.
- Large `AttributeValue` writes can hang behind an aborted prior request's lock — the provisioner
  uses DELETE + POST instead of PATCH for big block settings.
- Page **routes created via REST stay dormant until an app restart or cache clear** — so all
  links use `/page/{id}`; the pretty routes are bonus aliases.
- **Fluid Lava:** backslash regex classes (`\d`) inside filter arguments break the tag parser —
  use `[0-9]`.
- v1 OData can't return `BlockType.Path` on Rock 19 — block-type discovery uses v2 entity search.
- Endpoint-level security (`EndpointExecute` mode) 401'd despite correct Auth rows on 19.3.1, so
  the sweep endpoint runs in application-scope security; flip it to endpoint mode before ever
  broadening the app's `ExecuteView` beyond your admin role.

## AI agents

Each read endpoint returns agent-readable JSON with `?format=json` — the same data the HTML
panels render. Point a tool/agent at `GET /api/v2/lava-app/1/workflow-health/summary?format=json`
(and `types`, `instances`, `engine`, `logs`) to let an assistant report on workflow health, and
at the guarded `POST .../action-sweep` to let it propose (never silently perform) cleanups.
