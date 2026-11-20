from datetime import timedelta

from markupsafe import Markup

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .common import SciCommon

try:  # Odoo 19
    from odoo.service.model import get_public_method
except ImportError:  # Odoo 20 moved it to the ORM
    from odoo.models import get_public_method

PUBLIC_METHODS = (
    "sci_get_inbox_page", "sci_get_item", "sci_update_workflow",
    "sci_get_owner_candidates", "sci_get_filter_options",
)
MESSAGE_KEYS = {"body", "message", "messages", "message_ids", "preview", "attachment_ids", "subject"}


@tagged("post_install", "-at_install", "sci", "sci_security")
class TestInboxSecurity(SciCommon):

    def assertDenied(self, user, method, *args, **kwargs):
        with self.assertRaises(AccessError) as ctx:
            getattr(self.env["crm.lead"].with_user(user), method)(*args, **kwargs)
        return str(ctx.exception)

    def test_sec01_other_company_lead_detail_denied(self):
        message = self.assertDenied(self.sales_a, "sci_get_item", self.lead_b1.id)
        self.assertNotIn("secret", message)
        self.assertNotIn(self.lead_b1.name, message)
        self.assertDenied(self.sales_a, "sci_get_owner_candidates", self.lead_b1.id)

    def test_sec02_restricted_lead_no_detail_no_mutation(self):
        self.assertDenied(self.sales_a, "sci_get_item", self.lead_hidden.id)
        self.assertDenied(self.sales_a, "sci_update_workflow", self.lead_hidden.id, "done")
        self.assertEqual(self.lead_hidden.sci_state, "needs_action")
        # Missing ids give the very same neutral error as forbidden ones.
        missing = self.assertDenied(self.sales_a, "sci_get_item", 987654321)
        forbidden = self.assertDenied(self.sales_a, "sci_get_item", self.lead_hidden.id)
        self.assertEqual(missing, forbidden)
        for bogus in (None, False, "1 OR 1=1", [self.lead_a1.id], {"id": 1}):
            self.assertDenied(self.sales_a, "sci_get_item", bogus)

    def test_sec03_untrusted_filters_do_not_enable_domain_injection(self):
        baseline = self.page(self.sales_a)
        crafted = [
            {"quick": "all", "company_id": self.company_b.id},
            {"quick": "all", "domain": [(1, "=", 1)]},
            {"quick": "all", "team_id": self.team_b.id},
            {"quick": "all", "owner_id": self.sales_b.id},
            {"quick": "all", "lead_type": ["|", ("id", "!=", 0)]},
            {"quick": "all", "search": "%' OR 1=1 --"},
            {"quick": ["all"], "res_model": "res.partner", "allowed_company_ids": [self.company_b.id]},
        ]
        for filters in crafted:
            page = self.page(self.sales_a, filters)
            ids = {item["lead_id"] for item in page["items"]}
            self.assertLessEqual(ids, self.visible_a_ids, filters)
            self.assertLessEqual(page["total"], baseline["total"], filters)
            self.assertNotIn(self.lead_b1.id, ids)
            self.assertNotIn(self.lead_hidden.id, ids)
        # Non-dict filters are ignored entirely.
        self.assertEqual(self.page(self.sales_a, ["|", ("id", "!=", 0)])["total"], baseline["total"])

    def test_count_does_not_expose_inaccessible_leads(self):
        page = self.page(self.sales_a)
        self.assertEqual(page["total"], len(self.visible_a_ids))
        ids = {item["lead_id"] for item in page["items"]}
        self.assertNotIn(self.lead_hidden.id, ids)
        self.assertNotIn(self.lead_b1.id, ids)

    def test_sec04_read_only_user_cannot_write_workflow(self):
        # Simulate a deployment that restricts writes on one lead (global rule, write only).
        domain = f"[('id', '!=', {self.lead_a2.id})]"
        model_id = self.env["ir.model"]._get_id("crm.lead")
        if "ir.rule" in self.env:  # Odoo 19: record rules
            self.env["ir.rule"].create({
                "name": "SCI test: lead A2 is read-only", "model_id": model_id, "domain_force": domain,
                "perm_read": False, "perm_write": True, "perm_create": False, "perm_unlink": False,
            })
        else:  # Odoo 20: ir.access entries without a group restrict every user
            self.env["ir.access"].create({
                "name": "SCI test: lead A2 is read-only", "model_id": model_id, "operation": "u",
                "domain": domain,
            })
        Lead = self.env["crm.lead"].with_user(self.sales_a)
        item = Lead.sci_get_item(self.lead_a2.id)
        self.assertFalse(item["can_write"])
        self.assertDenied(self.sales_a, "sci_update_workflow", self.lead_a2.id, "done")
        self.assertEqual(self.lead_a2.sci_state, "waiting")
        self.assertTrue(Lead.sci_get_item(self.lead_a1.id)["can_write"])

    def test_sec05_portal_and_public_users_denied(self):
        public = self.env.ref("base.public_user")
        for user in (self.portal, public):
            self.assertDenied(user, "sci_get_inbox_page", {})
            self.assertDenied(user, "sci_get_item", self.lead_a1.id)
            self.assertDenied(user, "sci_update_workflow", self.lead_a1.id, "done")
            self.assertDenied(user, "sci_get_filter_options")
        self.assertEqual(self.lead_a1.sci_state, "needs_action")

    def test_sec06_crm_user_without_inbox_group_rejected(self):
        # The user has CRM rights on their own leads, but the product group is enforced server-side.
        self.assertDenied(self.no_sci_a, "sci_get_inbox_page", {})
        self.assertDenied(self.no_sci_a, "sci_get_item", self.lead_a1.id)
        self.assertDenied(self.no_sci_a, "sci_update_workflow", self.lead_a1.id, "done")
        self.assertDenied(self.no_sci_a, "sci_get_owner_candidates", self.lead_a1.id)
        self.assertDenied(self.no_sci_a, "sci_get_filter_options")
        # The workflow fields themselves are group-restricted, even through plain ORM writes.
        own_lead = self.env["crm.lead"].create({"name": "No group lead", "user_id": self.no_sci_a.id})
        with self.assertRaises(AccessError):
            own_lead.with_user(self.no_sci_a).write({"sci_state": "done"})
        with self.assertRaises(AccessError):
            own_lead.with_user(self.no_sci_a).read(["sci_state"])

    def test_sec07_responses_never_contain_messages(self):
        self.lead_a1.message_post(body=Markup("<p>TOP SECRET internal note</p>"), message_type="comment",
                                  subtype_xmlid="mail.mt_note")
        self.lead_a1.message_post(body=Markup("<p>Customer email body</p>"), message_type="email",
                                  subtype_xmlid="mail.mt_comment")
        Lead = self.env["crm.lead"].with_user(self.sales_a)
        responses = [
            Lead.sci_get_inbox_page({"quick": "all"}),
            Lead.sci_get_item(self.lead_a1.id),
            Lead.sci_update_workflow(self.lead_a1.id, "waiting"),
        ]
        for response in responses:
            dump = repr(response)
            self.assertNotIn("TOP SECRET", dump)
            self.assertNotIn("Customer email body", dump)
        for item in responses[0]["items"] + responses[1:]:
            self.assertFalse(MESSAGE_KEYS & item.keys(), "message preview is deferred in this release")

    def test_preview_only_if_secure_api_confirmed(self):
        item = self.env["crm.lead"].with_user(self.sales_a).sci_get_item(self.lead_a1.id)
        self.assertFalse(MESSAGE_KEYS & item.keys())

    def test_sec08_manager_cross_company_isolation(self):
        self.assertDenied(self.manager_a, "sci_get_item", self.lead_b1.id)
        self.assertDenied(self.manager_a, "sci_update_workflow", self.lead_b1.id, "done")
        ids_a = self.page_ids(self.manager_a)
        self.assertNotIn(self.lead_b1.id, ids_a)
        self.assertIn(self.lead_hidden.id, ids_a, "managers see all leads of their own company")
        self.assertEqual(self.page_ids(self.manager_b), {self.lead_b1.id})
        self.assertEqual(self.page(self.manager_b, {"quick": "all", "company_id": self.company_a.id})["total"], 1)
        self.assertEqual(self.lead_b1.sci_state, "needs_action")

    def test_sec09_html_is_returned_as_plain_text(self):
        item = self.env["crm.lead"].with_user(self.sales_a).sci_get_item(self.lead_html.id)
        self.assertEqual(item["name"], self.lead_html.name)
        self.assertNotIsInstance(item["name"], Markup)
        row = next(i for i in self.page(self.sales_a)["items"] if i["lead_id"] == self.lead_html.id)
        self.assertNotIsInstance(row["name"], Markup)

    def test_sec10_invalid_owner_status_and_oversized_request(self):
        Lead = self.env["crm.lead"].with_user(self.sales_a)
        for owner in (987654321, self.portal.id, self.sales_b.id, self.no_sci_a.id, "abc", -1):
            with self.assertRaises(ValidationError):
                Lead.sci_update_workflow(self.lead_a1.id, "waiting", owner_id=owner)
        self.assertFalse(self.lead_a1.sci_owner_id)
        self.assertEqual(self.lead_a1.sci_state, "needs_action")
        with self.assertRaises(ValidationError):
            Lead.sci_update_workflow(self.lead_a1.id, "waiting; DROP TABLE crm_lead")
        far_future = fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=36500))
        Lead.sci_update_workflow(self.lead_a1.id, "snoozed", snooze_until=far_future)
        self.assertEqual(self.page(self.sales_a, limit=100000)["limit"], 100)

    def test_private_helpers_not_rpc_callable(self):
        Lead = self.env["crm.lead"]
        for name in PUBLIC_METHODS:
            self.assertTrue(get_public_method(Lead, name))
        for name in ("_sci_build_domain", "_sci_get_accessible", "_sci_serialize", "_sci_owner_candidates"):
            with self.assertRaises(AccessError):
                get_public_method(Lead, name)
