# Compatibility notes: Odoo 20.0

These notes were checked against the Odoo `20.0` source (`version_info = (20, 0, 0, FINAL, 0, '')`) at `C:\projects\odoo-src\20.0`. The table lists only what is different from the 19.0 release of this module.

| Topic | Odoo 20 change | How the module handles it |
|---|---|---|
| Frontend framework | Owl 3: `useState` is replaced by `proxy()`, and `static props` by `props = useProps({...})`. Templates use `this.` for component members and `t-out` instead of `t-esc`. Inputs bind with `t-model.proxy`. | `inbox_action.js` uses `proxy(initialState())` and `useProps({...standardActionServiceProps})`. The template was ported to `this.`, `t-out` and `t-model.proxy`. `inbox_model.js` and `inbox_api.js` are the same as in 19.0. |
| Settings storage | `ir.config_parameter` no longer has `get_param`/`set_param`. It now has typed `get_bool`/`set_bool` (plus int, float and str). | The model reads the setting with `get_bool`. The tests use whichever API exists. |
| Record rules | `ir.rule` is replaced by `ir.access` (CSV columns: `id`, `name`, `model_id`, `group_id/id`, `operation`, `domain`). Entries with no group restrict everyone; entries with a group grant access. | The module defines no rules. The SEC-04 test creates an `ir.access` entry with no group to make one lead read-only. |
| RPC exposure | `get_public_method` moved to `odoo/orm/models.py` (imported via `odoo.models`). It still refuses names that start with `_`. | The test imports from whichever location exists. |
| Lead form | `team_id` moved into a notebook page. | The module inserts after `//page[@name='internal_notes']`, which exists in both versions. |
| `mail.message._message_fetch` | The `is_notification` argument is now `search_filter`. | Not used (message preview is not shipped). |

**Unchanged from 19.0:**
- `check_access`, `has_access`, `_filtered_access`, `search_fetch`, `search_count`, `_read_group` and `odoo.fields.Domain`
- `res.groups.privilege`, `group_ids` and `has_group`
- the `mail.activity.schedule` wizard
- the `crm.crm_menu_sales` menu
- the asset bundles and the test framework (`TransactionCase`, `HttpCase`, Hoot)

The design decisions are the same as in 19.0: snooze expiry is computed in the domain with no cron, there is no install-time back-fill, and there is no message preview. See `SECURITY_NOTES.md`.
