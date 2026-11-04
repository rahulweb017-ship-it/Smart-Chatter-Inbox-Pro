# SMART CHATTER INBOX PRO
## Claude-ready Odoo 19 application build specification

**Project:** Smart Chatter Inbox Pro  
**Technical module name:** `sd_smart_chatter_inbox`  
**Target:** Odoo 19.0 Community and Enterprise (self-hosted or Odoo.sh)  
**Release target:** 19.0.1.0.0  
**Document status:** Build specification, v1.0 — 29 October 2026  
**Product owner:** Softdeviser  
**Primary delivery:** Installable Odoo addon with automated tests, README, screenshots, and deployment instructions.

> **Instruction for Claude:** This is an implementation assignment, not a request for another strategy document. Read this specification and `CLAUDE_START_HERE.md`; examine the checked-out Odoo 19 source tree; implement the first milestone and continue milestone-by-milestone with tests. Where Odoo 19 internals differ from this proposed design, use actual source signatures, document the difference, and do not fabricate APIs or claim unrun tests passed.

---

# 1. Executive product brief

## 1.1 Customer problem
Sales teams working in Odoo CRM must repeatedly open lead/opportunity records to review chatter, decide who should respond, and create follow-up activities. Native Discuss already offers an inbox and chatter; the proposed product **does not replicate all mail features**. It provides a purpose-built **CRM response-work queue**, with owner, status, snooze, filters, related lead context, and one-click handoff to the original chatter.

## 1.2 One-sentence product promise
**Turn conversations on Odoo CRM leads into an accountable, organized team follow-up queue, without exporting private customer messages or replacing Odoo's mail engine.**

## 1.3 Product goals / measurable outcomes
- An authorized salesperson can review the work queue without individually opening every opportunity.
- Salespeople can set status to **Needs Action**, **Waiting**, **Done**, or **Snoozed** and assign follow-up ownership.
- Queue filters show only records the user is permitted to access under Odoo's native CRM and multi-company rules.
- A user can jump to the original CRM record and use its native chatter and activity composer.
- The addon installs, updates, and uninstalls cleanly on a fresh Odoo 19 database with CRM installed.
- First UI response target: under ~2 seconds at p95 on a representative dataset, subject to environment sizing and benchmarking.

## 1.4 First release positioning
- **Customer:** SMB sales teams and Odoo implementers with 3–50 CRM users.
- **Primary modules:** `crm`, `mail`, `web`, with their normal transitive dependencies.
- **Core differentiator:** persistent, filterable *action status and owner for CRM conversations*, not a generic replacement mail client.
- **Suggested launch price:** $79–99 per paid Odoo app purchase (commercial assumption, subject to market validation).
- **Initial license:** OPL-1 if commercial proprietary distribution is chosen; check all bundled assets and dependencies for compatibility.

## 1.5 Competitive research (context only)
- An established comparator, **Mail Messages Easy Pro** by Cetmix, displayed approximately **511 cumulative purchases** and a price of **US$283.59** on its Odoo 19 listing during this research. Counts are historical cumulative marketplace signals, **not monthly sales or downloads**. The competing app includes a message preview, send/forward/edit/move features, and recovery of lost messages.
- Our MVP should *not* attempt those sophisticated and risky features. Our focus is lead-focused team workflow with simple setup.
- **IP constraint:** Competitor's OPL-1 code, assets, product copy, and UI cannot be copied or redistributed. Build an independently designed module using Odoo's public extension points.

## 1.6 Assumptions and constraints
1. Use an exact Odoo **19.0 checkout**, inspect its installed `crm`/`mail` source and adjust source-specific details before coding.
2. **Odoo Online SaaS** generally does not support arbitrary custom Python addons; target Odoo.sh/self-hosted instances.
3. No external email provider integration and no third-party API credentials are required in MVP.
4. No AI, WhatsApp, Gmail, Outlook, IMAP, SMTP synchronization, mass-email dispatch, or customer mailbox replication in MVP.
5. Do not modify core Odoo files. Avoid monkeypatching/private mail endpoints.
6. This plan makes no claim that a production environment or repository is already available to Claude.

---

# 2. Scope and feature priority

