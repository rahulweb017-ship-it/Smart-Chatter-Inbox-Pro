# Changelog

## 18.0.1.1.0 (2026-11-21)

- Reply detection: a customer email or message moves the lead to Needs Action and marks it "Customer replied"; a team reply from the chatter moves Needs Action to Waiting. Notes, automated messages, mass mailings and OdooBot are ignored.
- New "Unanswered" quick filter, "Customer replied" chip with age, and last customer message / last team reply dates in the details pane and on the lead form.
- Store listing renamed to "CRM Follow Up Inbox | Unanswered Leads, Reminder & Snooze", with a new reply-detection demo and re-recorded GIFs and screenshots.
- New setting "Detect customer replies automatically" (on by default). Existing leads and old messages are not changed on upgrade.
- Tests: 14 reply-detection tests through the real mail gateway, 2 more Hoot tests and a tour step.

## 18.0.1.0.0 (2026-11-21)

First release for Odoo 18, ported from 19.0.1.0.0 with the same features and tests.

- CRM > Sales > Smart Chatter Inbox: a follow-up queue for CRM leads and opportunities.
- Workflow states Needs Action, Waiting, Done and Snoozed, stored on the lead (`sci_*` fields).
- Inbox owner that never changes the salesperson and never grants access.
- Snooze with automatic return to Needs Action when the date passes (computed, no cron).
- Search by lead title or customer. Filters: My Queue, status, owner, sales team, company and type.
- Open Chatter and Schedule Follow-up use Odoo's native lead form and activity wizard.
- Smart Inbox tab on the lead form and an "Include untriaged leads" setting in CRM Settings.
- Server-side security: no sudo on user data, product-group check on every call, whitelisted filters, capped pages.
- Tests: 29 Python (workflow, filters, the SEC-01 to SEC-10 security matrix, SCSS compile check), 10 Hoot unit tests, and a browser tour that covers save, filters, HTML escaping, the activity dialog and Open Chatter.
