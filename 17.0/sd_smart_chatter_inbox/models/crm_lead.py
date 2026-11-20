from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.osv import expression

SCI_GROUP = "sd_smart_chatter_inbox.group_sci_user"
SCI_STATES = ("needs_action", "waiting", "done", "snoozed")
SCI_QUICK_FILTERS = ("my", "needs_action", "unanswered", "waiting", "done", "snoozed", "all")
SCI_LEAD_TYPES = ("lead", "opportunity")
SCI_WORKFLOW_FIELDS = {"sci_state", "sci_owner_id", "sci_snooze_until"}
SCI_AUTO_DETECT_OFF_PARAM = "sd_smart_chatter_inbox.disable_auto_detect"
# Only messages a person wrote count. Skipped: notes, tracking/system notifications,
# automated messages (auto_comment), mass mailings (email_outgoing) and out-of-office replies.
SCI_CONVERSATION_TYPES = ("email", "comment")
SCI_DEFAULT_LIMIT = 30
SCI_MAX_LIMIT = 100
SCI_MAX_SEARCH = 100
SCI_ORDER = "sci_updated_at DESC NULLS LAST, id DESC"
SCI_LIST_FIELDS = [
    "name", "type", "partner_id", "partner_name", "contact_name", "stage_id", "user_id",
    "team_id", "company_id", "priority", "sci_state", "sci_owner_id", "sci_snooze_until",
    "sci_updated_at", "sci_awaiting_reply", "sci_last_incoming_at",
]
SCI_DETAIL_FIELDS = SCI_LIST_FIELDS + [
    "email_from", "phone", "expected_revenue", "activity_date_deadline", "sci_updated_by_id",
    "sci_last_outgoing_at", "sci_update_source",
]


def _sci_filtered_access(records, operation):
    """Odoo 17 has no ``_filtered_access``: the records the current user may ``operation``."""
    if not records.check_access_rights(operation, raise_exception=False):
        return records.browse()
    return records._filter_access_rules(operation)


def _sci_has_access(records, operation):
    """Odoo 17 has no ``has_access``: True if the user may ``operation`` on all ``records``."""
    return _sci_filtered_access(records, operation) == records