| ID | Priority | Feature | Release gate |
|---|---|---|---|
| F01 | P0 | Installable addon; CRM > Smart Chatter Inbox menu and client action | MVP |
| F02 | P0 | List eligible, accessible CRM leads/opportunities in a paginated work queue | MVP |
| F03 | P0 | Search by lead title/customer and filter by owner, state, team, company | MVP |
| F04 | P0 | Set status Needs Action / Waiting / Done / Snoozed | MVP |
| F05 | P0 | Set responsible user, with CRM/team access validation | MVP |
| F06 | P0 | Set/clear snooze-until; overdue snoozed items return to action queue | MVP |
| F07 | P0 | Show lead/contact details and safe message preview or summary if permitted | MVP |
| F08 | P0 | Open underlying lead/opportunity; launch native activity scheduling | MVP |
| F09 | P0 | Robust multi-company, record-rule and message privacy tests | MVP |
| F10 | P1 | Last incoming/customer message indicator, after verifying reliable classification | v1.1 |
| F11 | P1 | Shared team filters, saved filters, keyboard navigation | v1.1 |
| F12 | P1 | SLA timers, response analytics and daily manager overview | v1.1 |
| F13 | P2 | Templates, bulk actions, more model adapters (e.g. Sales Orders) | v2 |
| F14 | Out | Direct email sending, message delete/move/edit, lost message recovery | Not MVP |

**Definition of MVP:** F01–F09 complete, with working end-to-end tests. F07 may initially show an authenticated **CRM record summary** and a button to open its native chatter; richer message preview must be added only when a secure Odoo 19 message-fetch mechanism has been validated.

---

# 3. User roles and actual usage

## 3.1 Roles
- **Salesperson:** Already authorized to view particular CRM leads; sees only permitted records, can update workflow fields where underlying CRM write permission allows.
- **Sales manager:** Can manage visible team work queues *within existing CRM access boundaries*; manager status must **not** grant access to otherwise restricted companies/messages.
- **Odoo administrator:** Installs/configures the addon. Administration of this product must not bypass Odoo message or lead ACLs for ordinary users.

## 3.2 Key scenarios
1. **Morning triage.** Salesperson opens Smart Chatter Inbox → filters My Items / Needs Action → reviews CRM context → opens a lead to reply in native chatter.
2. **Handoff.** Manager (already able to edit relevant lead) sets assignee to a teammate who is eligible to see that lead → sees workflow owner in the queue.
3. **Waiting.** Salesperson sends a quotation in native Odoo workflow, marks lead Waiting. Status is workflow metadata, not a guarantee a message was delivered.
4. **Snooze.** Salesperson sets Snoozed until Friday at 10:00. It is hidden by default from immediate action queue, but visible in a Snoozed filter. Once the timestamp has elapsed, the computed queue state becomes Needs Action. Decide whether to persist the state lazily, or via scheduled cron; document one consistent behavior.
5. **Security.** Salesperson from Company A cannot discover lead or message subject from Company B through list, count, search, group filter, source IDs, or direct RPC.
6. **No history.** A lead with no chatter can appear as a CRM work item only if selected by a documented policy. Default proposal: include leads explicitly assigned a Smart Inbox state, and optionally include eligible active leads by a setting; do not infer 'unanswered' from no messages.

---

# 4. Functional requirements, detailed

## 4.1 Navigation
- CRM application: add a visible menu **Smart Chatter Inbox** for users who have the new inbox group **and** CRM model read rights.
- Selecting opens a dedicated responsive Owl client action, not an embedded website page.
- Optional app icon may come later; no second global root app needed in MVP.

## 4.2 Layout and information architecture
**Desktop:** left filter rail (20%), center paginated list (40%), right details pane (40%). **Tablet/mobile:** collapsible filter rail; list then details; avoid horizontal overflow.

Each queue row displays:
- CRM opportunity/lead title (read from accessible `crm.lead`), customer name (where user can view it), initials/avatar if safe;
- explicit workflow state, owner, team, time last changed; optional last visible message timestamp;
- a compact **Open CRM** action.

Right pane displays:
- record name, partner, CRM stage, salesperson, team;
- workflow status dropdown, assignee selector, snooze date/time;
- **Open in Odoo** action and **Schedule Activity** via standard Odoo action;
- optional latest **authorized** message excerpt after secure integration is proved.

**Do not render customer message HTML as raw unsanitized markup.** Prefer plain text or Odoo's sanitized renderer. Do not expose message body in list snippets unless permissions are independently established.

## 4.3 Search and filters
- Search: text across **lead title and partner display name**; never query unrestricted message bodies in MVP.
- Quick filters: My Queue, Needs Action, Waiting, Done, Snoozed, All Visible.
- Advanced filters: owner, CRM team, company if company is allowed; lead/opportunity; optional selected date ranges.
- All filters combine with the native record-rule-constrained `crm.lead` search. No global count of inaccessible data.
- Pagination: server-side limit 30 by default; deterministic ordering and pagination/cursor strategy; total count is calculated **after** access controls.
- Empty and loading states required. Preserve filters between opening records where reasonable.

