# Smart Chatter Inbox Pro (Odoo 20.0)

A CRM follow-up queue. Each lead or opportunity gets a follow-up status (**Needs Action**, **Waiting**, **Done**, **Snoozed**) and an owner, so your team can see what needs a reply. Replies, notes and activities still happen in Odoo's own chatter.

- Technical name: `sd_smart_chatter_inbox`
- Version: 20.0.1.0.0
- Depends on: `crm`, `mail`, `web`
- License: OPL-1. Author: Softdeviser.

## Features
- **Queue screen:** CRM > Sales > Smart Chatter Inbox. Filters on the left, the list in the middle, lead details on the right. On a phone, the list and details stack.
- **Quick filters:** My Queue, Needs Action, Waiting, Snoozed, Done, All Visible.
- **More filters:** owner, sales team, company and type, plus search by lead title or customer.
- **Owner:** a follow-up owner per lead. It never changes the salesperson and never shares the lead.
- **Snooze:** pick a date and time. The lead comes back to Needs Action when that time passes.
- **Native Odoo actions:** **Open Chatter** opens the lead form, and **Schedule Follow-up** opens Odoo's standard activity wizard.
- **Smart Inbox tab** on the lead form.
- **Respects Odoo's access rules:** sales rules, record rules and multi-company rules all apply.

## Installation
1. Copy `sd_smart_chatter_inbox` into a folder on your `addons_path`.
2. Update the Apps list and install **Smart Chatter Inbox Pro**.
3. Give users the group **Smart Chatter Inbox / User** (Settings > Users > Access Rights > Sales section). The administrator gets it on install.
4. Optional: CRM > Configuration > Settings > **Include untriaged leads**.

Works on Odoo.sh and self-hosted Odoo 20 (Community or Enterprise). Odoo Online (SaaS) cannot install custom Python apps.

## Upgrade and uninstall
- **Upgrade:** `odoo-bin -u sd_smart_chatter_inbox -d <db>`. Statuses, owners and snoozes are kept.
- **Uninstall:** from Apps. This removes the `sci_*` columns from `crm.lead`. No other data changes.

## Running the tests
```
odoo-bin -c odoo.conf -d <test_db> --addons-path=<odoo>/addons,<parent of this folder> \
  -i sd_smart_chatter_inbox --test-enable --test-tags /sd_smart_chatter_inbox --stop-after-init
```
The browser tour and the Hoot unit tests need Chrome or Chromium.

## Known limitations
- No message preview in this release. The details pane shows lead information and an **Open Chatter** button (see `doc/SECURITY_NOTES.md`).
- The statuses are a manual workflow. They do not detect unread or unanswered emails.
- The queue covers CRM leads and opportunities only.

## Support
rahul@softdeviser.com · https://softdeviser.com
