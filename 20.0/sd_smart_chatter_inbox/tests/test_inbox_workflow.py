from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import SciCommon


@tagged("post_install", "-at_install", "sci")
class TestInboxWorkflow(SciCommon):

    def test_install_and_action_visible_to_authorized_group(self):
        menu = self.env.ref("sd_smart_chatter_inbox.menu_sci_inbox")
        Menu = self.env["ir.ui.menu"]
        self.assertIn(menu.id, Menu.with_user(self.sales_a)._visible_menu_ids())
        self.assertNotIn(menu.id, Menu.with_user(self.no_sci_a)._visible_menu_ids())
        action = self.env.ref("sd_smart_chatter_inbox.action_sci_inbox")
        self.assertEqual(action.tag, "sd_smart_chatter_inbox.InboxAction")

    def test_install_does_not_write_existing_leads(self):
        # No ORM default: untriaged leads keep an empty state (presented as Needs Action).
        self.assertFalse(self.lead_untriaged.sci_state)
        self.assertFalse(self.lead_untriaged.sci_updated_at)

    def test_status_transitions_and_invalid_state_rejected(self):
        Lead = self.env["crm.lead"].with_user(self.sales_a)
        item = Lead.sci_update_workflow(self.lead_a1.id, "waiting")
        self.assertEqual(item["state"], "waiting")
        self.assertEqual(self.lead_a1.sci_state, "waiting")
        self.assertEqual(self.lead_a1.sci_updated_by_id, self.sales_a)
        self.assertTrue(self.lead_a1.sci_updated_at)

        item = Lead.sci_update_workflow(self.lead_a1.id, "done")
        self.assertEqual(item["effective_state"], "done")
        self.assertIn(self.lead_a1.id, self.page_ids(self.sales_a, {"quick": "done"}))
        self.assertNotIn(self.lead_a1.id, self.page_ids(self.sales_a, {"quick": "waiting"}))

        for bad_state in ("archived", "", None, 1, "NEEDS_ACTION"):
            with self.assertRaises(ValidationError):
                Lead.sci_update_workflow(self.lead_a1.id, bad_state)
        self.assertEqual(self.lead_a1.sci_state, "done")

    def test_snooze_future_validation_and_expiry(self):
        Lead = self.env["crm.lead"].with_user(self.sales_a)
        with self.assertRaises(ValidationError):
            Lead.sci_update_workflow(self.lead_a1.id, "snoozed")
        past = fields.Datetime.to_string(fields.Datetime.now() - timedelta(minutes=5))
        with self.assertRaises(ValidationError):
            Lead.sci_update_workflow(self.lead_a1.id, "snoozed", snooze_until=past)
        with self.assertRaises(ValidationError):
            Lead.sci_update_workflow(self.lead_a1.id, "snoozed", snooze_until="not a date")

        future = fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=1))
        item = Lead.sci_update_workflow(self.lead_a1.id, "snoozed", snooze_until=future)
        self.assertEqual(item["effective_state"], "snoozed")
        self.assertIn(self.lead_a1.id, self.page_ids(self.sales_a, {"quick": "snoozed"}))
        self.assertNotIn(self.lead_a1.id, self.page_ids(self.sales_a, {"quick": "needs_action"}))

        # Expired snooze: computed back into Needs Action, nothing written.
        needs_action = self.page_ids(self.sales_a, {"quick": "needs_action"})
        self.assertIn(self.lead_expired.id, needs_action)
        self.assertNotIn(self.lead_expired.id, self.page_ids(self.sales_a, {"quick": "snoozed"}))
        self.assertEqual(self.lead_expired.sci_state, "snoozed")
        expired = Lead.sci_get_item(self.lead_expired.id)
        self.assertEqual(expired["effective_state"], "needs_action")

        # Leaving snoozed clears the snooze date.
        Lead.sci_update_workflow(self.lead_a1.id, "needs_action")
        self.assertFalse(self.lead_a1.sci_snooze_until)

    def test_snoozed_requires_datetime_constraint(self):
        with self.assertRaises(ValidationError):
            self.lead_a2.write({"sci_state": "snoozed", "sci_snooze_until": False})

    def test_owner_change_does_not_change_crm_user_id(self):
        Lead = self.env["crm.lead"].with_user(self.sales_a)
        item = Lead.sci_update_workflow(self.lead_a1.id, "needs_action", owner_id=self.manager_a.id)
        self.assertEqual(self.lead_a1.sci_owner_id, self.manager_a)
        self.assertEqual(self.lead_a1.user_id, self.sales_a, "salesperson must not change")
        self.assertEqual(item["owner"]["id"], self.manager_a.id)
        # A teammate who cannot read the lead is refused, and no access is granted.
        with self.assertRaises(ValidationError):
            Lead.sci_update_workflow(self.lead_a1.id, "needs_action", owner_id=self.sales_a2.id)
        self.assertEqual(self.lead_a1.sci_owner_id, self.manager_a)
        self.assertFalse(self.lead_a1.with_user(self.sales_a2).has_access("read"))
        # Clearing falls back to the salesperson.
        item = Lead.sci_update_workflow(self.lead_a1.id, "needs_action", owner_id=False)
        self.assertFalse(item["owner"])
        self.assertEqual(item["effective_owner"]["id"], self.sales_a.id)

    def test_owner_candidates_exclude_ineligible_users(self):
        candidates = {c["id"] for c in self.env["crm.lead"].with_user(self.manager_a)
                      .sci_get_owner_candidates(self.lead_a1.id)}
        self.assertIn(self.sales_a.id, candidates)
        self.assertIn(self.manager_a.id, candidates)
        self.assertNotIn(self.no_sci_a.id, candidates, "users without the inbox group are excluded")
        self.assertNotIn(self.sales_b.id, candidates, "other-company users are excluded")
        self.assertNotIn(self.portal.id, candidates)

    def test_my_queue(self):
        ids = self.page_ids(self.sales_a, {"quick": "my"})
        self.assertIn(self.lead_a1.id, ids)
        self.assertIn(self.lead_a2.id, ids)
        self.assertIn(self.lead_expired.id, ids)
        self.assertNotIn(self.lead_a3.id, ids, "done items leave My Queue")
        self.assertNotIn(self.lead_snoozed.id, ids, "active snoozes leave My Queue")
        # Assign to the manager: it leaves sales_a's queue and enters the manager's.
        self.env["crm.lead"].with_user(self.manager_a).sci_update_workflow(
            self.lead_a2.id, "waiting", owner_id=self.manager_a.id)
        self.assertNotIn(self.lead_a2.id, self.page_ids(self.sales_a, {"quick": "my"}))
        self.assertIn(self.lead_a2.id, self.page_ids(self.manager_a, {"quick": "my"}))