## 4.4 Workflow status and ownership
- Status values: `needs_action`, `waiting`, `done`, `snoozed`.
- Default when an eligible lead has never been triaged: **Needs Action** (computed in UI), but do not write fields to all existing leads during install.
- Status changes write to the parent `crm.lead` record via server-side method, respecting access rights, record rules, company and user authorization.
- `snoozed` must include future datetime. Clearing snooze returns to Needs Action (or previously stored state if explicitly designed).
- Ownership defaults to lead salesperson (`user_id`) if custom owner is empty; do not silently change Odoo's `user_id` during inbox assignment.
- Assignee selection cannot elevate user access; validate candidate user eligibility and show a clear warning when record access cannot be ensured. At minimum, constrain options to current team members and explain that visibility is still governed by CRM rules. Do not infer access solely from team membership.
- Assignment/changes are logged through native CRM tracking only if explicitly opted in; avoid repetitive chatter updates.

## 4.5 Message details / reply handling
- MVP uses Odoo **native chatter** for replies, notes, attachments, and scheduling. Clicking Reply/Open navigates to the parent record rather than performing its own `mail.message.create` or `message_post` until thoroughly tested.
- A preview may be shown only after identifying a supported Odoo 19 mail message-fetch API that enforces exact message + parent record read rules. If not verified, ship a **CRM context pane with 'Open Chatter'** and mark message preview as deferred. This is a **nonnegotiable security gate**.
- Do not expose orphaned/lost mail messages or discuss channels; these are outside scope.
- Do not promise email opens or outgoing/incoming classification can be perfect without mail gateway configuration.

## 4.6 Follow-up activities
- Click **Schedule Follow-up** on an item → open Odoo's standard activity composer for that CRM record, rather than inventing a custom email task database.
- Display planned activity count and next deadline only when the user's existing permissions allow it; defer if not secure.
- Preserve Odoo core activity behavior; avoid creating duplicates on repeated UI clicks.

## 4.7 Reliability and UX
- UI notifications for successful changes and actionable errors.
- Disable submit controls during in-flight mutations; no duplicate writes.
- Empty states and onboarding tip for a new database.
- Clear time zone labels; store datetimes UTC using Odoo framework and format user-local times.
- No performance-blocking full-text search, global `mail.message` scans, or unbounded browser datasets.
- Keyboard focus indicators, accessible labels, appropriate contrast, and screen-reader-friendly buttons.

---

# 5. Technical architecture (approved default)

## 5.1 Architectural choice
**MVP is CRM-only and parent-record-first.** Extend `crm.lead` with a small set of workflow fields. Use the existing `crm.lead` model as the query and access-control authority. This avoids a duplicate all-mail index whose ACLs could reveal restricted subjects or messages.

**Backend:** Python Odoo ORM; model extension, safe server methods, standard ACL/record rules.  
**Frontend:** Owl component registered as an Odoo `ir.actions.client` action; Odoo `orm`, `action`, `notification`, `dialog` services; QWeb XML templates, SCSS.  
**Persistent state:** Workflow fields on `crm.lead` only.  
**Messaging:** Native `mail.thread`, mail UI, and activities; secure message preview optional.

### Conceptual data flow
1. User opens client action `sd_smart_chatter_inbox.InboxAction`.
2. Owl calls a **model method on `crm.lead`** (not arbitrary SQL) to list a page.
3. Server composes an allowed CRM search domain and applies native access rules; response contains only safe fields.
4. User selects a row → server fetches authorized CRM details; optionally fetches message preview through a separately proven secure API.
5. User changes status → `crm.lead` write under their own user, with validation.
6. User selects Open Chatter / Schedule Activity → Odoo built-in action.

## 5.2 Proposed field dictionary (extend `crm.lead`)

| Field | Odoo type | Default | Requirements |
|---|---|---|---|
| `sci_state` | Selection | `needs_action` | Options needs_action, waiting, done, snoozed; optional `tracking=False` |
| `sci_owner_id` | Many2one(`res.users`) | False | Workflow owner; fallback to lead `user_id`, not a replacement for it |
| `sci_snooze_until` | Datetime | False | Required for snoozed; user-local input/UTC storage |
| `sci_updated_at` | Datetime | False | Updated only on SCI workflow state change |
| `sci_updated_by_id` | Many2one(`res.users`) | False | Audit metadata; read-only in UI |

**Avoid field name collisions:** before implementation inspect CRM modules and available fields. Prefix custom fields with `sci_`. Odoo already supplies name, partner, stage, company, user, team, dates, and chatter. **Do not create redundant copies of messages or customer data.**

**Snooze expiration:** a computed presentation state `effective_state` may be `needs_action` when `sci_state='snoozed'` and `sci_snooze_until <= now`. If using a saved state instead, add a narrow cron that writes only expired leads in approved companies, after reviewing cron permissions. Choose one route, provide tests, and document status transitions and count filters. MVP preference: computed effective state for reads and UI, plus a bounded cron only if necessary for reliable filtering.

