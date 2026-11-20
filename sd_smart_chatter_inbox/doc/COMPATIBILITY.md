# Compatibility notes: Odoo 17.0

These notes were checked against the Odoo 17.0 source at commit `dca5cd22` (2026-10-15), in `C:\projects\odoo-src\17.0`. The 17.0 build was ported from 18.0. Only the rows marked **differs** changed.

| Topic | Odoo 17 fact | How the module uses it |
|---|---|---|
| Access checks (**differs**) | There is no `has_access` or `_filtered_access`. 17 has `check_access_rights(op, raise_exception=False)` and `_filter_access_rules(op)`. | `models/crm_lead.py` adds the module-level helpers `_sci_has_access` and `_sci_filtered_access`, built on those two methods. Callers are unchanged. |
| Translations (**differs**) | There is no `self.env._()`. | Uses `from odoo import _`. |
| RPC exposure | `odoo/service/model.py::get_public_method` refuses names that start with `_`. | Helpers are named `_sci_*`. A test checks they cannot be called over RPC. |
| Groups | `category_id` (`ir.module.category`) and `users`, as in 18. | Same `security_groups.xml` as 18. |
| Domains | List domains with `odoo.osv.expression.AND/OR`, as in 18. | Same code as 18. |
| Activity dialog | Wizard model `mail.activity.schedule`, opened as in `mail/static/src/core/web/activity_service.js`. | **Schedule Follow-up** opens this wizard. |
| JS modules (**differs**) | Files are only transpiled as ES modules if they start with `/** @odoo-module **/`. | Every JS file has the header. |
| Unit tests (**differs**) | There is no Hoot. JS unit tests are QUnit in `web.qunit_suite_tests`. | `static/tests/inbox.test.js` holds the same 12 tests in QUnit, using `createWebClient` and `mockRPC`. `tests/test_inbox_qunit.py` runs them. |
| Tours (**differs**) | A step without `run` clicks by default. `run` functions get `this.$anchor`. Selects use `run: "text <value>"`. While a modal is open, triggers are searched inside it. Test tours need `test: true`. | Check-only steps use `isCheck: true`. The dialog step uses `[name=activity_type_id]` with no `.modal` prefix. |
| URLs (**differs**) | There are no `/odoo/...` URLs. Actions open with `/web#action=<xmlid>`. | The tour test and `tools/browser_smoke.py` use the right form. |
| Message hook | `mail.thread._message_post_after_hook(self, message, msg_values)`, as in 18 and 19. Incoming email goes through `message_process`, which returns the record id. | Reply detection (17.0.1.1.0) overrides it on `crm.lead` with the same code as 18. |
| Message types (**differs**) | `email`, `comment`, `email_outgoing`, `notification`, `auto_comment`, `user_notification`. There is no `out_of_office`. | Only `email` and `comment` count. Out-of-office replies cannot be told apart, so they count as a customer message. The test for ignored messages skips that case. |
| Views | Lead form anchor `//page[@name='internal_notes']`. Settings `<app name="crm">`, `<block>` and `<setting>`. `invisible`/`required` take expressions. | Same views as 18. |

## Snooze rules
- Needs Action = no status, or `needs_action`, or `snoozed` with `sci_snooze_until <= now`.
- Snoozed = `snoozed` with `sci_snooze_until > now`.
- Unanswered = `sci_awaiting_reply` and not Snoozed.
- When a snooze expires, nothing is written to the database.
