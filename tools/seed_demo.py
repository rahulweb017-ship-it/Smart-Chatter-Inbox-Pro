"""Seed fictitious demo data for screenshots. Run with: odoo-bin shell -d <db> < seed_demo.py"""
from datetime import timedelta

from odoo import fields

# Odoo 19+ calls the user groups field group_ids; 18 calls it groups_id.
GROUPS = "group_ids" if "group_ids" in env["res.users"]._fields else "groups_id"
Lead = env["crm.lead"]
admin = env.ref("base.user_admin")
team = env["crm.team"].search([], limit=1) or env["crm.team"].create({"name": "Sales"})


def user(login, name):
    u = env["res.users"].search([("login", "=", login)])
    if not u:
        u = env["res.users"].create({
            "login": login, "name": name,
            GROUPS: [(6, 0, [env.ref("sales_team.group_sale_salesman_all_leads").id,
                                  env.ref("sd_smart_chatter_inbox.group_sci_user").id])],
        })
    u[GROUPS] = [(4, env.ref("sd_smart_chatter_inbox.group_sci_user").id)]  # re-add after a reinstall
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
    existing = Lead.search([("name", "=", name)], limit=1)
    if existing:  # restore demo workflow values (e.g. after an uninstall/reinstall)
        existing.write({"sci_state": state or False, "sci_owner_id": owner.id if owner else False,
                        "sci_snooze_until": snooze or False})
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

# Customer emails, so reply detection has something to show (Unanswered list, "Customer replied").
# Posted like an incoming email: message_type "email", authored by the customer.
if "sci_awaiting_reply" in Lead._fields:
    replies = {
        "Annual support renewal": "Hi, can you send the renewal quote before Friday?",
        "Quote follow-up: 12 licenses": "We are ready to sign. Can we get 15 licenses at the same price?",
        "ERP rollout – 40 users": "Following up: did you get our requirements document?",
    }
    for name, body in replies.items():
        lead = Lead.search([("name", "=", name)], limit=1)
        if not lead:
            continue
        posted = lead.message_ids.filtered(lambda m: m.message_type == "email" and body in (m.body or ""))
        if not posted:
            lead.message_post(body=body, message_type="email", author_id=lead.partner_id.id,
                              subtype_xmlid="mail.mt_comment")
        else:  # re-run: restore what the email set instead of posting it again
            (posted[1:]).unlink()
            lead.write({"sci_state": "needs_action", "sci_awaiting_reply": True,
                        "sci_last_incoming_at": posted[0].date, "sci_update_source": "customer_reply",
                        "sci_updated_by_id": False})
env.cr.commit()
print("seeded", Lead.search_count([]))