## 5.3 Server API contract (design, names are proposals)
Implement on inherited `crm.lead` only after reviewing exact Odoo 19 ORM signatures:

- `@api.model sci_get_inbox_page(domain_filters: dict, limit: int = 30, offset: int = 0) -> dict`: returns `items`, `total`, `limit`, `offset`, `has_more`; whitelist filter keys and bound `limit <= 100`; never accept arbitrary client-supplied ORM domain or model name.
- `@api.model sci_get_item(lead_id: int) -> dict`: return permitted CRM record detail; use `browse(...).exists()` plus explicit read permission verification and native record rules; do not `sudo()`.
- `sci_update_workflow(lead_id: int, state: str, owner_id: int|None, snooze_until: datetime|None) -> dict`: validate only allowed keys/states, write through authorized `crm.lead`, return safe updated record.
- `@api.model sci_get_allowed_filters() -> dict`: optional values obtained via standard permitted ORM searches, never reveal other companies/teams via global counts.

**Security caution:** Odoo's exact `check_access` and `check_access_rule` APIs can vary by version. Claude must inspect the installed Odoo 19 source and use correct public API. If direct RPC is callable by any logged-in user, the methods must enforce both CRM read/write access and any specific module group on the server. Do not rely on a hidden menu or frontend-only conditions.

### Example response structure (illustrative, not a guaranteed Odoo API)
```json
{
  "items": [
    {
      "lead_id": 42,
      "name": "Website redesign request",
      "partner_name": "Example Co",
      "stage_name": "Qualified",
      "state": "needs_action",
      "effective_state": "needs_action",
      "owner_name": "Salesperson",
      "company_name": "Company A",
      "updated_at": "2026-10-29 08:10:00"
    }
  ],
  "total": 1,
  "limit": 30,
  "offset": 0,
  "has_more": false
}
```
This example uses fictitious customers and IDs. Never expose `mail.message` objects wholesale or raw unfiltered HTML.

## 5.4 Suggested addon structure
```text
sd_smart_chatter_inbox/
├── __init__.py
├── __manifest__.py
├── README.md
├── LICENSE
├── models/
│   ├── __init__.py
│   └── crm_lead.py
├── security/
│   ├── security_groups.xml
│   └── ir.model.access.csv                # only if a new real model requires it
├── views/
│   ├── crm_inbox_menu.xml
│   ├── crm_inbox_actions.xml
│   └── crm_lead_extension_views.xml       # optional concise workflow fields
├── static/
│   ├── description/
│   │   ├── icon.png
│   │   └── index.html                     # marketplace description later
│   └── src/
│       ├── js/inbox_action.js
│       ├── js/inbox_api.js
│       ├── xml/inbox_action.xml
│       └── scss/inbox.scss
├── tests/
│   ├── __init__.py
│   ├── test_inbox_workflow.py
│   ├── test_inbox_security.py
│   └── test_inbox_filters.py
└── doc/
    ├── USER_GUIDE.md
    ├── SECURITY_NOTES.md
    └── COMPATIBILITY.md
```
**Important:** Avoid creating an `ir.model.access.csv` that grants broader ACLs to existing `crm.lead` or `mail.message`. A client action and a model extension normally do not need a new ACL on `crm.lead`. If a separate model is introduced later, define a specific least-privilege ACL and record rules.

## 5.5 Manifest design guidance
```python
{
    "name": "Smart Chatter Inbox Pro",
    "version": "19.0.1.0.0",
    "summary": "Actionable CRM follow-up queue for Odoo chatter",
    "category": "Sales/CRM",
    "author": "Softdeviser",
    "license": "OPL-1",
    "depends": ["base", "web", "mail", "crm"],
    "data": [
        "security/security_groups.xml",
        "views/crm_inbox_actions.xml",
        "views/crm_inbox_menu.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "sd_smart_chatter_inbox/static/src/js/**/*.js",
            "sd_smart_chatter_inbox/static/src/xml/**/*.xml",
            "sd_smart_chatter_inbox/static/src/scss/**/*.scss"
        ]
    },
    "application": False,
    "installable": True
}
```
The snippet is a draft: implement proper manifest order (groups before menus), avoid missing references, and validate loading on a clean Odoo 19 server. Asset globs and exact imports must be tested against installed version.

