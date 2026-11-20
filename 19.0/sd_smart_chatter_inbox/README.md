# CRM Follow Up Inbox (Smart Chatter Inbox Pro, Odoo 19.0)

A CRM follow-up queue. Each lead or opportunity gets a follow-up status (**Needs Action**, **Waiting**, **Done**, **Snoozed**) and an owner, so your team can see what needs a reply. Replies, notes and activities still happen in Odoo's own chatter.

- Technical name: `sd_smart_chatter_inbox`
- Version: 19.0.1.1.0
- Depends on: `crm`, `mail`, `web`
- License: OPL-1. Author: Softdeviser.

## Features
- **Queue screen:** CRM > Sales > Smart Chatter Inbox. Filters on the left, the list in the middle, lead details on the right. On a phone, the list and details stack.
- **Reply detection:** a customer email or message moves the lead to Needs Action and marks it **Customer replied**. A reply from your team (Send message) moves it from Needs Action to Waiting. Internal notes, automated messages and mass mailings are ignored. You can turn this off in CRM Settings.
- **Quick filters:** My Queue, Needs Action, Unanswered, Waiting, Snoozed, Done, All Visible.
- **More filters:** owner, sales team, company and type, plus search by lead title or customer.
- **Owner:** a follow-up owner per lead. It never changes the salesperson and never shares the lead.
- **Snooze:** pick a date and time. The lead comes back to Needs Action when that time passes.
- **Native Odoo actions:** **Open Chatter** opens the lead form, and **Schedule Follow-up** opens Odoo's standard activity wizard.
- **Smart Inbox tab** on the lead form.
- **Respects Odoo's access rules:** sales rules, record rules and multi-company rules all apply.

## Installation
1. Copy `sd_smart_chatter_inbox` into a folder on your `addons_path`.
2. Update the Apps list and install **CRM Follow Up Inbox | Unanswered Leads, Reminder & Snooze** (technical name `sd_smart_chatter_inbox`).
3. Give users the group **Smart Chatter Inbox / User** (Settings > Users > Access Rights > Sales section). The administrator gets it on install.
4. Optional: CRM > Configuration > Settings > **Include untriaged leads**. **Detect customer replies automatically** is on by default; it only reacts to messages posted after install.

Works on Odoo.sh and self-hosted Odoo 19 (Community or Enterprise). Odoo Online (SaaS) cannot install custom Python apps.

## Upgrade and uninstall
- **Upgrade:** `odoo-bin -u sd_smart_chatter_inbox -d <db>`. Statuses, owners and snoozes are kept. Upgrading to 1.1 does not scan old messages: reply detection starts with the next message.
- **Uninstall:** from Apps. This removes the `sci_*` columns from `crm.lead`. No other data changes.

## Running the tests
```
odoo-bin -c odoo.conf -d <test_db> --addons-path=<odoo>/addons,<parent of this folder> \
  -i sd_smart_chatter_inbox --test-enable --test-tags /sd_smart_chatter_inbox --stop-after-init
```
The browser tour and the Hoot unit tests need Chrome or Chromium.

## Tested
- Automated: 43 Python tests (including the SEC-01 to SEC-10 security matrix and reply detection through the real mail gateway), 12 browser unit tests and a browser tour.
- Browsers: Chrome and Firefox, at desktop and phone sizes.
- Speed: 10,000 leads and 100,000 messages, with p95 under 100 ms per call (`doc/BENCHMARK.md`).

## Known limitations
- No message preview in this release. The details pane shows lead information and an **Open Chatter** button (see `doc/SECURITY_NOTES.md`).
- Reply detection works from who wrote the last message on the lead. It does not track whether an email was opened or read.
- On Odoo 19, out-of-office auto-replies are recognised by Odoo and ignored. Other automatic replies from the customer's mail server may still count as a customer message.
- The queue covers CRM leads and opportunities only.

## Support
rahul@softdeviser.com · https://softdeviser.com
