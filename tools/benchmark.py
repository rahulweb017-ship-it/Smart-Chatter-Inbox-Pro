"""AC-08 benchmark: 10,000 leads / 100,000 messages.

Run with:  odoo-bin shell -d <bench_db> < tools/benchmark.py
Seeds data once (idempotent), then times the inbox API as a salesperson (record rules
active) and as a sales manager, reporting wall time and SQL query counts.
"""
import random
import statistics
import time

from odoo import fields

N_LEADS, N_MESSAGES, RUNS = 10_000, 100_000, 15
STATES = ["needs_action", "waiting", "done", "snoozed", False]
Lead = env["crm.lead"]
random.seed(42)


def get_user(login, groups):
    user = env["res.users"].search([("login", "=", login)])
    if not user:
        user = env["res.users"].create({
            "login": login, "name": login,
            "group_ids": [(6, 0, [env.ref(g).id for g in groups])],
        })
    return user


manager = get_user("bench_manager", ["sales_team.group_sale_manager", "sd_smart_chatter_inbox.group_sci_user"])
sellers = [get_user(f"bench_seller_{i}", ["sales_team.group_sale_salesman", "sd_smart_chatter_inbox.group_sci_user"])
           for i in range(10)]
team = env["crm.team"].search([("name", "=", "Bench Team")]) or env["crm.team"].create({"name": "Bench Team"})
team.member_ids = [(6, 0, [u.id for u in sellers] + [manager.id])]

existing = Lead.search_count([("name", "=like", "BENCH %")])
if existing < N_LEADS:
    print(f"seeding {N_LEADS - existing} leads ...", flush=True)
    t0 = time.time()
    partners = env["res.partner"].create([{"name": f"Bench Customer {i}"} for i in range(500)])
    now = fields.Datetime.now()
    for start in range(existing, N_LEADS, 1000):
        vals = []
        for i in range(start, min(start + 1000, N_LEADS)):
            state = random.choice(STATES)
            v = {
                "name": f"BENCH {i} opportunity", "type": "opportunity",
                "user_id": random.choice(sellers).id, "team_id": team.id,
                "partner_id": random.choice(partners).id,
            }
            if state:
                v["sci_state"] = state
                v["sci_updated_at"] = now
            if state == "snoozed":
                v["sci_snooze_until"] = fields.Datetime.add(now, days=random.randint(-5, 5))
            vals.append(v)
        Lead.with_context(tracking_disable=True, mail_create_nolog=True).create(vals)
        env.cr.commit()
    lead_ids = Lead.search([("name", "=like", "BENCH %")]).ids
    print(f"seeding {N_MESSAGES} messages (bulk SQL) ...", flush=True)
    author = env.user.partner_id.id
    for start in range(0, N_MESSAGES, 10_000):
        env.cr.execute("""
            INSERT INTO mail_message (model, res_id, message_type, body, author_id, date, create_date, write_date, create_uid, write_uid)
            SELECT 'crm.lead', (%s::int[])[1 + (g %% %s)], 'comment', '<p>bench message ' || g || '</p>', %s,
                   now(), now(), now(), %s, %s
              FROM generate_series(%s, %s) g
        """, (lead_ids, len(lead_ids), author, env.uid, env.uid, start, start + 9_999))
        env.cr.commit()
    print(f"seeded in {time.time() - t0:.0f}s", flush=True)

env.cr.execute("SELECT count(*) FROM crm_lead WHERE name LIKE 'BENCH %%'")
leads_count = env.cr.fetchone()[0]
env.cr.execute("SELECT count(*) FROM mail_message WHERE model = 'crm.lead'")
print(f"dataset: {leads_count} leads, {env.cr.fetchone()[0]} crm.lead messages", flush=True)

ICP = env["ir.config_parameter"].sudo()


def set_untriaged(enabled):
    if hasattr(ICP, "set_bool"):
        ICP.set_bool("sd_smart_chatter_inbox.include_untriaged", enabled)
    else:
        ICP.set_param("sd_smart_chatter_inbox.include_untriaged", "True" if enabled else "")


def measure(label, user, call):
    model = Lead.with_user(user)
    call(model)  # warm caches
    times, queries = [], []
    for _ in range(RUNS):
        env.invalidate_all()
        q0 = env.cr.sql_log_count
        t0 = time.perf_counter()
        result = call(model)
        times.append((time.perf_counter() - t0) * 1000)
        queries.append(env.cr.sql_log_count - q0)
    p95 = sorted(times)[int(RUNS * 0.95) - 1]
    extra = f" total={result['total']} items={len(result['items'])}" if isinstance(result, dict) and "items" in result else ""
    print(f"{label:<52} median={statistics.median(times):7.1f}ms p95={p95:7.1f}ms queries={max(queries):3d}{extra}",
          flush=True)


seller = sellers[0]
some_lead = Lead.with_user(seller).search([("sci_state", "!=", False)], limit=1)
for untriaged in (False, True):
    set_untriaged(untriaged)
    tag = "untriaged ON " if untriaged else "untriaged OFF"
    measure(f"[{tag}] seller   page 1 (30)", seller, lambda m: m.sci_get_inbox_page({"quick": "needs_action"}))
    measure(f"[{tag}] seller   page 1 (100)", seller,
            lambda m: m.sci_get_inbox_page({"quick": "needs_action"}, limit=100))
    measure(f"[{tag}] seller   last page", seller, lambda m: m.sci_get_inbox_page({"quick": "all"}, offset=900))
    measure(f"[{tag}] seller   search 'Customer 12'", seller,
            lambda m: m.sci_get_inbox_page({"quick": "all", "search": "Customer 12"}))
    measure(f"[{tag}] manager  page 1 (30)", manager, lambda m: m.sci_get_inbox_page({"quick": "needs_action"}))
    measure(f"[{tag}] manager  My Queue", manager, lambda m: m.sci_get_inbox_page({"quick": "my"}))
    measure(f"[{tag}] manager  snoozed", manager, lambda m: m.sci_get_inbox_page({"quick": "snoozed"}))
measure("seller   filter options", seller, lambda m: m.sci_get_filter_options())
measure("seller   item detail", seller, lambda m: m.sci_get_item(some_lead.id))
measure("seller   owner candidates", seller, lambda m: m.sci_get_owner_candidates(some_lead.id))
set_untriaged(False)
env.cr.rollback()