## 5.6 Frontend Owl component design
- `InboxAction` root: owns filter state, current page, selected lead ID, loading/error states.
- `InboxFilters`: quick filters and search with debouncing.
- `InboxList`: paginated list, keyboard-selectable rows, badges.
- `InboxDetail`: lead context, workflow form, Open Chatter / Schedule Activity actions.
- `InboxEmpty`: zero items / no permissions / error state.
- `inbox_api.js`: typed-ish adaptor for Odoo `orm` calls, consistent response validation.
- Use `registry.category('actions').add('sd_smart_chatter_inbox.InboxAction', InboxAction)` after matching `ir.actions.client` tag.
- Prefer standard components and Owl events over direct DOM mutation; clean up event handlers and avoid global state leaks.
- Keep most business logic in server model methods, **not** JavaScript.
- Use stable XML template names under `sd_smart_chatter_inbox.*` and accessible input labels.

---

# 6. Security and privacy: release-blocking requirements

## 6.1 Threat model
Untrusted authenticated internal users may call backend methods directly, forge lead IDs, pass arbitrary filters, change ownership, or attempt to retrieve another company's lead through result counts, search snippets, attachment URLs, and deep links. Treat client-side UI state as untrusted.

## 6.2 Rules to implement
1. **Never sudo user-facing searches/reads** of CRM leads, messages, or attachment bodies. If privileged maintenance code is unavoidable later, segregate it from response-building and document its proof of safety.
2. **Parent-first access:** discover records through `crm.lead.search()`/`search_read()` under normal user context and record rules, then fetch permitted related content.
3. Verify actual record read rights before returning detail and write rights before changing workflow fields; verify any new SCI group condition server-side.
4. **No arbitrary RPC fields**: whitelist filters, requested IDs, user actions, and update keys. Limit page size and max search length.
5. Never allow arbitrary `res_model`, `res_id`, or raw SQL from RPC arguments.
6. **Multi-company:** respect `allowed_company_ids`, record rules and user permissions; never set `allowed_company_ids` from untrusted input.
7. **Message previews:** only after proof that chosen native 19.0 mail fetch method filters per-message visibility and parent record visibility. Notes, private channels and inaccessible attachments must remain hidden.
8. Messages, email addresses and business data must not be sent to third-party analytics or cloud services.
9. No rendering untrusted raw HTML or markdown-as-HTML. Escape text by default; use Odoo-supported sanitization if HTML rendering is essential.
10. Follow-up owner/team access must not grant additional CRM rights. A manager can see only what Odoo grants that manager.
11. Safe error messages: deny unauthorized requests without echoing sensitive record names or content; log minimal audit information.
12. Never modify/deactivate Odoo native `mail.message` record rules and do not broaden native group permissions.

## 6.3 Security test matrix (mandatory)
| Test | Scenario | Expected |
|---|---|---|
| SEC-01 | User A asks for Company B lead via item detail RPC | Access denied; no title, owner, or message leaked |
| SEC-02 | User A requests another user's restricted lead with ID | No detail and no status mutation |
| SEC-03 | User A uses crafted `company_id` or generic domain in list filters | Rejected or ignored; no broadened results/counts |
| SEC-04 | Authorized read-only user attempts SCI status write | Denied (or interface shows readonly) |
| SEC-05 | Portal/public user calls endpoint directly | No access |
| SEC-06 | User lacks SCI group but has CRM rights | Direct SCI RPC rejected if product access is group-restricted |
| SEC-07 | Lead visible, one message private/restricted | Restricted message/body/attachment absent from response |
| SEC-08 | Manager from Company A queries Company B | No cross-company leakage unless native ACL grants it |
| SEC-09 | Malicious HTML in lead/message text | UI displays escaped/sanitized text, no script execution |
| SEC-10 | Invalid owner / status / 100000-item request | Validation error or capped page, no privilege escalation |

**Acceptance rule:** If any SEC-01 through SEC-10 fails, the product is **not** production-ready even if the interface looks complete.

---

# 7. Interaction details and screen states

## 7.1 Primary screens
1. **Main inbox:** heading, search input, quick-filter tabs, list, detail panel.
2. **Lead summary:** lead title, partner, stage, owner, status, snooze, latest permitted details, Open CRM.
3. **Snooze editor:** calendar and time with timezone hint; clear option.
4. **Permission denied:** neutral message ('You no longer have access to this CRM record.') with back to inbox.
5. **Empty state:** 'No leads match these filters' and a reset control.

## 7.2 Explicit user-facing labels
- **Needs Action**: Team follow-up pending; a manual workflow state, not proof email was unread.
- **Waiting**: A response is expected from customer/third party.
- **Done**: No immediate follow-up needed.
- **Snoozed**: Hidden from Needs Action until selected date/time.
- **Open Chatter**: Opens CRM record so user can use native Odoo messaging.

## 7.3 Responsive design
- Width >= 1100px: 3-pane layout.
- Width 720–1099px: compact list and detail; filters in drawer.
- Width < 720px: list / detail stacked navigation, sticky top search, accessible controls.
- Avoid copying competitor screenshots/UI; create a clean, original visual system.

