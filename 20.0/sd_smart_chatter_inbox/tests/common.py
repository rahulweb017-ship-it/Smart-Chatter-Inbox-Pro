from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, new_test_user

SCI = "sd_smart_chatter_inbox.group_sci_user"


def _set_include_untriaged(env, enabled):
    params = env["ir.config_parameter"].sudo()
    if hasattr(params, "set_bool"):  # Odoo 20 typed parameters
        params.set_bool("sd_smart_chatter_inbox.include_untriaged", enabled)
    else:  # Odoo 19
        params.set_param("sd_smart_chatter_inbox.include_untriaged", "True" if enabled else "")


class SciCommon(TransactionCase):
    """Two companies, two teams, sales users with and without the inbox group, and leads
    covering every workflow state, a lead hidden by record rules, an untriaged lead and a
    lead whose name contains HTML/script and Unicode."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True, mail_create_nolog=True))
        Lead = cls.env["crm.lead"]
        # Do not depend on the database's current setting (demo databases may enable it).
        _set_include_untriaged(cls.env, False)
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "SCI Company B"})

        def user(login, groups, company):
            return new_test_user(
                cls.env, login=login, groups=groups, company_id=company.id, company_ids=[(6, 0, company.ids)])

        cls.manager_a = user("sci_manager_a", f"sales_team.group_sale_manager,{SCI}", cls.company_a)
        cls.sales_a = user("sci_sales_a", f"sales_team.group_sale_salesman,{SCI}", cls.company_a)
        cls.sales_a2 = user("sci_sales_a2", f"sales_team.group_sale_salesman,{SCI}", cls.company_a)
        cls.sales_b = user("sci_sales_b", f"sales_team.group_sale_salesman_all_leads,{SCI}", cls.company_b)
        cls.manager_b = user("sci_manager_b", f"sales_team.group_sale_manager,{SCI}", cls.company_b)
        cls.no_sci_a = user("sci_no_group_a", "sales_team.group_sale_salesman", cls.company_a)
        cls.portal = new_test_user(cls.env, login="sci_portal", groups="base.group_portal")

        cls.team_a = cls.env["crm.team"].create({
            "name": "SCI Team A", "company_id": cls.company_a.id,
            "member_ids": [(6, 0, (cls.sales_a | cls.sales_a2 | cls.manager_a).ids)],
        })
        cls.team_b = cls.env["crm.team"].create({
            "name": "SCI Team B", "company_id": cls.company_b.id,
            "member_ids": [(6, 0, (cls.sales_b | cls.manager_b).ids)],
        })
        cls.partner = cls.env["res.partner"].create({"name": "Ünïcødé Kunde 株式会社"})
        now = fields.Datetime.now()

        def lead(name, owner, team, company, **vals):
            return Lead.create(dict(
                name=name, type="opportunity", user_id=owner.id, team_id=team.id, company_id=company.id, **vals))

        cls.lead_a1 = lead("SCI A1 needs action", cls.sales_a, cls.team_a, cls.company_a,
                           partner_id=cls.partner.id, sci_state="needs_action")
        cls.lead_a2 = lead("SCI A2 waiting", cls.sales_a, cls.team_a, cls.company_a, sci_state="waiting")
        cls.lead_a3 = lead("SCI A3 done", cls.sales_a, cls.team_a, cls.company_a, sci_state="done")
        cls.lead_snoozed = lead("SCI A4 snoozed future", cls.sales_a, cls.team_a, cls.company_a,
                                sci_state="snoozed", sci_snooze_until=now + timedelta(days=2))
        cls.lead_expired = lead("SCI A5 snoozed expired", cls.sales_a, cls.team_a, cls.company_a,
                                sci_state="snoozed", sci_snooze_until=now - timedelta(hours=1))
        cls.lead_html = lead("<script>alert('x')</script><b>Ünïcødé</b> 測試", cls.sales_a, cls.team_a,
                             cls.company_a, sci_state="needs_action")
        cls.lead_untriaged = lead("SCI A7 untriaged", cls.sales_a, cls.team_a, cls.company_a)
        # Same company, other salesperson: hidden from sales_a by the native "own leads" rule.
        cls.lead_hidden = lead("SCI A8 hidden secret", cls.manager_a, cls.team_a, cls.company_a,
                               sci_state="needs_action")
        cls.lead_b1 = lead("SCI B1 other company secret", cls.sales_b, cls.team_b, cls.company_b,
                           sci_state="needs_action")

        cls.visible_a_ids = {
            cls.lead_a1.id, cls.lead_a2.id, cls.lead_a3.id, cls.lead_snoozed.id,
            cls.lead_expired.id, cls.lead_html.id,
        }

    def page(self, user, filters=None, **kwargs):
        return self.env["crm.lead"].with_user(user).sci_get_inbox_page(filters or {"quick": "all"}, **kwargs)

    def page_ids(self, user, filters=None, **kwargs):
        return {item["lead_id"] for item in self.page(user, filters, limit=100, **kwargs)["items"]}

    def set_include_untriaged(self, enabled):
        _set_include_untriaged(self.env, enabled)
