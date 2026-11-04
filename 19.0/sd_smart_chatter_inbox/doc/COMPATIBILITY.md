# Compatibility notes: Odoo 19.0

These notes were checked against Odoo `19.0+e-20260605`, installed at `C:\Program Files\Odoo 19.0e.20260605\server`.

| Topic | Odoo 19 fact | How the module uses it |
|---|---|---|
| Access checks | `check_access(op)`, `has_access(op)` and `_filtered_access(op)` in `odoo/orm/models.py`. `check_access_rights` and `check_access_rule` are deprecated. | `has_access` gates every lead. `_filtered_access` batches the names of related records. |
| RPC exposure | `odoo/service/model.py::get_public_method` refuses names that start with `_`. | Helpers are named `_sci_*`. A test checks they cannot be called over RPC. |
| Groups | `res.groups.privilege` (`category_id`) together with `res.groups.privilege_id` and `user_ids`. Users have `group_ids` and `has_group(xmlid)`. | Adds the privilege "Smart Chatter Inbox" and the group `group_sci_user`. |
| Client actions | `ir.actions.client` has **no** `group_ids` field. | Access is enforced by the menu group and by a server check in every method. |
| CRM rules | `crm_rule_personal_lead`, `crm_rule_all_lead` and the global `crm_lead_company_rule`. | Not changed. Everything is read through them. |
| Domains | `odoo.fields.Domain` (the `expression()` helper is deprecated). | Filters are built with `Domain`. |
| Activity dialog | Wizard model `mail.activity.schedule`, opened the same way as `store.scheduleActivity()` in `mail/static/src/core/web/store_service_patch.js`. | **Schedule Follow-up** opens this wizard. |
| Open record | `action.doAction({type: 'ir.actions.act_window', res_model, res_id, views: [[false, 'form']]})` | **Open Chatter**. |
| Frontend | Owl 2 with `useState` and `static props`. No `@odoo-module` header. | `inbox_action.js`. |
| Tests | `TransactionCase`, `HttpCase.start_tour`, `browser_js` and `new_test_user`. `SavepointCase` is gone. Hoot tests go in `web.assets_unit_tests`. | `tests/` and `static/tests/`. |
| Views | Lead form anchor `//page[@name='internal_notes']`. Settings anchor `//app[@name='crm']`. | The same anchors exist in 20.0. |

## Answers to the spec's open questions (§13.2)
1. **Opening a lead:** with a standard `act_window` action (`doAction`), which keeps the breadcrumbs.
2. **Scheduling an activity:** with the `mail.activity.schedule` wizard, which is the same one the chatter uses.
3. **Message preview:** not shipped. `mail.message._message_fetch` does check each message, but internal users can see internal notes, so a preview needs a separate review first (`SECURITY_NOTES.md`).
4. **Access checks:** `has_access` and `check_access`. The `sci_*` fields hold no company data, so `check_company` is not needed.
5. **Snooze:** no cron. The expiry is part of the search domain, so filters and counts are always exact.
6. **Manifest and assets:** globs in `web.assets_backend`, `web.assets_unit_tests` and `web.assets_tests`. All checked on a fresh database.
7. **Groups:** one optional product group. It implies nothing, so it never widens CRM rights.

## Snooze rules
- Needs Action = no status, or `needs_action`, or `snoozed` with `sci_snooze_until <= now`.
- Snoozed = `snoozed` with `sci_snooze_until > now`.
- When a snooze expires, nothing is written to the database.