---

# 8. Acceptance criteria / executable behavior

### AC-01 Installation
**Given** a clean Odoo 19 Community instance with CRM installed, **when** the addon is installed from Apps, **then** no dependency, XML, JS bundle, or security load error occurs and the CRM menu appears to authorized users.

### AC-02 Accessible list
**Given** Company A salesperson with access to leads L1 and L2 but not L3, **when** they open the inbox, **then** they see only permitted leads and the total count excludes L3.

### AC-03 State transitions
**Given** a permitted lead, **when** the salesperson marks it Waiting and then Done, **then** state persists after refresh and filtering reflects the new value.

### AC-04 Snooze
**Given** a lead in Needs Action, **when** the salesperson snoozes it until a future datetime, **then** it leaves the immediate Needs Action filter and appears under Snoozed; after expiry it appears in Needs Action again per documented implementation.

### AC-05 Ownership
**Given** a visible CRM lead, **when** an authorized user assigns a valid teammate as inbox owner, **then** owner persists but no hidden CRM sharing or direct mail message grants are created.

### AC-06 Native chatter
**Given** an inbox item, **when** the user clicks Open Chatter, **then** Odoo navigates to the correct CRM lead record and the ordinary chatter functions remain available.

### AC-07 Security
**Given** an unauthorized lead ID, **when** it is passed to a direct RPC, **then** the result is access denied or not found, with no sensitive fields returned.

### AC-08 Large dataset
**Given** 10,000 leads and 100,000 messages in benchmark database, **when** the user opens default page, **then** API returns a bounded page rather than all records; record timings and database query counts and address N+1 patterns.

### AC-09 Upgrade
**Given** existing workflow statuses, **when** the module upgrades from 19.0.1.0.0 to a patch release, **then** statuses and snooze metadata remain intact.

### AC-10 No false unread claims
**Given** a message without reliable recipient/direction metadata, **when** shown in MVP, **then** UI does not claim it is unread, unanswered, or externally received based on guesswork.

---

# 9. Automated testing, QA and quality gates

## 9.1 Python / ORM test suite
Use Odoo 19-compatible transaction tests (`TransactionCase`/`SavepointCase` as available in source). Include fixtures for two companies, three users (manager, salesperson, restricted), two teams, CRM leads in each company, and public/private messages when appropriate.

- `test_install_and_action_visible_to_authorized_group`
- `test_status_transitions_and_invalid_state_rejected`
- `test_snooze_future_validation_and_expiry`
- `test_user_cannot_read_other_company_lead`
- `test_user_cannot_change_other_team_restricted_lead`
- `test_count_does_not_expose_inaccessible_leads`
- `test_untrusted_filters_do_not_enable_domain_injection`
- `test_owner_change_does_not_change_crm_user_id`
- `test_read_only_user_cannot_write_workflow`
- `test_search_order_and_pagination_stable`
- `test_preview_only_if_secure_api_confirmed`

## 9.2 Frontend tests
Use the test framework shipping with Odoo 19 (Hoot/unit tests and a browser tour where available). Test first load, filter selection, pagination, load failure, state update, snooze form, malformed response, keyboard focus, and Open CRM action.

## 9.3 Manual QA
- Odoo 19 Community and Enterprise, clean install/upgrade/uninstall.
- Chrome and Firefox latest stable desktop; at least one modern mobile viewport.
- Multi-company switch and user permission change while interface remains open.
- A lead deleted after it was selected; stale status update conflict; session expiration.
- Unicode customer names, long subject lines, zero messages, dates near timezone boundaries, untrusted HTML.
- No dependency on paid Enterprise-only code for Community baseline.

## 9.4 Performance budgets (targets, not promises)
- Page size 30, max 100; no unbounded fetch of all `mail.message` records.
- Initial list server processing target <= 700 ms p95 in reference benchmark; interactive visible UI <= 2 s p95. Set up benchmark and report real measurements.
- Search must use bounded ORM queries, prefetch relations, and avoid N+1 chatter lookups.
- If preview is slow, load it separately on row selection, not with whole list.

## 9.5 Release blockers
No release with security failure, install error, data loss on update, uncaught Owl exception on main workflow, or missing permissions tests. A visual screenshot or code generation alone does not count as testing.

---

# 10. Development milestones and Claude execution plan

