# Smart Chatter Inbox Pro: source repository

An Odoo app that turns CRM leads into a follow-up queue (Needs Action, Waiting, Done, Snoozed). Sold on the Odoo Apps store for $19.

| Folder | Odoo version | Module version |
|---|---|---|
| `19.0/sd_smart_chatter_inbox` | 19.0 (Community and Enterprise) | 19.0.1.0.0 |
| `20.0/sd_smart_chatter_inbox` | 20.0 | 20.0.1.0.0 |

The two versions differ only where Odoo changed. Most of the code is identical, including `inbox_model.js`, `inbox_api.js` and all the Python tests. These files differ:

- **`static/src/js/inbox_action.js`:** 19 uses Owl 2 (`useState`, `static props`). 20 uses Owl 3 (`proxy`, `useProps`).
- **`static/src/xml/inbox_action.xml`:** the 20 template uses `this.`, `t-out` and `t-model.proxy`, and Odoo icons instead of Font Awesome.
- **`models/crm_lead.py`:** 19 reads the setting with `get_param`; 20 uses `get_bool`.

See each version's `doc/COMPATIBILITY.md` for details. When you fix a bug, fix it in both folders.

## Tests (commands used for this release)
Odoo 19 (local Enterprise install):
```
"C:\Program Files\Odoo 19.0e.20260605\python\python.exe" "C:\Program Files\Odoo 19.0e.20260605\server\odoo-bin" ^
  -c "C:\Program Files\Odoo 19.0e.20260605\server\odoo.conf" -d sci_test ^
  --addons-path="C:\Program Files\Odoo 19.0e.20260605\server\odoo\addons,C:\projects\Smart_Chatter_Inbox_Pro\19.0" ^
  -i crm,sd_smart_chatter_inbox --test-enable --test-tags /sd_smart_chatter_inbox ^
  --http-port=8072 --stop-after-init
```
Odoo 20 (source checkout; uses the same PostgreSQL server):
```
C:\projects\odoo-src\venv20.0\Scripts\python.exe C:\projects\odoo-src\20.0\odoo-bin ^
  -c "C:\Program Files\Odoo 19.0e.20260605\server\odoo.conf" -d sci_test20 ^
  --addons-path=C:\projects\odoo-src\20.0\addons,C:\projects\odoo-src\20.0\odoo\addons,C:\projects\Smart_Chatter_Inbox_Pro\20.0 ^
  --data-dir=C:\projects\odoo-src\data20 -i crm,sd_smart_chatter_inbox --test-enable ^
  --test-tags /sd_smart_chatter_inbox --http-port=8078 --stop-after-init
```
In Git Bash, prefix the command with `MSYS_NO_PATHCONV=1`. Otherwise Git Bash rewrites `/sd_smart_chatter_inbox` into a Windows path and no tests run.

## Tools
- `tools/make_images.py`: generates the original icon and banner.
- `tools/seed_demo.py`: adds made-up demo leads for screenshots (`odoo-bin shell ... < tools/seed_demo.py`).
- `tools/screenshots.py`: takes the store screenshots with Playwright.

## Release ZIPs
```
git archive --format=zip -o dist/sd_smart_chatter_inbox-19.0.1.0.0.zip HEAD:19.0 sd_smart_chatter_inbox
git archive --format=zip -o dist/sd_smart_chatter_inbox-20.0.1.0.0.zip HEAD:20.0 sd_smart_chatter_inbox
```
