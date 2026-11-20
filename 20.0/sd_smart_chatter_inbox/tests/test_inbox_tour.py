from odoo.tests import HttpCase, new_test_user, tagged


@tagged("post_install", "-at_install", "sci")
class TestInboxTour(HttpCase):

    def test_inbox_tour(self):
        user = new_test_user(
            self.env, login="sci_tour_user",
            groups="sales_team.group_sale_salesman,sd_smart_chatter_inbox.group_sci_user")
        Lead = self.env["crm.lead"]
        lead = Lead.create({"name": "SCI Tour lead", "user_id": user.id, "sci_state": "needs_action"})
        customer = self.env["res.partner"].create({"name": "SCI Tour customer", "email": "tour@example.com"})
        lead.message_post(body="Any news?", message_type="email", author_id=customer.id,
                          subtype_xmlid="mail.mt_comment")
        self.assertTrue(lead.sci_awaiting_reply)
        Lead.create({"name": "<script>alert('x')</script> Tour HTML", "user_id": user.id,
                     "sci_state": "needs_action"})
        self.start_tour("/odoo/action-sd_smart_chatter_inbox.action_sci_inbox", "sci_inbox_tour",
                        login="sci_tour_user")
        self.assertEqual(lead.sci_state, "waiting")
        self.assertFalse(lead.sci_awaiting_reply, "marking it Waiting by hand clears the flag")
        self.assertEqual(lead.sci_updated_by_id, user)
        self.assertEqual(lead.user_id, user)