| Phase | Estimated effort* | Claude's deliverable | Gate |
|---|---|---|---|
| 0. Environment and source audit | 0.5–1 day | Verify exact Odoo 19 APIs, repository layout, DB and `mail` internals; create compatibility notes | Evidence from real repo |
| 1. Installable shell | 1–2 days | Manifest, menu, action, Owl hello-world/empty UI, basic group | Clean install + UI renders |
| 2. CRM workflow fields | 2–4 days | `crm.lead` extension, workflow transitions, server tests | ORM tests pass |
| 3. Secure queue API | 4–6 days | Scoped pagination, filters, detail, security tests | SEC matrix passes |
| 4. OWL interface | 5–9 days | Responsive queue, filters, details, status/assignee/snooze | Browser workflow works |
| 5. Native chatter & activity handoff | 1–3 days | Open CRM, Schedule Activity, secure preview only if justified | Correct record action |
| 6. Hardening & publishing | 4–6 days | Full automated tests, docs, screenshots, manifest/branding, demo | Release checklist complete |

*Planning estimates for an **experienced Odoo engineer** with access to a functional development environment; not a guaranteed calendar schedule. Parallel work and new Odoo learning can shift the total. Estimated MVP: **4–7 weeks**.

## 10.1 Claude working agreement
- Work directly inside the repository. Do not present pseudo-code as complete implementation.
- If no repository or Odoo 19 server exists, build module files in a clean directory and **clearly state tests could not be run**, along with exact commands needed.
- Before coding each phase, inspect relevant Odoo 19 code and explain any deviations in ≤10 lines.
- After each phase, run available tests, include commands and actual output, identify blockers, and commit in logical increments if Git is available.
- Do not replace the architecture with a full mail-message index without approval; security risk is materially higher.
- Never claim 'passing' based solely on reading code; distinguish generated, linted, installed, UI tested, and production validated.
- Do not use or reproduce paid competitor source code, screenshots, or text.

## 10.2 Required phase reports
For each phase Claude must return:
1. What was implemented (feature IDs).
2. Which files changed.
3. Commands executed and test results (pass/fail/blocked, with accurate counts).
4. Security implications and any deviations from specification.
5. What's next and any environment blocker preventing progress.

---

# 11. Development environment and commands

## 11.1 Reference environment
- Odoo core and addons source: **19.0 branch** checked out.
- PostgreSQL database and an Odoo system user.
- Python interpreter/dependencies matching Odoo 19 requirements.
- Editable `addons_path` including `sd_smart_chatter_inbox` parent folder.
- Chrome/Chromium for optional UI tour tests.

## 11.2 Sample commands (adapt to local setup)
```bash
# Module install and server-side tests; update paths, ports and DB role as needed
./odoo-bin -d sci_test -i sd_smart_chatter_inbox \
  --addons-path=addons,/path/to/custom-addons \
  --test-enable --stop-after-init --log-level=test

# Module upgrade/regression
./odoo-bin -d sci_test -u sd_smart_chatter_inbox \
  --addons-path=addons,/path/to/custom-addons \
  --test-enable --stop-after-init --log-level=test

# Interactive local test
./odoo-bin -d sci_test \
  --addons-path=addons,/path/to/custom-addons \
  --dev=assets
```
**Important:** These commands are illustrative. Claude must check Odoo 19 CLI flags and shell paths in the installed environment and not invent success results.

## 11.3 Minimum demo data
- Company A and Company B.
- Sales manager A, salesperson A, salesperson B.
- 6 leads (including one hidden by record rules) and mixed notes/messages on visible leads.
- Workflow statuses in all four states; two dates (future/past snoozes).
- A contact with long Unicode name and a record with potential HTML/script-like input to test escaping.

---

# 12. Marketplace packaging and go-to-market

## 12.1 Listing copy (draft, not final)
**Title:** Smart Chatter Inbox Pro – CRM Follow-up & Team Inbox  
**Subtitle:** Keep every Odoo CRM conversation organized, assigned and actionable.

**Proof-driven benefits:**
- All your accessible CRM lead follow-ups in one workspace.
- Track Needs Action, Waiting, Done and Snoozed.
- Assign responsibility without changing CRM salesperson ownership.
- Open the original lead and use native Odoo Chatter.
- Respect existing multi-company record access.

Avoid claims of universal email inbox sync, perfect 'unread' detection, zero missed messages, or cross-app support that is not implemented.

## 12.2 Screenshots to capture after development
1. Three-pane inbox on desktop with sample data.
2. Needs Action and Waiting filters.
3. Snooze date/time editor.
4. Lead detail and Open Chatter integration.
5. Responsive mobile list/details.

## 12.3 Store release checklist
- Correct technical module name and `19.0.x` version.
- Verified install on supported Odoo edition(s) and explicit hosting requirements.
- `__manifest__.py` metadata, license and author details.
- No proprietary competitor code or unauthorized brand assets.
- English README, feature list, screenshots, 1–2 minute product demo, change log.
- Support email/contact, refund/support policy, known limitations and compatibility matrix.
- Clean zip archive: exactly one valid addon root folder (no build caches, database dumps, credentials).
- No telemetry without clear disclosure and consent.
- Upgrade migration test and database backup recommendations.

