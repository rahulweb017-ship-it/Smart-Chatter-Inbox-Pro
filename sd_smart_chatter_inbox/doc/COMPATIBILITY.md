# Compatibility notes: Odoo 18.0

These notes were checked against the Odoo 18.0 source at commit `98e48692` (2026-10-23), in `C:\projects\odoo-src\18.0`. The 18.0 build was ported from 19.0. Only the rows marked **differs** changed.

| Topic | Odoo 18 fact | How the module uses it |
|---|---|---|
| Access checks | `check_access(op)`, `has_access(op)` and `_filtered_access(op)` exist in `odoo/models.py`, as in 19. | Same code as 19. |
| RPC exposure | Methods whose names start with `_` cannot be called over RPC. | Helpers are named `_sci_*`. A test checks they cannot be called over RPC. |
| Groups (**differs**) | There is no `res.groups.privilege`. Groups use `category_id` (`ir.module.category`) and `users`. Users have `groups_id`. | `security/security_groups.xml` adds the category "Smart Chatter Inbox" under Sales and the group `group_sci_user`. |
| Client actions | `ir.actions.client` has no group field. | Access is enforced by the menu group and by a server check in every method. |
| CRM rules | `crm_rule_personal_lead`, `crm_rule_all_lead` and `crm_lead_company_rule`. | Not changed. Everything is read through them. |
| Domains (**differs**) | There is no `odoo.fields.Domain`. Domains are lists combined with `odoo.osv.expression.AND/OR`. | `_sci_base_domain` and `_sci_build_domain` in `models/crm_lead.py` build list domains. |
| Translations | `self.env._()` exists. | Same code as 19. |
| Activity dialog | Wizard model `mail.activity.schedule`, opened as in `mail/static/src/core/web/store_service_patch.js`. | **Schedule Follow-up** opens this wizard. |
| Frontend | Owl 2 with `useState` and `static props`. No `@odoo-module` header needed. | `inbox_action.js` is identical to 19. |
| Tests | `TransactionCase`, `HttpCase.start_tour`, `browser_js`, `new_test_user`, and Hoot tests in `web.assets_unit_tests`. | `tests/` and `static/tests/` are identical to 19, except the out-of-office case above. |
| Message hook | `mail.thread._message_post_after_hook(self, message, msg_values)`, as in 19. Incoming email goes through `message_process`, which returns the record id. | Reply detection (18.0.1.1.0) overrides it on `crm.lead` with the same code as 19. |
| Message types (**differs**) | `email`, `comment`, `email_outgoing`, `notification`, `auto_comment`, `user_notification`. There is no `out_of_office`. | Only `email` and `comment` count, as in 19. Out-of-office replies cannot be told apart, so they count as a customer message. The test for ignored messages skips that case. |
| Views | Lead form anchor `//page[@name='internal_notes']`. Settings anchor `//app[@name='crm']`. | Same views as 19. |

## Snooze rules
- Needs Action = no status, or `needs_action`, or `snoozed` with `sci_snooze_until <= now`.
- Snoozed = `snoozed` with `sci_snooze_until > now`.
- Unanswered = `sci_awaiting_reply` and not Snoozed.
- When a snooze expires, nothing is written to the database.
