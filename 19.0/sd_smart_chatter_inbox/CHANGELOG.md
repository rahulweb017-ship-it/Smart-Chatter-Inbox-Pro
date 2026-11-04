# Changelog

## 19.0.1.0.0 (2026-11-05)

First release.

- CRM > Sales > Smart Chatter Inbox: a follow-up queue for CRM leads and opportunities.
- Workflow states Needs Action, Waiting, Done and Snoozed, stored on the lead (`sci_*` fields).
- Inbox owner that never changes the salesperson and never grants access.
- Snooze with automatic return to Needs Action when the date passes (computed, no cron).
- Search by lead title or customer. Filters: My Queue, status, owner, sales team, company and type.
- Open Chatter and Schedule Follow-up use Odoo's native lead form and activity wizard.
- Smart Inbox tab on the lead form and an "Include untriaged leads" setting in CRM Settings.
- Server-side security: no sudo on user data, product-group check on every call, whitelisted filters, capped pages.
- Tests: 29 Python (workflow, filters, the SEC-01 to SEC-10 security matrix, SCSS compile check), 10 Hoot unit tests, and a browser tour that covers save, filters, HTML escaping, the activity dialog and Open Chatter.
