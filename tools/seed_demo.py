"""Seed fictitious demo data for screenshots. Run with: odoo-bin shell -d <db> < seed_demo.py"""
from datetime import timedelta

from odoo import fields

Lead = env["crm.lead"]
admin = env.ref("base.user_admin")
team = env["crm.team"].search([], limit=1) or env["crm.team"].create({"name": "Sales"})


def user(login, name):
    u = env["res.users"].search([("login", "=", login)])
    if not u:
        u = env["res.users"].create({
            "login": login, "name": name,
            "group_ids": [(6, 0, [env.ref("sales_team.group_sale_salesman_all_leads").id,
                                  env.ref("sd_smart_chatter_inbox.group_sci_user").id])],
        })
    return u


maya = user("maya.demo", "Maya Fernandes")
leo = user("leo.demo", "Leo Brandt")
team.member_ids = [(4, admin.id), (4, maya.id), (4, leo.id)]
params = env["ir.config_parameter"]
if hasattr(params, "set_bool"):  # Odoo 20
    params.set_bool("sd_smart_chatter_inbox.include_untriaged", True)
else:
    params.set_param("sd_smart_chatter_inbox.include_untriaged", "True")

now = fields.Datetime.now()
rows = [
    ("Website redesign request", "Northwind Studio", admin, "needs_action", None, None),
    ("ERP rollout – 40 users", "Bluefin Logistics", admin, "waiting", maya, None),
    ("Annual support renewal", "Kettle & Co", maya, "needs_action", None, None),
    ("Warehouse barcode pilot", "Orbital Foods", leo, "snoozed", None, now + timedelta(days=3)),
    ("Quote follow-up: 12 licenses", "Lumen Dental Group", admin, "needs_action", leo, None),
    ("Partnership enquiry", "Café Zürich GmbH", maya, "done", None, None),
    ("Trade show lead – POS demo", "Harbor Retail", leo, "waiting", None, None),
    ("Pricing question via website", "Sakura Trading 株式会社", admin, False, None, None),
]
for name, partner, sp, state, owner, snooze in rows:
    if Lead.search([("name", "=", name)]):
        continue
    p = env["res.partner"].create({"name": partner, "is_company": True,
                                    "email": partner.split()[0].lower() + "@example.com"})
    vals = {"name": name, "partner_id": p.id, "user_id": sp.id, "team_id": team.id,
            "type": "opportunity", "expected_revenue": 4800}
    if state:
        vals["sci_state"] = state
    if owner:
        vals["sci_owner_id"] = owner.id
    if snooze:
        vals["sci_snooze_until"] = snooze
    Lead.create(vals)
env.cr.commit()
print("seeded", Lead.search_count([]))
