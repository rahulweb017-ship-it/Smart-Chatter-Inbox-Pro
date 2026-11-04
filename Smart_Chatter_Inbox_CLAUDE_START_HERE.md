# CLAUDE: START BUILDING THIS ODOO APP

You are the lead Odoo 19 developer. Your task is to **implement** the paid Odoo app specified in `Smart_Chatter_Inbox_Pro_Build_Spec.md`, not to write another product strategy.

## Product and environment
- Name: **Smart Chatter Inbox Pro**
- Addon technical name: `sd_smart_chatter_inbox`
- Target: **Odoo 19.0**, Community-first and Enterprise where tested
- Purpose: A CRM-focused sales conversation follow-up queue: Needs Action, Waiting, Done, Snoozed; owner; secure filtering; open original chatter; native activity scheduling.
- Owner: Softdeviser
- MVP must not attempt universal inbox sync, arbitrary mail.message access, or a full email client.

## Nonnegotiable rules
1. FIRST read the entire build spec. Inspect the actual Odoo **19.0 source tree** before assuming model methods or JS imports exist.
2. NEVER use `sudo()` to return user-facing CRM, message or attachment data. Preserve native CRM ACL, record-rule and multi-company restrictions.
3. Only return CRM leads/messages the requesting user is allowed to read. Do not implement global mail search or orphan message recovery.
4. Deliver actual, self-contained addon files inside a proper Odoo addon directory. No placeholder-only implementation.
5. Run real tests when an Odoo server/DB is present. If none exists, be explicit that tests weren't run and provide exact commands; do not invent passing results.
6. Do not copy source/assets/descriptions of any paid competitor.
7. Choose maintainable documented Odoo extension points; do not edit core Odoo files.
8. Build in phases; give a file and test report for each phase, then continue to the next unless environment truly blocks further work.

## Required execution order
**Phase 0 — Source audit:** locate the 19.0 Odoo installation or source, verify CRM lead fields, ACL patterns, OWL client actions, and standard chatter/action APIs. Save concise findings in `doc/COMPATIBILITY.md`.

**Phase 1 — Installable shell:** implement `__manifest__.py`, init files, security group, CRM menu, client action registration and a working Owl screen. Verify clean install.

**Phase 2 — Secure backend:** extend `crm.lead` with custom `sci_` workflow fields; build validated, paginated server methods; write tests including role/multi-company isolation.

**Phase 3 — Working UI:** list/filters/detail; status updates, owner, snooze; loading/empty/error states; navigate to native CRM chatter and schedule activity.

**Phase 4 — Tests and release:** automated Python and browser tests where available; security scenarios, README, changelog, clean ZIP and installation notes.

Only add a latest-message excerpt after confirming a version-correct **security-checked** message-read API. Otherwise show CRM context and Open Chatter.

## First response I expect
- `Odoo source/environment audit` with exact paths and any blockers
- Source tree/phase-1 files created
- Commands actually run and test outcome
- Next phase to implement

**Now start implementation. Do not ask me for more product decisions already covered by the specification.**
