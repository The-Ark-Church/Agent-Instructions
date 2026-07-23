#!/usr/bin/env python3
"""Provision the Workflow Health dashboard on any Rock RMS instance. Idempotent.

Creates a brand-new "Workflow Health" dashboard page (plus its child instances grid,
Lava application, six endpoints, security, and daily metrics) under a parent page you
choose. Safe to re-run: every object is discovered by stable name/path/guid and created
only if missing. The script carries NO instance-specific ids — the page-id tokens inside
the templates (__WFH_DASHBOARD_PAGE_ID__ etc.) are substituted with the ids of the pages
this run creates, and any discovery that does not match exactly one row aborts with a
clear message instead of guessing.

Required environment:
  WFH_BASE_URL          e.g. https://rock.example.org (use an origin/no-CDN host if you have one)
  WFH_API_KEY           REST key whose person belongs to the admin security role (below)

Optional environment:
  WFH_PARENT_PAGE_ID    Id of the EXISTING page to create the new dashboard page UNDER. Default:
                        the stock "Power Tools" page (found by its well-known Rock GUID, present
                        on every instance). Set this to put the dashboard somewhere else — the
                        dashboard page itself is created by this script, so point this at its
                        intended PARENT, never at the dashboard page.
  WFH_LAYOUT_ID         Layout id for the new pages. Default: inherit the parent page's layout.
  WFH_ADMIN_ROLE        Security role NAME to grant full access. Default 'RSR - Rock
                        Administration' (Rock's built-in administrators role, present on
                        every instance). Set this to your own admin role if you prefer.
  WFH_JOBS_PAGE_ID      Jobs Administration page id; default: discovered via the route
                        'admin/system/jobs', else required.
  WFH_METRIC_SCHEDULE   Schedule NAME for the daily metrics (default 'Daily 3 AM Metric').
                        Must already exist on your instance — pick a daily schedule you
                        have, or set WFH_SKIP_METRICS=1.
  WFH_SKIP_METRICS      '1' to skip the metrics phase entirely.

Prerequisites on the target (see DEPLOY.md): the key's role needs the four v2 REST Execute
grants — the Lava application/endpoint entities are v2-only. Rock ships a helper for this;
DEPLOY.md Phase 0 shows how to verify and grant.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

SP = os.path.dirname(os.path.abspath(__file__))

BASE = os.environ.get("WFH_BASE_URL", "").rstrip("/")
KEY = os.environ.get("WFH_API_KEY", "")
_parent_env = os.environ.get("WFH_PARENT_PAGE_ID", "")
if not BASE or not KEY:
    sys.exit("Set WFH_BASE_URL and WFH_API_KEY (WFH_PARENT_PAGE_ID is optional) — see DEPLOY.md")
PARENT_PAGE_ID = int(_parent_env) if _parent_env.isdigit() else None

APP_SLUG = "workflow-health"
APP_NAME = "Workflow Health"
DASH_PAGE_NAME = "Workflow Health"
CHILD_PAGE_NAME = "Workflow Health - Instances"
DASH_BLOCK_NAME = "Workflow Health Dashboard"
GRID_BLOCK_NAME = "Workflow Instances Grid"
PPF_BLOCK_NAME = "Instance Filters"
# Pretty-URL routes are optional aliases and are independent of where the page lives in the
# tree. Override with WFH_DASHBOARD_ROUTE / WFH_INSTANCES_ROUTE, or set either to an empty
# string to skip creating it. The /page/{id} links always work regardless.
ROUTE_DASHBOARD = os.environ.get("WFH_DASHBOARD_ROUTE", "admin/power-tools/workflow-health")
ROUTE_INSTANCES = os.environ.get("WFH_INSTANCES_ROUTE", "admin/power-tools/workflow-health/instances")
ADMIN_ROLE_NAME = os.environ.get("WFH_ADMIN_ROLE", "RSR - Rock Administration")

# Stock Rock "Power Tools" page — well-known seeded GUID, present on every instance. Used as
# the default parent when WFH_PARENT_PAGE_ID isn't set; override that var to place the dashboard
# anywhere else in your admin tree.
POWER_TOOLS_GUID = "7f1f4130-cb98-473b-9de1-7a886d2283ed"

ENDPOINTS = [
    # (file, name, slug, http method (0=GET, 1=POST), security mode (1=ApplicationView))
    ("ep-summary.lava", "Summary", "summary", 0, 1),
    ("ep-types.lava", "Types", "types", 0, 1),
    ("ep-instances.lava", "Instances", "instances", 0, 1),
    ("ep-engine.lava", "Engine", "engine", 0, 1),
    ("ep-logs.lava", "Logs", "logs", 0, 1),
    # Sweep also runs ApplicationView (mode 1): EndpointExecute (mode 0) 401'd on Rock 19.3.1
    # despite correct Auth rows (suspected AuthCache init quirk). Endpoint-level Execute
    # allow/deny rows are still created below so mode 0 can be adopted later — REQUIRED before
    # the application's ExecuteView is ever granted beyond the admin role.
    ("ep-action-sweep.lava", "Action: Sweep Stale", "action-sweep", 1, 1),
]

METRICS = [
    ("Active Workflows", "Count of workflow instances with no CompletedDateTime.",
     "SELECT COUNT(*) FROM [Workflow] WHERE [CompletedDateTime] IS NULL"),
    ("Stuck Workflow Processing", "Active instances flagged IsProcessing for over an hour (engine will not retry them).",
     "SELECT COUNT(*) FROM [Workflow] WHERE [CompletedDateTime] IS NULL AND [IsProcessing] = 1 AND ([LastProcessedDateTime] IS NULL OR [LastProcessedDateTime] < DATEADD(HOUR, -1, GETDATE()))"),
    ("Workflow Log Rows", "Total rows in WorkflowLog (via partition stats; the workflow table-size driver).",
     "SELECT ISNULL(SUM([pt].[rows]), 0) FROM [sys].[partitions] AS [pt] WHERE [pt].[object_id] = OBJECT_ID('[dbo].[WorkflowLog]') AND [pt].[index_id] IN (0, 1)"),
    ("Completed Workflows Kept Forever", "Completed instances of types with no Completed Workflow Retention Period.",
     "SELECT COUNT(*) FROM [Workflow] AS [w] JOIN [WorkflowType] AS [wt] ON [wt].[Id] = [w].[WorkflowTypeId] WHERE [w].[CompletedDateTime] IS NOT NULL AND ISNULL([wt].[CompletedWorkflowRetentionPeriod], 0) = 0"),
]

created = {"appId": None, "appGuid": None, "endpoints": {}, "pages": {}, "blocks": {}, "routes": {}, "metrics": {}, "authIds": []}


# ---------- HTTP helpers ----------

def api(method, path, body=None, timeout=90):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Authorization-Token", KEY)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw) if raw else None
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


def get_list(path):
    status, rows = api("GET", path)
    if status != 200:
        sys.exit(f"GET {path} -> {status} {rows}")
    return rows or []


def v2_search(model, where, select="new (Id, Name)"):
    status, resp = api("POST", f"/api/v2/models/{model}/search", {"where": where, "select": select})
    if status != 200:
        sys.exit(f"v2 search {model} failed ({status}): {resp}\n"
                 "If this is 401/403, the key's role is missing the v2 REST Execute grants — see DEPLOY.md Phase 0.")
    if isinstance(resp, dict):
        return resp.get("items") or []
    return resp or []


def one(rows, what):
    if len(rows) != 1:
        sys.exit(f"DISCOVERY FAILED: expected exactly 1 {what}, found {len(rows)}: {rows[:3]} — verify on the target and fix before re-running.")
    return rows[0]


def flt(expr):
    return urllib.parse.quote(expr)


# ---------- Phase D: discovery (no writes) ----------

print(f"== Workflow Health provisioner -> {BASE} ==")
print("-- discovering instance facts (no writes yet) --")

et = {}
for name in ["Rock.Model.Block", "Rock.Model.Metric", "Rock.Model.LavaApplication", "Rock.Model.LavaEndpoint"]:
    et[name] = one(get_list(f"/api/EntityTypes?$filter={flt(f'Name eq %27{name}%27'.replace('%27', chr(39)))}"), f"EntityType '{name}'")["Id"]
ET_BLOCK, ET_METRIC = et["Rock.Model.Block"], et["Rock.Model.Metric"]
ET_LAVA_APP, ET_LAVA_EP = et["Rock.Model.LavaApplication"], et["Rock.Model.LavaEndpoint"]

admin_role = one(get_list(f"/api/Groups?$filter={flt(chr(39).join(['Name eq ', ADMIN_ROLE_NAME, ' and IsSecurityRole eq true']))}"), f"security role '{ADMIN_ROLE_NAME}' (set WFH_ADMIN_ROLE if yours differs)")
GROUP_ADMIN = admin_role["Id"]

ft = {}
for name in ["Person", "Integer", "Boolean"]:
    ft[name] = one(get_list(f"/api/FieldTypes?$filter={flt(f'Name eq ' + chr(39) + name + chr(39))}"), f"FieldType '{name}'")["Id"]

# Block types by stable identity (WebForms by Path; Obsidian by Name with null Path).
# v1 OData no longer exposes BlockType.Path (Rock 19) — use v2 entity search, which queries real columns.
BT_DD = one(v2_search("blocktypes", 'Path == "~/Blocks/Reporting/DynamicData.ascx"'), "Dynamic Data block type")["id"]
BT_PPF = one(v2_search("blocktypes", 'Path == "~/Blocks/Reporting/PageParameterFilter.ascx"'), "Page Parameter Filter block type")["id"]
BT_LAC = one(v2_search("blocktypes", 'Name == "Lava Application Content" && Path == null'), "Lava Application Content block type (Path null)")["id"]


def block_setting_attr(block_type_id, key):
    rows = get_list(f"/api/Attributes?$filter={flt(f'EntityTypeQualifierColumn eq ' + chr(39) + 'BlockTypeId' + chr(39) + f' and EntityTypeQualifierValue eq ' + chr(39) + str(block_type_id) + chr(39) + f' and Key eq ' + chr(39) + key + chr(39))}")
    return one(rows, f"attribute '{key}' on BlockTypeId {block_type_id}")["Id"]

ATTR_LAC_APPLICATION = block_setting_attr(BT_LAC, "Application")
ATTR_LAC_TEMPLATE = block_setting_attr(BT_LAC, "LavaTemplate")
ATTR_DD = {k: block_setting_attr(BT_DD, k) for k in
           ["Query", "QueryParams", "UrlMask", "GridHeaderContent", "ShowExcelExport", "ShowGridFilter",
            "WrapInPanel", "PanelTitle", "Timeout", "PersonReport", "UpdatePage"]}
ATTR_PPF = {k: block_setting_attr(BT_PPF, k) for k in
            ["BlockTitleText", "BlockTitleIconCSSClass", "ShowBlockTitle", "FilterButtonText",
             "ShowFilterButton", "ShowResetFiltersButton", "FiltersPerRow", "FilterButtonSize",
             "DoesSelectionCausePostback"]}

# Parent page: explicit WFH_PARENT_PAGE_ID wins; otherwise default to the stock Power Tools page.
if PARENT_PAGE_ID is None:
    pt_q = "Guid eq guid" + chr(39) + POWER_TOOLS_GUID + chr(39)
    pt = one(get_list(f"/api/Pages?$filter={flt(pt_q)}"),
             "stock Power Tools page by guid (set WFH_PARENT_PAGE_ID to choose a different parent)")
    PARENT_PAGE_ID = pt["Id"]
    print(f"   parent defaulted to stock Power Tools page (Id {PARENT_PAGE_ID})")
# The parent page must exist; the dashboard page is created UNDER it (this run).
status, parent_page = api("GET", f"/api/Pages/{PARENT_PAGE_ID}")
if status != 200:
    sys.exit(f"Parent page {PARENT_PAGE_ID} not found ({status}) — WFH_PARENT_PAGE_ID must be an existing page to create the dashboard under.")
layout_env = os.environ.get("WFH_LAYOUT_ID", "")
LAYOUT_ID = int(layout_env) if layout_env.isdigit() else parent_page["LayoutId"]
print(f"   parent page {PARENT_PAGE_ID} ('{parent_page['InternalName']}'), new pages use layout {LAYOUT_ID}")

# Jobs page: explicit env wins; else discover a route like admin/system/jobs
jobs_env = os.environ.get("WFH_JOBS_PAGE_ID", "")
if jobs_env.isdigit():
    JOBS_PAGE_ID = int(jobs_env)
else:
    routes = [r for r in get_list(f"/api/PageRoutes?$filter={flt('Route eq ' + chr(39) + 'admin/system/jobs' + chr(39))}")]
    if len(routes) == 1:
        JOBS_PAGE_ID = routes[0]["PageId"]
    else:
        sys.exit("Could not discover the Jobs Administration page (route 'admin/system/jobs') — set WFH_JOBS_PAGE_ID explicitly.")
print(f"   jobs page {JOBS_PAGE_ID}")

# Metric prerequisites
metric_source_type = one(get_list(f"/api/DefinedTypes?$filter={flt('Name eq ' + chr(39) + 'Source Value Type' + chr(39))}"), "DefinedType 'Source Value Type'")
sql_dv = one(get_list(f"/api/DefinedValues?$filter={flt(f'DefinedTypeId eq {metric_source_type[chr(73)+chr(100)]} and Value eq ' + chr(39) + 'SQL' + chr(39))}"), "DefinedValue 'SQL' under Source Value Type")
SOURCE_TYPE_SQL_ID = sql_dv["Id"]
sched_name = os.environ.get("WFH_METRIC_SCHEDULE", "Daily 3 AM Metric")
skip_metrics = os.environ.get("WFH_SKIP_METRICS") == "1"
if not skip_metrics:
    sched = one(get_list(f"/api/Schedules?$filter={flt('Name eq ' + chr(39) + sched_name + chr(39))}"), f"schedule '{sched_name}' (set WFH_METRIC_SCHEDULE to a daily schedule you have, or WFH_SKIP_METRICS=1)")
    SCHEDULE_ID = sched["Id"]
    print(f"   discovery complete (role Group {GROUP_ADMIN}, DD {BT_DD}, PPF {BT_PPF}, LAC {BT_LAC}, SQL source {SOURCE_TYPE_SQL_ID}, schedule {SCHEDULE_ID})")
else:
    print(f"   discovery complete (role Group {GROUP_ADMIN}, DD {BT_DD}, PPF {BT_PPF}, LAC {BT_LAC}); metrics skipped")


# ---------- Phase 1: Lava application + rigging ----------

print("-- lava application --")
rows = v2_search("lavaapplications", f'Slug == "{APP_SLUG}"', select="new (Id, Guid)")
if rows:
    app_id, app_guid = rows[0]["id"], str(rows[0]["guid"])
    print(f"   application exists (Id {app_id})")
else:
    status, resp = api("POST", "/api/v2/models/lavaapplications", {
        "name": APP_NAME, "slug": APP_SLUG,
        "description": "Data + action layer for the Workflow Health dashboard and AI agent tools. Each read endpoint returns an HTML fragment by default and JSON with ?format=json. Source of record: the workflow-health-dashboard recipe.",
        "isActive": True, "isSystem": False,
        # Must not be null: LavaAppController deserializes it unconditionally (500 otherwise).
        "configurationRiggingJson": "{}",
    })
    if status not in (200, 201):
        sys.exit(f"application create failed ({status}): {resp}")
    rows = v2_search("lavaapplications", f'Slug == "{APP_SLUG}"', select="new (Id, Guid)")
    app_id, app_guid = rows[0]["id"], str(rows[0]["guid"])
    print(f"   created application Id {app_id}")
created["appId"], created["appGuid"] = app_id, app_guid


# ---------- Phase 2: pages + routes (before endpoints — templates need the ids) ----------

print("-- pages & routes --")

# Dashboard page — created under the parent you chose (idempotent by parent + internal name).
rows = get_list(f"/api/Pages?$filter={flt(f'ParentPageId eq {PARENT_PAGE_ID} and InternalName eq ' + chr(39) + DASH_PAGE_NAME + chr(39))}")
if rows:
    dash_page_id = rows[0]["Id"]
    print(f"   dashboard page exists (Id {dash_page_id})")
else:
    siblings = get_list(f"/api/Pages?$filter={flt(f'ParentPageId eq {PARENT_PAGE_ID}')}")
    next_order = max([s.get("Order", 0) for s in siblings], default=-1) + 1
    status, dash_page_id = api("POST", "/api/Pages", {
        "InternalName": DASH_PAGE_NAME, "PageTitle": DASH_PAGE_NAME, "BrowserTitle": DASH_PAGE_NAME,
        "Description": "Live workflow engine health: KPI strip, active workflow types, longest-running instances, log/retention hygiene, and one-click admin actions. Data comes from the workflow-health Lava application.",
        "ParentPageId": PARENT_PAGE_ID, "LayoutId": LAYOUT_ID, "IsSystem": False,
        "RequiresEncryption": False,
        "EnableViewState": True,
        "PageDisplayTitle": True, "PageDisplayBreadCrumb": True, "PageDisplayIcon": True,
        "PageDisplayDescription": False,
        "DisplayInNavWhen": 0,  # WhenAllowed — shows in nav for users with access
        "MenuDisplayDescription": False, "MenuDisplayIcon": True, "MenuDisplayChildPages": False,
        "BreadCrumbDisplayName": True, "BreadCrumbDisplayIcon": False,
        "IconCssClass": "fa fa-heartbeat", "Order": next_order, "OutputCacheDuration": 0,
        "IncludeAdminFooter": True, "AllowIndexing": False,
    })
    if status not in (200, 201):
        sys.exit(f"dashboard page create failed ({status}): {dash_page_id}")
    print(f"   created dashboard page Id {dash_page_id}")

# Instances grid page — child of the dashboard page.
rows = get_list(f"/api/Pages?$filter={flt(f'ParentPageId eq {dash_page_id} and InternalName eq ' + chr(39) + CHILD_PAGE_NAME + chr(39))}")
if rows:
    child_page_id = rows[0]["Id"]
    print(f"   child page exists (Id {child_page_id})")
else:
    status, child_page_id = api("POST", "/api/Pages", {
        "InternalName": CHILD_PAGE_NAME, "PageTitle": CHILD_PAGE_NAME, "BrowserTitle": CHILD_PAGE_NAME,
        "Description": "Sortable, exportable grid of active workflow instances. Filters: Person (initiated or assigned), WorkflowTypeId, MinAgeDays, StuckOnly.",
        "ParentPageId": dash_page_id, "LayoutId": LAYOUT_ID, "IsSystem": False,
        "RequiresEncryption": False,
        "EnableViewState": True,  # classic WebForms Dynamic Data block needs ViewState
        "PageDisplayTitle": True, "PageDisplayBreadCrumb": True, "PageDisplayIcon": True,
        "PageDisplayDescription": False,
        "DisplayInNavWhen": 2,  # Never — reached via dashboard links
        "MenuDisplayDescription": False, "MenuDisplayIcon": False, "MenuDisplayChildPages": False,
        "BreadCrumbDisplayName": True, "BreadCrumbDisplayIcon": False,
        "IconCssClass": "fa fa-list", "Order": 0, "OutputCacheDuration": 0,
        "IncludeAdminFooter": True, "AllowIndexing": False,
    })
    if status not in (200, 201):
        sys.exit(f"child page create failed ({status}): {child_page_id}")
    print(f"   created child page Id {child_page_id}")
created["pages"] = {"dashboard": dash_page_id, "instances": child_page_id}

for page_id, route in [(dash_page_id, ROUTE_DASHBOARD), (child_page_id, ROUTE_INSTANCES)]:
    if not route.strip():
        print("   route skipped (blank)")
        continue
    rows = get_list(f"/api/PageRoutes?$filter={flt('Route eq ' + chr(39) + route + chr(39))}")
    if rows:
        if rows[0]["PageId"] != page_id:
            sys.exit(f"route '{route}' already exists but points at page {rows[0]['PageId']} — resolve before re-running.")
        print(f"   route exists: {route}")
        created["routes"][route] = rows[0]["Id"]
    else:
        status, rid = api("POST", "/api/PageRoutes", {"PageId": page_id, "Route": route, "IsSystem": False, "IsGlobal": False})
        print(f"   created route {route} -> {status} (Id {rid}; dormant until app restart/cache clear — links use /page/id)")
        created["routes"][route] = rid


# ---------- token substitution ----------

def load(rel):
    with open(os.path.join(SP, rel)) as f:
        s = f.read()
    s = s.replace("__WFH_DASHBOARD_PAGE_ID__", str(dash_page_id))
    s = s.replace("__WFH_INSTANCES_PAGE_ID__", str(child_page_id))
    s = s.replace("__WFH_JOBS_PAGE_ID__", str(JOBS_PAGE_ID))
    if "__WFH_" in s:
        sys.exit(f"unresolved __WFH_ token remains in {rel} — add its substitution here before deploying.")
    return s


# ---------- Phase 3: endpoints ----------

print("-- endpoints --")
for fname, name, slug, http_method, sec_mode in ENDPOINTS:
    template = load(os.path.join("endpoints", fname))
    rows = v2_search("lavaendpoints", f'Slug == "{slug}" && LavaApplicationId == {app_id}', select="new (Id, IdKey)")
    if rows:
        ep_id = rows[0]["id"]
        # PATCH only mutable fields — a full payload (lavaApplicationId/slug/enums) 400s on v2 PATCH.
        status, resp = api("PATCH", f"/api/v2/models/lavaendpoints/{rows[0]['idKey']}", {"codeTemplate": template, "enabledLavaCommands": "Sql"})
        print(f"   updated {slug} (Id {ep_id}) -> {status}")
        if status not in (200, 204):
            sys.exit(f"endpoint update failed: {resp}")
    else:
        status, resp = api("POST", "/api/v2/models/lavaendpoints", {
            "lavaApplicationId": app_id, "name": name, "slug": slug,
            "description": f"Workflow Health {name} endpoint. Source of record: the workflow-health-dashboard recipe (endpoints/{fname}).",
            "httpMethod": http_method, "securityMode": sec_mode,
            "enabledLavaCommands": "Sql", "codeTemplate": template,
            "isActive": True, "isSystem": False,
        })
        if status not in (200, 201):
            sys.exit(f"endpoint {slug} create failed ({status}): {resp}")
        rows = v2_search("lavaendpoints", f'Slug == "{slug}" && LavaApplicationId == {app_id}')
        ep_id = rows[0]["id"]
        print(f"   created {slug} (Id {ep_id})")
    created["endpoints"][slug] = ep_id


# ---------- Phase 4: security ----------

print("-- security --")

def ensure_auth(entity_type_id, entity_id, action, allow, special_role, group_id, order):
    q = flt(f"EntityTypeId eq {entity_type_id} and EntityId eq {entity_id} and Action eq " + chr(39) + action + chr(39) + " and AllowOrDeny eq " + chr(39) + allow + chr(39) + " and SpecialRole eq " + chr(39) + str(special_role) + chr(39))
    rows = get_list(f"/api/Auths?$filter={q}")
    if rows:
        print(f"   auth exists: {action} {allow} sr={special_role}")
        return
    status, newid = api("POST", "/api/Auths", {
        "EntityTypeId": entity_type_id, "EntityId": entity_id, "Order": order,
        "Action": action, "AllowOrDeny": allow, "SpecialRole": special_role, "GroupId": group_id,
    })
    print(f"   auth {action} {allow} sr={special_role} group={group_id} -> {status} (Id {newid})")
    if status in (200, 201):
        created["authIds"].append(newid)

for action in ["View", "Edit", "Administrate", "ExecuteView"]:
    ensure_auth(ET_LAVA_APP, app_id, action, "A", 0, GROUP_ADMIN, 0)
ensure_auth(ET_LAVA_APP, app_id, "ExecuteView", "D", 1, None, 1)
# Endpoint-level rows for the sweep so it can move to EndpointExecute mode later.
sweep_id = created["endpoints"]["action-sweep"]
ensure_auth(ET_LAVA_EP, sweep_id, "Execute", "A", 0, GROUP_ADMIN, 0)
ensure_auth(ET_LAVA_EP, sweep_id, "Execute", "D", 1, None, 1)


# ---------- Phase 5: blocks ----------

print("-- blocks --")

def replace_attr(entity_id, attribute_id, value):
    q = flt(f"AttributeId eq {attribute_id} and EntityId eq {entity_id}")
    rows = get_list(f"/api/AttributeValues?$filter={q}")
    if rows:
        # DELETE + POST beats PATCH for large values (see README gotchas: lock hangs on big PATCHes)
        api("DELETE", f"/api/AttributeValues/{rows[0]['Id']}")
    status, newid = api("POST", "/api/AttributeValues", {"AttributeId": attribute_id, "EntityId": entity_id, "Value": value, "IsSystem": False})
    if status not in (200, 201):
        sys.exit(f"attribute value save failed ({status}) attr {attribute_id} on {entity_id}: {newid}")
    print(f"   attr {attribute_id} on block {entity_id} -> {status}")


def ensure_block(page_id, name, block_type_id, order):
    rows = get_list(f"/api/Blocks?$filter={flt(f'PageId eq {page_id} and Name eq ' + chr(39) + name + chr(39))}")
    if rows:
        print(f"   block exists: {name} (Id {rows[0]['Id']})")
        return rows[0]["Id"]
    status, bid = api("POST", "/api/Blocks", {
        "PageId": page_id, "BlockTypeId": block_type_id, "Zone": "Main",
        "Name": name, "Order": order, "IsSystem": False, "OutputCacheDuration": 0,
    })
    if status not in (200, 201):
        sys.exit(f"block '{name}' create failed ({status}): {bid}")
    print(f"   created block {name} (Id {bid})")
    return bid

dash_block_id = ensure_block(dash_page_id, DASH_BLOCK_NAME, BT_LAC, 0)
replace_attr(dash_block_id, ATTR_LAC_APPLICATION, app_guid)
replace_attr(dash_block_id, ATTR_LAC_TEMPLATE, load("dashboard-block.lava"))

ppf_block_id = ensure_block(child_page_id, PPF_BLOCK_NAME, BT_PPF, 0)
grid_block_id = ensure_block(child_page_id, GRID_BLOCK_NAME, BT_DD, 1)
api("PATCH", f"/api/Blocks/{grid_block_id}", {"Order": 1})
created["blocks"] = {"dashboard": dash_block_id, "filters": ppf_block_id, "grid": grid_block_id}

# PPF filter definitions = block-scoped attributes on the PPF block instance
for key, name, ft_name, order, desc in [
    ("Person", "Person", "Person", 0, "Workflows this person initiated or is currently assigned to"),
    ("WorkflowTypeId", "Workflow Type Id", "Integer", 1, ""),
    ("MinAgeDays", "Min Age (days)", "Integer", 2, ""),
    ("StuckOnly", "Stuck Only", "Boolean", 3, "Only instances stuck IsProcessing for over an hour"),
]:
    q = flt("EntityTypeQualifierColumn eq " + chr(39) + "Id" + chr(39) + f" and EntityTypeQualifierValue eq " + chr(39) + str(ppf_block_id) + chr(39) + " and Key eq " + chr(39) + key + chr(39))
    rows = get_list(f"/api/Attributes?$filter={q}")
    if rows:
        print(f"   filter attr exists: {key}")
        continue
    status, aid = api("POST", "/api/Attributes", {
        "IsSystem": False, "FieldTypeId": ft[ft_name], "EntityTypeId": ET_BLOCK,
        "EntityTypeQualifierColumn": "Id", "EntityTypeQualifierValue": str(ppf_block_id),
        "Key": key, "Name": name, "Description": desc, "Order": order,
        "IsGridColumn": False, "IsMultiValue": False, "IsRequired": False,
    })
    print(f"   filter attr {key} -> {status} (Id {aid})")

for attr_id, value in [
    (ATTR_PPF["BlockTitleText"], "Filters"), (ATTR_PPF["BlockTitleIconCSSClass"], "fa fa-filter"),
    (ATTR_PPF["ShowBlockTitle"], "True"), (ATTR_PPF["FilterButtonText"], "Filter"),
    (ATTR_PPF["ShowFilterButton"], "True"), (ATTR_PPF["ShowResetFiltersButton"], "True"),
    (ATTR_PPF["FiltersPerRow"], "4"), (ATTR_PPF["FilterButtonSize"], "3"),
    (ATTR_PPF["DoesSelectionCausePostback"], "False"),
]:
    replace_attr(ppf_block_id, attr_id, value)

for key, value in [
    ("Query", load("dd-instances-query.sql")),
    ("QueryParams", "WorkflowTypeId=0,MinAgeDays=0,StuckOnly=0,Person="),
    ("UrlMask", "/Workflow/{Id}"),
    ("GridHeaderContent", load("dd-grid-header.html")),
    ("ShowExcelExport", "True"), ("ShowGridFilter", "True"), ("WrapInPanel", "True"),
    ("PanelTitle", "Active Workflow Instances"), ("Timeout", "30"),
    ("PersonReport", "False"), ("UpdatePage", "True"),
]:
    replace_attr(grid_block_id, ATTR_DD[key], value)


# ---------- Phase 6: metrics ----------

if skip_metrics:
    print("-- metrics skipped (WFH_SKIP_METRICS=1) --")
else:
    print("-- metrics --")
    rows = get_list(f"/api/Categories?$filter={flt(f'Name eq ' + chr(39) + 'Workflow Health' + chr(39) + f' and EntityTypeId eq {ET_METRIC}')}")
    if rows:
        cat_id = rows[0]["Id"]
        print(f"   category exists (Id {cat_id})")
    else:
        status, cat_id = api("POST", "/api/Categories", {"Name": "Workflow Health", "EntityTypeId": ET_METRIC, "IsSystem": False, "IconCssClass": "fa fa-heartbeat", "Order": 0})
        print(f"   category -> {status} (Id {cat_id})")
    for title, desc, sql in METRICS:
        rows = get_list(f"/api/Metrics?$filter={flt('Title eq ' + chr(39) + title + chr(39))}")
        if rows:
            metric_id = rows[0]["Id"]
            print(f"   metric exists: {title} (Id {metric_id})")
        else:
            status, metric_id = api("POST", "/api/Metrics", {
                "Title": title, "Description": desc, "IsSystem": False,
                "SourceValueTypeId": SOURCE_TYPE_SQL_ID, "SourceSql": sql,
                "ScheduleId": SCHEDULE_ID, "IsCumulative": False, "NumericDataType": 0,
            })
            if status not in (200, 201):
                sys.exit(f"metric '{title}' create failed ({status}): {metric_id}")
            print(f"   metric {title} -> Id {metric_id}")
        if not get_list(f"/api/MetricPartitions?$filter={flt(f'MetricId eq {metric_id}')}"):
            api("POST", "/api/MetricPartitions", {"MetricId": metric_id, "IsRequired": True, "Order": 0})
        if not get_list(f"/api/MetricCategories?$filter={flt(f'MetricId eq {metric_id}')}"):
            api("POST", "/api/MetricCategories", {"MetricId": metric_id, "CategoryId": cat_id, "Order": 0})
        created["metrics"][title] = metric_id

print("== provisioning complete ==")
print(json.dumps(created, indent=2, default=str))
print("Next: verification matrix in DEPLOY.md Phase 3; clear the Rock cache to activate the pretty routes.")
