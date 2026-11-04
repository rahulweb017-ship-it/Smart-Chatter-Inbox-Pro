from odoo.tests import tagged

from .common import SciCommon


@tagged("post_install", "-at_install", "sci")
class TestInboxFilters(SciCommon):

    def test_quick_filters(self):
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "waiting"}), {self.lead_a2.id})
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "done"}), {self.lead_a3.id})
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "snoozed"}), {self.lead_snoozed.id})
        self.assertEqual(
            self.page_ids(self.sales_a, {"quick": "needs_action"}),
            {self.lead_a1.id, self.lead_html.id, self.lead_expired.id})
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "all"}), self.visible_a_ids)

    def test_untriaged_policy_setting(self):
        self.assertNotIn(self.lead_untriaged.id, self.page_ids(self.sales_a))
        self.set_include_untriaged(True)
        self.assertIn(self.lead_untriaged.id, self.page_ids(self.sales_a, {"quick": "needs_action"}))
        item = self.env["crm.lead"].with_user(self.sales_a).sci_get_item(self.lead_untriaged.id)
        self.assertTrue(item["is_untriaged"])
        self.assertEqual(item["effective_state"], "needs_action")
        self.assertNotIn(self.lead_untriaged.id, self.page_ids(self.sales_a, {"quick": "waiting"}))

    def test_search_title_and_customer(self):
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "all", "search": "A2 wait"}), {self.lead_a2.id})
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "all", "search": "株式会社"}), {self.lead_a1.id})
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "all", "search": "nothing-matches-this"}), set())
        # Over-long search terms are truncated, not rejected.
        page = self.page(self.sales_a, {"quick": "all", "search": "x" * 5000})
        self.assertEqual(page["total"], 0)

    def test_owner_team_type_filters(self):
        self.env["crm.lead"].with_user(self.manager_a).sci_update_workflow(
            self.lead_a2.id, "waiting", owner_id=self.manager_a.id)
        self.assertEqual(
            self.page_ids(self.manager_a, {"quick": "all", "owner_id": self.manager_a.id}),
            {self.lead_a2.id, self.lead_hidden.id})
        self.assertEqual(
            self.page_ids(self.manager_a, {"quick": "all", "team_id": self.team_a.id}),
            self.visible_a_ids | {self.lead_hidden.id})
        self.lead_a3.type = "lead"
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "all", "lead_type": "lead"}), {self.lead_a3.id})
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "all", "lead_type": "bogus"}), self.visible_a_ids)

    def test_search_order_and_pagination_stable(self):
        first = self.page(self.sales_a, limit=4, offset=0)
        second = self.page(self.sales_a, limit=4, offset=4)
        self.assertEqual(first["total"], len(self.visible_a_ids))
        self.assertTrue(first["has_more"])
        self.assertFalse(second["has_more"])
        ids = [i["lead_id"] for i in first["items"]] + [i["lead_id"] for i in second["items"]]
        self.assertEqual(len(ids), len(set(ids)), "no duplicates across pages")
        self.assertEqual(set(ids), self.visible_a_ids)
        again = [i["lead_id"] for i in self.page(self.sales_a, limit=4, offset=0)["items"]]
        self.assertEqual(again, ids[:4], "ordering is deterministic")
        # Most recently changed first.
        self.env["crm.lead"].with_user(self.sales_a).sci_update_workflow(self.lead_a3.id, "waiting")
        self.assertEqual(self.page(self.sales_a, limit=1)["items"][0]["lead_id"], self.lead_a3.id)

    def test_page_size_is_capped(self):
        page = self.page(self.sales_a, limit=100000)
        self.assertEqual(page["limit"], 100)
        page = self.page(self.sales_a, limit=-5, offset=-10)
        self.assertEqual(page["limit"], 30)
        self.assertEqual(page["offset"], 0)
        page = self.page(self.sales_a, limit="abc", offset=None)
        self.assertEqual(page["limit"], 30)

    def test_filter_options_only_expose_permitted_data(self):
        options = self.env["crm.lead"].with_user(self.sales_a).sci_get_filter_options()
        team_ids = {t["id"] for t in options["teams"]}
        self.assertIn(self.team_a.id, team_ids)
        self.assertNotIn(self.team_b.id, team_ids)
        self.assertEqual({c["id"] for c in options["companies"]}, {self.company_a.id})
        self.assertNotIn(self.sales_b.id, {o["id"] for o in options["owners"]})
