from odoo.tests import HttpCase, new_test_user, tagged


@tagged("post_install", "-at_install", "sci")
class TestInboxTour(HttpCase):

    def test_inbox_tour(self):
        user = new_test_user(
            self.env, login="sci_tour_user",
            groups="sales_team.group_sale_salesman,sd_smart_chatter_inbox.group_sci_user")
        Lead = self.env["crm.lead"]
        lead = Lead.create({"name": "SCI Tour lead", "user_id": user.id, "sci_state": "needs_action"})
        Lead.create({"name": "<script>alert('x')</script> Tour HTML", "user_id": user.id,
                     "sci_state": "needs_action"})
        self.start_tour("/odoo/action-sd_smart_chatter_inbox.action_sci_inbox", "sci_inbox_tour",
                        login="sci_tour_user")
        self.assertEqual(lead.sci_state, "waiting")
        self.assertEqual(lead.sci_updated_by_id, user)
        self.assertEqual(lead.user_id, user)