---

# 13. Risk register and design decisions

| Risk | Severity | Mitigation |
|---|---|---|
| Leaking restricted chatter/messages | Critical | Parent-first access; native Odoo message APIs; dedicated security tests; preview is optional |
| Existing Odoo Discuss overlaps with concept | High | Position as CRM responsibility/status queue; demonstrate different workflow |
| Odoo 19 mail APIs changed | High | Inspect 19.0 source before use, no guessing private methods |
| Assigned owner can't access underlying lead | Medium–high | Validate and communicate; never grant access automatically |
| Slow list queries on large databases | Medium | Paginate, filter server-side, avoid N+1 and global mail scans |
| Snooze inconsistent with filters | Medium | Explicit expiration semantics + tests |
| Enterprise/Community differences | Medium | Test baseline on Community; optional Enterprise test |
| Marketplace price undercutting | Medium | Focus on demonstrated workflow value, support, usable UX |
| Feature creep into generic email client | High | Keep F14 out of MVP and gate extra scope |

## 13.1 Decisions already made
- **D1:** Begin with CRM lead/opportunity chatter, not all Odoo messages.
- **D2:** Reuse native messaging and activities; do not build an email transport system.
- **D3:** Store workflow state on `crm.lead` to inherit core record-level security.
- **D4:** Default no unrestricted message preview until separately validated.
- **D5:** Target Odoo 19, Community-first, support Enterprise where tested.
- **D6:** Single commercial paid module at initial launch; free tier later only after validation.

## 13.2 Open questions Claude should resolve autonomously
1. Which exact Odoo 19 supported API opens a CRM lead form while preserving navigation context?
2. Which native activity scheduling action is safest/least brittle?
3. Which message-fetch API, if any, provides security-checked excerpts for a lead? If ambiguous, **omit preview**.
4. How does the chosen Odoo 19 ORM treat specific access-check APIs and `check_company` for these fields?
5. Is a cron needed for snooze, or can effective-state filtering be expressed efficiently and correctly with a search domain?
6. Which manifest/asset conventions apply to the exact Odoo checkout?
7. Which CRM security group and optional SCI menu group best supports least privilege without interfering with existing CRM role groups?

Document answers in `doc/COMPATIBILITY.md`; do not block basic installable shell on noncritical uncertain features.

---

# 14. Sources and verification links

Accessed for planning on **29 October 2026**. Review against the installed 19.0 branch before implementation.

1. [Odoo 19 - Developer Security: ACLs and record rules](https://www.odoo.com/documentation/19.0/developer/reference/backend/security.html)
2. [Odoo 19 - Backend Framework Overview (Owl and services)](https://www.odoo.com/documentation/19.0/developer/reference/frontend/framework_overview.html)
3. [Odoo 19 - Frontend Services](https://www.odoo.com/documentation/19.0/developer/reference/frontend/services.html)
4. [Odoo 19 - Create a Client Action](https://www.odoo.com/documentation/19.0/developer/howtos/javascript_client_action.html)
5. [Odoo 19 - Module Manifests](https://www.odoo.com/documentation/19.0/developer/reference/backend/module.html)
6. [Odoo 19 - Testing Odoo](https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html)
7. [Odoo 19 - Chatter and scheduled activities](https://www.odoo.com/documentation/19.0/applications/productivity/discuss/chatter.html)
8. [Odoo 19 - Discuss (native inbox)](https://www.odoo.com/documentation/19.0/applications/productivity/discuss.html)
9. [Odoo 19 - CRM Activities](https://www.odoo.com/documentation/19.0/applications/sales/crm/optimize/utilize_activities.html)
10. [Competitor: Mail Messages Easy Pro](https://apps.odoo.com/apps/modules/19.0/prt_mail_messages_pro)

---

# 15. Definition of done and final deliverables

**Claude's final implementation deliverable must contain:**
- A complete installable `sd_smart_chatter_inbox` module source tree.
- Installation, upgrade and uninstall steps and tested edition matrix.
- Functional CRM workflow UI; status, snooze, owner, search/filters, native chatter/activities navigation.
- Server and UI test code, actual commands run and their results; explicit untested items.
- Multi-company and privilege-escalation security tests with evidence.
- README, user guide, version/changelog, screenshots and clean app ZIP.
- No dependence on paid competitor source, no data leaks, and no claims of features not actually built.

**Immediate starting action:** Execute the instructions in `CLAUDE_START_HERE.md`, start Phase 0 source audit and Phase 1 installable shell, and return actual files and test results—not another planning document.