class CrmLead(models.Model):
    _inherit = "crm.lead"

    # No ORM default on purpose: a default would be back-filled into every existing lead at
    # install time. An empty state means "untriaged" and is presented as Needs Action.
    sci_state = fields.Selection(
        [
            ("needs_action", "Needs Action"),
            ("waiting", "Waiting"),
            ("done", "Done"),
            ("snoozed", "Snoozed"),
        ],
        string="Inbox Status",
        copy=False,
        index=True,
        groups=SCI_GROUP,
        help="Needs Action: team follow-up pending. Set automatically when the customer writes.\n"
        "Waiting: a response is expected from the customer or a third party.\n"
        "Done: no immediate follow-up needed.\n"
        "Snoozed: hidden from Needs Action until the snooze date/time.",
    )
    sci_owner_id = fields.Many2one(
        "res.users",
        string="Inbox Owner",
        copy=False,
        index="btree_not_null",
        groups=SCI_GROUP,
        domain=[("share", "=", False)],
        help="Follow-up owner in Smart Chatter Inbox. Falls back to the salesperson when empty. "
        "Does not change the salesperson and grants no access to the lead.",
    )
    sci_snooze_until = fields.Datetime(string="Snoozed Until", copy=False, groups=SCI_GROUP)
    sci_updated_at = fields.Datetime(string="Inbox Updated On", copy=False, readonly=True, groups=SCI_GROUP)
    sci_updated_by_id = fields.Many2one(
        "res.users", string="Inbox Updated By", copy=False, readonly=True, groups=SCI_GROUP,
    )
    # Reply detection. Like the fields above, none has a default, so installing or upgrading
    # writes nothing to existing leads: they are only set by messages posted afterwards.
    sci_awaiting_reply = fields.Boolean(
        string="Customer Replied", copy=False, readonly=True, index=True, groups=SCI_GROUP,
        help="The customer wrote last and the team has not replied yet.",
    )
    sci_last_incoming_at = fields.Datetime(
        string="Last Customer Message", copy=False, readonly=True, groups=SCI_GROUP)
    sci_last_outgoing_at = fields.Datetime(
        string="Last Team Reply", copy=False, readonly=True, groups=SCI_GROUP)
    sci_update_source = fields.Selection(
        [("manual", "Manual"), ("customer_reply", "Customer replied"), ("team_reply", "Team replied")],
        string="Status Set By", copy=False, readonly=True, groups=SCI_GROUP,
        help="Whether the inbox status was last set by a person or by reply detection.",
    )

    @api.constrains("sci_state", "sci_snooze_until")
    def _check_sci_snooze(self):
        for lead in self:
            if lead.sci_state == "snoozed" and not lead.sci_snooze_until:
                raise ValidationError(_("A snoozed item needs a snooze date and time."))

    def write(self, vals):
        if SCI_WORKFLOW_FIELDS & vals.keys():
            vals = dict(vals)
            if vals.get("sci_state") and vals["sci_state"] != "snoozed":
                vals["sci_snooze_until"] = False
            vals.setdefault("sci_updated_at", fields.Datetime.now())
            vals.setdefault("sci_updated_by_id", self.env.uid)
            if "sci_state" in vals:
                vals.setdefault("sci_update_source", "manual")
                # Marking a lead Waiting or Done by hand means it was dealt with.
                if vals["sci_update_source"] == "manual" and vals["sci_state"] in ("waiting", "done"):
                    vals.setdefault("sci_awaiting_reply", False)
        return super().write(vals)

    # ------------------------------------------------------------------
    # Reply detection
    # ------------------------------------------------------------------

    def _message_post_after_hook(self, message, msg_vals):
        result = super()._message_post_after_hook(message, msg_vals)
        self._sci_on_message_posted(message)
        return result

    @api.model
    def _sci_auto_detect_enabled(self):
        return not self.env["ir.config_parameter"].sudo().get_param(SCI_AUTO_DETECT_OFF_PARAM)

    def _sci_message_direction(self, message):
        """'incoming' for a customer message, 'outgoing' for a team reply, None to ignore."""
        message = message.sudo()  # the poster may be OdooBot (mail gateway) or a user outside the group
        if message.message_type not in SCI_CONVERSATION_TYPES:
            return None
        if message.is_internal or message.subtype_id.internal:
            return None  # internal notes are not part of the conversation with the customer
        author = message.author_id
        if author and author == self.env.ref("base.partner_root", raise_if_not_found=False):
            return None  # OdooBot: lead enrichment and other automated posts
        internal = author and author.with_context(active_test=False).user_ids.filtered(lambda u: not u.share)
        return "outgoing" if internal else "incoming"

    def _sci_on_message_posted(self, message):
        if len(self) != 1 or not self._sci_auto_detect_enabled():
            return
        direction = self._sci_message_direction(message)
        if not direction:
            return
        # sudo: the poster is often not an inbox user (incoming mail runs as OdooBot). Only this
        # lead's own sci_* workflow fields are written; nothing is read or shown through sudo.
        lead = self.sudo()
        when = message.date or fields.Datetime.now()
        if direction == "incoming":
            vals = {
                "sci_awaiting_reply": True,
                "sci_last_incoming_at": when,
                "sci_state": "needs_action",
                "sci_update_source": "customer_reply",
                "sci_updated_by_id": False,
            }
        else:
            vals = {"sci_awaiting_reply": False, "sci_last_outgoing_at": when}
            if not lead.sci_state or lead.sci_state == "needs_action":
                vals.update(sci_state="waiting", sci_update_source="team_reply", sci_updated_by_id=False)
        lead.write(vals)

    # ------------------------------------------------------------------
    # Public RPC API used by the Smart Chatter Inbox client action.
    # Every method runs as the calling user (never sudo) so ACLs, record
    # rules and multi-company rules of crm.lead decide what is visible.
    # ------------------------------------------------------------------

    @api.model
    def sci_get_inbox_page(self, filters=None, limit=SCI_DEFAULT_LIMIT, offset=0):
        self._sci_check_product_access()
        limit = self._sci_to_int(limit)
        limit = min(limit, SCI_MAX_LIMIT) if limit and limit > 0 else SCI_DEFAULT_LIMIT
        offset = max(0, self._sci_to_int(offset) or 0)
        domain = self._sci_build_domain(filters)
        total = self.search_count(domain)
        leads = self.search_fetch(domain, SCI_LIST_FIELDS, offset=offset, limit=limit, order=SCI_ORDER)
        return {
            "items": leads._sci_serialize(SCI_LIST_FIELDS),
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(leads) < total,
        }

    @api.model
    def sci_get_item(self, lead_id):
        self._sci_check_product_access()
        lead = self._sci_get_accessible(lead_id, "read")
        item = lead._sci_serialize(SCI_DETAIL_FIELDS)[0]
        item["can_write"] = _sci_has_access(lead, "write")
        return item

    @api.model
    def sci_update_workflow(self, lead_id, state, owner_id=None, snooze_until=None):
        """Change status, owner and snooze of one lead.

        ``owner_id``: None keeps the current owner, False/0 clears it, an id sets it.
        ``snooze_until``: UTC string "YYYY-MM-DD HH:MM:SS", required (and in the future) when snoozing.
        """
        self._sci_check_product_access()
        if state not in SCI_STATES:
            raise ValidationError(_("Invalid inbox status."))
        lead = self._sci_get_accessible(lead_id, "write")
        vals = {"sci_state": state}
        if state == "snoozed":
            vals["sci_snooze_until"] = self._sci_parse_future_datetime(snooze_until)
        if owner_id is not None:
            if owner_id is False or owner_id == 0:
                vals["sci_owner_id"] = False
            else:
                owner_id = self._sci_to_int(owner_id)
                if not owner_id or owner_id not in lead._sci_owner_candidates().ids:
                    raise ValidationError(_(
                        "This user cannot be the inbox owner: they must be an active Smart Chatter Inbox "
                        "user of the lead's sales team who can already access this lead."))
                vals["sci_owner_id"] = owner_id
        lead.write(vals)
        return self.sci_get_item(lead.id)

    @api.model
    def sci_get_owner_candidates(self, lead_id):
        self._sci_check_product_access()
        lead = self._sci_get_accessible(lead_id, "read")
        return [{"id": user.id, "name": user.name} for user in lead._sci_owner_candidates()]

    @api.model
    def sci_get_filter_options(self):
        self._sci_check_product_access()
        teams = self.env["crm.team"].search_fetch([], ["name"], limit=200, order="name")
        owner_groups = self._read_group(
            self._sci_base_domain(), ["sci_owner_id"], limit=200, order="sci_owner_id")
        owners = self.env.user | self.env["res.users"].union(*(owner for (owner,) in owner_groups))
        return {
            "teams": [{"id": team.id, "name": team.name} for team in teams],
            "owners": [{"id": user.id, "name": user.name} for user in owners.sorted("name")],
            "companies": [{"id": company.id, "name": company.name} for company in self.env.companies],
            "include_untriaged": self._sci_include_untriaged(),
            "is_manager": self.env.user.has_group("sales_team.group_sale_manager"),
            "current_user_id": self.env.uid,
        }

    # ------------------------------------------------------------------
    # Helpers (private: not callable over RPC)
    # ------------------------------------------------------------------

    @api.model
    def _sci_check_product_access(self):
        user = self.env.user
        if not user._is_internal() or not user.has_group(SCI_GROUP):
            raise AccessError(_("You are not allowed to use Smart Chatter Inbox."))

    @api.model
    def _sci_get_accessible(self, lead_id, operation):
        """Return the lead if the current user may perform ``operation`` on it.

        The same neutral error is raised for missing and forbidden records so that
        callers cannot probe which ids exist.
        """
        lead_id = self._sci_to_int(lead_id)
        lead = self.browse(lead_id).exists() if lead_id else self.browse()
        if not lead or not _sci_has_access(lead, "read") or not _sci_has_access(lead, operation):
            raise AccessError(_("This CRM record does not exist or you no longer have access to it."))
        return lead

    def _sci_owner_candidates(self):
        """Users who may own the follow-up of this lead.

        Members/leader of the lead's sales team, the salesperson and the current user,
        restricted to active internal Smart Chatter Inbox users who can already read the
        lead under their own access rights. Nothing is shared or granted.
        """
        self.ensure_one()
        team = _sci_filtered_access(self.team_id, "read")
        users = team.member_ids | team.user_id | self.user_id | self.env.user | self.sci_owner_id
        candidates = self.env["res.users"]
        for user in users:
            if not user.active or user.share or not user.has_group(SCI_GROUP):
                continue
            as_candidate = self.with_user(user).with_context(allowed_company_ids=[])
            if _sci_has_access(as_candidate, "read"):
                candidates |= user
        return candidates.sorted("name")

    @api.model
    def _sci_include_untriaged(self):
        return bool(self.env["ir.config_parameter"].sudo().get_param("sd_smart_chatter_inbox.include_untriaged"))

    @api.model
    def _sci_base_domain(self):
        if self._sci_include_untriaged():
            return []
        return [("sci_state", "!=", False)]

    @api.model
    def _sci_build_domain(self, filters):
        """Translate whitelisted UI filters into a domain. Unknown keys are ignored."""
        filters = filters if isinstance(filters, dict) else {}
        now = fields.Datetime.now()
        AND, OR = expression.AND, expression.OR
        domains = [self._sci_base_domain()]

        snoozed_expired = [("sci_state", "=", "snoozed"), ("sci_snooze_until", "<=", now)]
        snoozed_active = [("sci_state", "=", "snoozed"), ("sci_snooze_until", ">", now)]
        needs_action = OR([[("sci_state", "in", [False, "needs_action"])], snoozed_expired])

        quick = filters.get("quick")
        if quick == "my":
            mine = OR([
                [("sci_owner_id", "=", self.env.uid)],
                [("sci_owner_id", "=", False), ("user_id", "=", self.env.uid)],
            ])
            domains += [mine, OR([needs_action, [("sci_state", "=", "waiting")]])]
        elif quick == "needs_action":
            domains.append(needs_action)
        elif quick == "unanswered":
            # The customer wrote last; a lead snoozed after that stays hidden until it wakes up.
            domains += [[("sci_awaiting_reply", "=", True)], ["!"] + AND([snoozed_active])]
        elif quick == "snoozed":
            domains.append(snoozed_active)
        elif quick in ("waiting", "done"):
            domains.append([("sci_state", "=", quick)])

        search = filters.get("search")
        if isinstance(search, str) and search.strip():
            term = search.strip()[:SCI_MAX_SEARCH]
            domains.append(OR([
                [("name", "ilike", term)], [("partner_name", "ilike", term)],
                [("contact_name", "ilike", term)], [("partner_id", "ilike", term)],
            ]))

        owner_id = self._sci_to_int(filters.get("owner_id"))
        if owner_id:
            domains.append(OR([
                [("sci_owner_id", "=", owner_id)],
                [("sci_owner_id", "=", False), ("user_id", "=", owner_id)],
            ]))

        team_id = self._sci_to_int(filters.get("team_id"))
        if team_id:
            domains.append([("team_id", "=", team_id)])

        # Only companies already enabled for this user/session; anything else is ignored.
        company_id = self._sci_to_int(filters.get("company_id"))
        if company_id and company_id in self.env.companies.ids:
            domains.append([("company_id", "=", company_id)])

        if filters.get("lead_type") in SCI_LEAD_TYPES:
            domains.append([("type", "=", filters["lead_type"])])

        return AND(domains)

    def _sci_serialize(self, field_names):
        """Plain-data rows built only from fields the user can read.

        Related record names are read in batch and only for records the user can access.
        """
        now = fields.Datetime.now()
        names = {}
        for fname in field_names:
            if self._fields[fname].type == "many2one":
                related = _sci_filtered_access(self[fname], "read")
                names[fname] = {rec.id: rec.display_name for rec in related}

        def m2o(lead, fname):
            rec = lead[fname]
            if not rec or rec.id not in names[fname]:
                return False
            return {"id": rec.id, "name": names[fname][rec.id]}

        def dt(value):
            return fields.Datetime.to_string(value) if value else False

        rows = []
        for lead in self:
            state = lead.sci_state or False
            effective = state or "needs_action"
            if state == "snoozed" and lead.sci_snooze_until and lead.sci_snooze_until <= now:
                effective = "needs_action"
            owner = m2o(lead, "sci_owner_id")
            row = {
                "lead_id": lead.id,
                "name": lead.name or "",
                "type": lead.type,
                "partner": m2o(lead, "partner_id"),
                "partner_name": lead.partner_name or lead.contact_name or "",
                "stage": m2o(lead, "stage_id"),
                "salesperson": m2o(lead, "user_id"),
                "team": m2o(lead, "team_id"),
                "company": m2o(lead, "company_id"),
                "priority": lead.priority,
                "state": state,
                "effective_state": effective,
                "is_untriaged": not state,
                "owner": owner,
                "effective_owner": owner or m2o(lead, "user_id"),
                "snooze_until": dt(lead.sci_snooze_until),
                "updated_at": dt(lead.sci_updated_at),
                "awaiting_reply": bool(lead.sci_awaiting_reply),
                "last_incoming_at": dt(lead.sci_last_incoming_at),
            }
            if "email_from" in field_names:
                row.update({
                    "email_from": lead.email_from or "",
                    "phone": lead.phone or "",
                    "expected_revenue": lead.expected_revenue,
                    "currency": lead.company_currency.name or "",
                    "activity_date_deadline": fields.Date.to_string(lead.activity_date_deadline)
                    if lead.activity_date_deadline else False,
                    "updated_by": m2o(lead, "sci_updated_by_id"),
                    "last_outgoing_at": dt(lead.sci_last_outgoing_at),
                    "update_source": lead.sci_update_source or False,
                })
            rows.append(row)
        return rows

    @api.model
    def _sci_parse_future_datetime(self, value):
        try:
            parsed = fields.Datetime.to_datetime(value) if isinstance(value, str) and value else None
        except ValueError:
            parsed = None
        if not parsed:
            raise ValidationError(_("Choose a valid snooze date and time."))
        if parsed <= fields.Datetime.now():
            raise ValidationError(_("The snooze date and time must be in the future."))
        return parsed

    @api.model
    def _sci_to_int(self, value):
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
