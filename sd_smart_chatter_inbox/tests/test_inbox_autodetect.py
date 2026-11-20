from datetime import timedelta
from itertools import count

from markupsafe import Markup

from odoo import fields
from odoo.tests import tagged

from .common import SciCommon

_message_ids = count(1)
OFF_PARAM = "sd_smart_chatter_inbox.disable_auto_detect"


@tagged("post_install", "-at_install", "sci")
class TestInboxAutoDetect(SciCommon):
    """Reply detection: customer messages reopen a lead, team replies move it to Waiting."""

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param(OFF_PARAM, False)

    # -- helpers --------------------------------------------------------

    def customer_email(self, lead=None, sender="Kunde <kunde@example.com>", subject="Re: your quote"):
        """Feed a raw email through the real mail gateway. Without ``lead`` it creates a new lead."""
        raw = (
            f"From: {sender}\r\nTo: sales@example.com\r\nSubject: {subject}\r\n"
            f"Message-ID: <sci-{next(_message_ids)}-{fields.Datetime.now().timestamp()}@example.com>\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n\r\nHello, any news on my quote?\r\n"
        )
        lead_id = self.env["mail.thread"].message_process(
            "crm.lead", raw, thread_id=lead.id if lead else None)
        return self.env["crm.lead"].browse(lead_id)

    def team_reply(self, lead, user, **kwargs):
        kwargs.setdefault("message_type", "comment")
        kwargs.setdefault("subtype_xmlid", "mail.mt_comment")
        return lead.with_user(user).message_post(body=Markup("<p>Thanks, here it is.</p>"), **kwargs)

    def snapshot(self, lead):
        lead.invalidate_recordset()
        return (lead.sci_state, lead.sci_awaiting_reply, lead.sci_last_incoming_at,
                lead.sci_last_outgoing_at, lead.sci_update_source)

    # -- customer messages ---------------------------------------------

    def test_customer_email_reopens_any_status(self):
        for lead in (self.lead_a2, self.lead_a3, self.lead_snoozed, self.lead_untriaged):
            with self.subTest(lead=lead.name):
                self.customer_email(lead)
                self.assertEqual(lead.sci_state, "needs_action")
                self.assertTrue(lead.sci_awaiting_reply)
                self.assertTrue(lead.sci_last_incoming_at)
                self.assertEqual(lead.sci_update_source, "customer_reply")
                self.assertFalse(lead.sci_snooze_until, "a customer message wakes a snoozed lead")
                self.assertFalse(lead.sci_updated_by_id, "set by detection, not by a person")
                self.assertEqual(lead.user_id, self.sales_a, "salesperson is never changed")

    def test_new_lead_from_email_needs_action(self):
        lead = self.customer_email(subject="Quote request for 40 desks")
        self.assertEqual(lead.name, "Quote request for 40 desks")
        self.assertEqual(lead.sci_state, "needs_action")
        self.assertTrue(lead.sci_awaiting_reply)

    # -- team replies ----------------------------------------------------

    def test_team_reply_moves_needs_action_to_waiting(self):
        self.customer_email(self.lead_a1)
        self.assertTrue(self.lead_a1.sci_awaiting_reply)
        self.team_reply(self.lead_a1, self.sales_a)
        self.assertEqual(self.lead_a1.sci_state, "waiting")
        self.assertFalse(self.lead_a1.sci_awaiting_reply)
        self.assertTrue(self.lead_a1.sci_last_outgoing_at)
        self.assertEqual(self.lead_a1.sci_update_source, "team_reply")
        self.assertFalse(self.lead_a1.sci_updated_by_id)

    def test_team_reply_on_untriaged_lead_moves_to_waiting(self):
        self.team_reply(self.lead_untriaged, self.sales_a)
        self.assertEqual(self.lead_untriaged.sci_state, "waiting")

    def test_team_reply_keeps_done_snoozed_and_waiting(self):
        until = self.lead_snoozed.sci_snooze_until
        for lead, state in ((self.lead_a3, "done"), (self.lead_snoozed, "snoozed"), (self.lead_a2, "waiting")):
            with self.subTest(state=state):
                self.team_reply(lead, self.sales_a)
                self.assertEqual(lead.sci_state, state)
                self.assertTrue(lead.sci_last_outgoing_at)
        self.assertEqual(self.lead_snoozed.sci_snooze_until, until)

    def test_team_email_reply_counts_as_outgoing(self):
        """An internal user answering by email (routed back to the lead) is a team reply."""
        self.customer_email(self.lead_a1, sender=f"Sales A <{self.sales_a.email}>")
        self.assertEqual(self.lead_a1.sci_state, "waiting")
        self.assertFalse(self.lead_a1.sci_awaiting_reply)

    def test_user_outside_inbox_group_can_still_post(self):
        lead = self.env["crm.lead"].create({
            "name": "SCI no-group lead", "user_id": self.no_sci_a.id, "team_id": self.team_a.id,
            "sci_state": "needs_action",
        })
        self.team_reply(lead, self.no_sci_a)  # must not raise: the poster cannot see sci_* fields
        self.assertEqual(lead.sci_state, "waiting")

    # -- ignored messages ---------------------------------------------

    def test_notes_and_automated_messages_are_ignored(self):
        lead = self.lead_a2
        before = self.snapshot(lead)
        self.team_reply(lead, self.sales_a, subtype_xmlid="mail.mt_note")  # Log note
        lead.message_post(body=Markup("<p>auto</p>"), message_type="auto_comment", subtype_xmlid="mail.mt_comment")
        lead.message_post(body=Markup("<p>out of office</p>"), message_type="out_of_office",
                          author_id=self.partner.id, subtype_xmlid="mail.mt_comment")
        lead.message_post(body=Markup("<p>mass mailing</p>"), message_type="email_outgoing",
                          subtype_xmlid="mail.mt_comment")
        lead.message_post(body=Markup("<p>system</p>"), message_type="notification")
        lead.message_post(body=Markup("<p>Lead enrichment</p>"), message_type="comment",
                          author_id=self.env.ref("base.partner_root").id, subtype_xmlid="mail.mt_comment")
        self.assertEqual(self.snapshot(lead), before)

    def test_setting_off_changes_nothing(self):
        self.env["ir.config_parameter"].sudo().set_param(OFF_PARAM, "True")
        before = self.snapshot(self.lead_a2)
        self.customer_email(self.lead_a2)
        self.assertEqual(self.snapshot(self.lead_a2), before)

    def test_settings_toggle_round_trip(self):
        Settings = self.env["res.config.settings"]
        self.assertTrue(Settings.create({}).sci_auto_detect, "on by default")
        Settings.create({"sci_auto_detect": False}).execute()
        self.assertTrue(self.env["ir.config_parameter"].sudo().get_param(OFF_PARAM))
        self.assertFalse(Settings.create({}).sci_auto_detect)
        Settings.create({"sci_auto_detect": True}).execute()
        self.assertFalse(self.env["ir.config_parameter"].sudo().get_param(OFF_PARAM))

    def test_creating_leads_sets_no_detection_fields(self):
        self.assertFalse(self.lead_untriaged.sci_awaiting_reply)
        self.assertFalse(self.lead_untriaged.sci_last_incoming_at)
        self.assertFalse(self.lead_untriaged.sci_update_source)

    # -- Unanswered filter and manual changes --------------------------

    def test_unanswered_filter(self):
        self.customer_email(self.lead_a2)
        self.customer_email(self.lead_a3)
        unanswered = {"quick": "unanswered"}
        self.assertEqual(self.page_ids(self.sales_a, unanswered), {self.lead_a2.id, self.lead_a3.id})
        Lead = self.env["crm.lead"].with_user(self.sales_a)
        # Snoozing hides it from Unanswered until the snooze ends; the flag is kept.
        later = fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=1))
        Lead.sci_update_workflow(self.lead_a2.id, "snoozed", snooze_until=later)
        self.assertTrue(self.lead_a2.sci_awaiting_reply)
        self.assertEqual(self.page_ids(self.sales_a, unanswered), {self.lead_a3.id})
        # Marking it Done by hand means it was dealt with.
        Lead.sci_update_workflow(self.lead_a3.id, "done")
        self.assertFalse(self.lead_a3.sci_awaiting_reply)
        self.assertEqual(self.lead_a3.sci_update_source, "manual")
        self.assertEqual(self.page_ids(self.sales_a, unanswered), set())

    def test_unanswered_respects_record_rules(self):
        self.customer_email(self.lead_hidden)
        self.customer_email(self.lead_b1)
        self.assertEqual(self.page_ids(self.sales_a, {"quick": "unanswered"}), set())

    def test_serialized_fields(self):
        self.customer_email(self.lead_a1)
        Lead = self.env["crm.lead"].with_user(self.sales_a)
        row = next(i for i in Lead.sci_get_inbox_page({"quick": "unanswered"})["items"]
                   if i["lead_id"] == self.lead_a1.id)
        self.assertIs(row["awaiting_reply"], True)
        self.assertTrue(row["last_incoming_at"])
        item = Lead.sci_get_item(self.lead_a1.id)
        self.assertEqual(item["update_source"], "customer_reply")
        self.assertIs(item["last_outgoing_at"], False)
