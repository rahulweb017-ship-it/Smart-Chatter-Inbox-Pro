# CRM Follow Up Inbox (formerly Smart Chatter Inbox Pro): source repository

An Odoo app that turns CRM leads into a follow-up queue (Needs Action, Waiting, Done, Snoozed). Sold on the Odoo Apps store for $19.

| Folder | Odoo version | Module version |
|---|---|---|
| `17.0/sd_smart_chatter_inbox` | 17.0 (Community and Enterprise) | 17.0.1.0.0 |
| `18.0/sd_smart_chatter_inbox` | 18.0 (Community and Enterprise) | 18.0.1.0.0 |
| `19.0/sd_smart_chatter_inbox` | 19.0 (Community and Enterprise) | 19.0.1.0.0 |
| `20.0/sd_smart_chatter_inbox` | 20.0 | 20.0.1.0.0 |

The versions differ only where Odoo changed. Most of the code is identical, including `inbox_model.js`, `inbox_api.js` and all the Python tests. These files differ:

- **`static/src/js/inbox_action.js`:** 19 uses Owl 2 (`useState`, `static props`). 20 uses Owl 3 (`proxy`, `useProps`).
- **`static/src/xml/inbox_action.xml`:** the 20 template uses `this.`, `t-out` and `t-model.proxy`, and Odoo icons instead of Font Awesome.
- **`models/crm_lead.py`:** 19 reads the setting with `get_param`; 20 uses `get_bool`. 18 builds list domains with `odoo.osv.expression` because `odoo.fields.Domain` does not exist there.
- **`security/security_groups.xml`:** 19 and 20 use `res.groups.privilege` and `user_ids`. 18 uses an `ir.module.category` and `users`.

18.0 is otherwise identical to 19.0, including the JS, templates and tests.

17.0 is ported from 18.0 and also changes:
- **`models/crm_lead.py`:** 17 has no `has_access`, `_filtered_access` or `env._`. Small helpers `_sci_has_access` and `_sci_filtered_access` use `check_access_rights` and `_filter_access_rules`, and messages use `_()`.
- **JS:** every file starts with `/** @odoo-module **/`, which 17 needs to load it as a module.
- **Unit tests:** 17 has no Hoot, so `static/tests/inbox.test.js` holds the same 10 tests in QUnit (`web.qunit_suite_tests`), run by `tests/test_inbox_qunit.py`.
- **Tour:** uses the 17 tour format (`test: true`, `isCheck`, `this.$anchor`, `run: "text ..."`) and opens `/web#action=...`, because 17 has no `/odoo/...` URLs.

See each version's `doc/COMPATIBILITY.md` for details. When you fix a bug, fix it in all four folders.

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
Odoo 18 (source checkout). The 19 `odoo.conf` cannot be used as-is: 18 rejects `db_replica_port = None` and has no `rpc` server-wide module. Make a copy without those lines first, outside the repo, because it holds DB credentials:
```
grep -vE "=\s*None\s*$|^server_wide_modules" "C:/Program Files/Odoo 19.0e.20260605/server/odoo.conf" > %TEMP%/odoo18.conf
C:\projects\odoo-src\venv18.0\Scripts\python.exe C:\projects\odoo-src\18.0\odoo-bin ^
  -c %TEMP%\odoo18.conf -d sci_test18 ^
  --addons-path=C:\projects\odoo-src\18.0\addons,C:\projects\odoo-src\18.0\odoo\addons,C:\projects\Smart_Chatter_Inbox_Pro\18.0 ^
  --data-dir=C:\projects\odoo-src\data18 -i crm,sd_smart_chatter_inbox --test-enable ^
  --test-tags /sd_smart_chatter_inbox --http-port=8079 --stop-after-init
```
Odoo 17 (source checkout): the same filtered config copy as for 18.
```
C:\projects\odoo-src\venv17.0\Scripts\python.exe C:\projects\odoo-src\17.0\odoo-bin ^
  -c %TEMP%\odoo18.conf -d sci_test17 ^
  --addons-path=C:\projects\odoo-src\17.0\addons,C:\projects\odoo-src\17.0\odoo\addons,C:\projects\Smart_Chatter_Inbox_Pro\17.0 ^
  --data-dir=C:\projects\odoo-src\data17 -i crm,sd_smart_chatter_inbox --test-enable ^
  --test-tags /sd_smart_chatter_inbox --http-port=8077 --stop-after-init
```
In Git Bash, prefix the command with `MSYS_NO_PATHCONV=1`. Otherwise Git Bash rewrites `/sd_smart_chatter_inbox` into a Windows path and no tests run.

## Tools
- `tools/make_images.py`: generates the app icon.
- `tools/make_thumbnail.py <out_dir>`: generates the animated store thumbnail `banner.gif` (and `banner.png`).
- `tools/record_gifs.py <url> <out_dir> [triage snooze filters chatter mobile]`: records the store-page GIF demos from a running server. Run `seed_demo.py` first.
- `tools/seed_demo.py`: adds made-up demo leads for screenshots (`odoo-bin shell ... < tools/seed_demo.py`).
- `tools/screenshots.py`: takes the store screenshots with Playwright.
- `tools/benchmark.py`: AC-08 benchmark with 10,000 leads and 100,000 messages (`odoo-bin shell -d <bench_db> < tools/benchmark.py`). Results are in each version's `doc/BENCHMARK.md`.
- `tools/browser_smoke.py <url> chromium|firefox`: 13-step check of the real UI on desktop and phone sizes. It detects Odoo 17, which has no `/odoo/...` URLs, and uses `/web#action=...` instead.

## Odoo Apps store branches
The store reads one branch per Odoo version, with the addon folder at the branch root. Development happens on `master`. The `17.0`, `18.0`, `19.0` and `20.0` branches are generated from it:
```
git subtree split --prefix=17.0 -b 17.0 && git push origin 17.0
git subtree split --prefix=18.0 -b 18.0 && git push origin 18.0
git subtree split --prefix=19.0 -b 19.0 && git push origin 19.0
git subtree split --prefix=20.0 -b 20.0 && git push origin 20.0
```
Repository URLs to register on apps.odoo.com:
- `ssh://git@github.com/rahulweb017-ship-it/Smart-Chatter-Inbox-Pro.git#17.0`
- `ssh://git@github.com/rahulweb017-ship-it/Smart-Chatter-Inbox-Pro.git#18.0`
- `ssh://git@github.com/rahulweb017-ship-it/Smart-Chatter-Inbox-Pro.git#19.0`
- `ssh://git@github.com/rahulweb017-ship-it/Smart-Chatter-Inbox-Pro.git#20.0`

## Release ZIPs
```
git archive --format=zip -o dist/sd_smart_chatter_inbox-17.0.1.0.0.zip HEAD:17.0 sd_smart_chatter_inbox
git archive --format=zip -o dist/sd_smart_chatter_inbox-18.0.1.0.0.zip HEAD:18.0 sd_smart_chatter_inbox
git archive --format=zip -o dist/sd_smart_chatter_inbox-19.0.1.0.0.zip HEAD:19.0 sd_smart_chatter_inbox
git archive --format=zip -o dist/sd_smart_chatter_inbox-20.0.1.0.0.zip HEAD:20.0 sd_smart_chatter_inbox
```
