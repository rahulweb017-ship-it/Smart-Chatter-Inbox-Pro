from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain

SCI_GROUP = "sd_smart_chatter_inbox.group_sci_user"
SCI_STATES = ("needs_action", "waiting", "done", "snoozed")
SCI_QUICK_FILTERS = ("my", "needs_action", "waiting", "done", "snoozed", "all")
SCI_LEAD_TYPES = ("lead", "opportunity")
SCI_WORKFLOW_FIELDS = {"sci_state", "sci_owner_id", "sci_snooze_until"}
SCI_DEFAULT_LIMIT = 30
SCI_MAX_LIMIT = 100
SCI_MAX_SEARCH = 100
SCI_ORDER = "sci_updated_at DESC NULLS LAST, id DESC"
SCI_LIST_FIELDS = [
    "name", "type", "partner_id", "partner_name", "contact_name", "stage_id", "user_id",
    "team_id", "company_id", "priority", "sci_state", "sci_owner_id", "sci_snooze_until",
    "sci_updated_at",
]
SCI_DETAIL_FIELDS = SCI_LIST_FIELDS + [
    "email_from", "phone", "expected_revenue", "activity_date_deadline", "sci_updated_by_id",
]


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
        help="Needs Action: team follow-up pending (a manual workflow state, not proof an email is unread).\n"
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

    @api.constrains("sci_state", "sci_snooze_until")
    def _check_sci_snooze(self):
        for lead in self:
            if lead.sci_state == "snoozed" and not lead.sci_snooze_until:
                raise ValidationError(self.env._("A snoozed item needs a snooze date and time."))

    def write(self, vals):
        if SCI_WORKFLOW_FIELDS & vals.keys():
            vals = dict(vals)
            if vals.get("sci_state") and vals["sci_state"] != "snoozed":
                vals["sci_snooze_until"] = False
            vals.setdefault("sci_updated_at", fields.Datetime.now())
            vals.setdefault("sci_updated_by_id", self.env.uid)
        return super().write(vals)

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
        item["can_write"] = lead.has_access("write")
        return item

    @api.model
    def sci_update_workflow(self, lead_id, state, owner_id=None, snooze_until=None):
        """Change status, owner and snooze of one lead.

        ``owner_id``: None keeps the current owner, False/0 clears it, an id sets it.
        ``snooze_until``: UTC string "YYYY-MM-DD HH:MM:SS", required (and in the future) when snoozing.
        """
        self._sci_check_product_access()
        if state not in SCI_STATES:
            raise ValidationError(self.env._("Invalid inbox status."))
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
                    raise ValidationError(self.env._(
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
            raise AccessError(self.env._("You are not allowed to use Smart Chatter Inbox."))

    @api.model
    def _sci_get_accessible(self, lead_id, operation):
        """Return the lead if the current user may perform ``operation`` on it.

        The same neutral error is raised for missing and forbidden records so that
        callers cannot probe which ids exist.
        """
        lead_id = self._sci_to_int(lead_id)
        lead = self.browse(lead_id).exists() if lead_id else self.browse()
        if not lead or not lead.has_access("read") or not lead.has_access(operation):
            raise AccessError(self.env._("This CRM record does not exist or you no longer have access to it."))
        return lead

    def _sci_owner_candidates(self):
        """Users who may own the follow-up of this lead.

        Members/leader of the lead's sales team, the salesperson and the current user,
        restricted to active internal Smart Chatter Inbox users who can already read the
        lead under their own access rights. Nothing is shared or granted.
        """
        self.ensure_one()
        team = self.team_id._filtered_access("read")
        users = team.member_ids | team.user_id | self.user_id | self.env.user | self.sci_owner_id
        candidates = self.env["res.users"]
        for user in users:
            if not user.active or user.share or not user.has_group(SCI_GROUP):
                continue
            as_candidate = self.with_user(user).with_context(allowed_company_ids=[])
            if as_candidate.has_access("read"):
                candidates |= user
        return candidates.sorted("name")

    @api.model
    def _sci_include_untriaged(self):
        return self.env["ir.config_parameter"].sudo().get_bool("sd_smart_chatter_inbox.include_untriaged")

    @api.model
    def _sci_base_domain(self):
        if self._sci_include_untriaged():
            return Domain.TRUE
        return Domain("sci_state", "!=", False)

    @api.model
    def _sci_build_domain(self, filters):
        """Translate whitelisted UI filters into a domain. Unknown keys are ignored."""
        filters = filters if isinstance(filters, dict) else {}
        now = fields.Datetime.now()
        domains = [self._sci_base_domain()]

        snoozed_expired = Domain("sci_state", "=", "snoozed") & Domain("sci_snooze_until", "<=", now)
        snoozed_active = Domain("sci_state", "=", "snoozed") & Domain("sci_snooze_until", ">", now)
        needs_action = Domain("sci_state", "in", [False, "needs_action"]) | snoozed_expired

        quick = filters.get("quick")
        if quick == "my":
            mine = Domain("sci_owner_id", "=", self.env.uid) | (
                Domain("sci_owner_id", "=", False) & Domain("user_id", "=", self.env.uid))
            domains += [mine, needs_action | Domain("sci_state", "=", "waiting")]
        elif quick == "needs_action":
            domains.append(needs_action)
        elif quick == "snoozed":
            domains.append(snoozed_active)
        elif quick in ("waiting", "done"):
            domains.append(Domain("sci_state", "=", quick))

        search = filters.get("search")
        if isinstance(search, str) and search.strip():
            term = search.strip()[:SCI_MAX_SEARCH]
            domains.append(
                Domain("name", "ilike", term) | Domain("partner_name", "ilike", term)
                | Domain("contact_name", "ilike", term) | Domain("partner_id", "ilike", term))

        owner_id = self._sci_to_int(filters.get("owner_id"))
        if owner_id:
            domains.append(Domain("sci_owner_id", "=", owner_id) | (
                Domain("sci_owner_id", "=", False) & Domain("user_id", "=", owner_id)))

        team_id = self._sci_to_int(filters.get("team_id"))
        if team_id:
            domains.append(Domain("team_id", "=", team_id))

        # Only companies already enabled for this user/session; anything else is ignored.
        company_id = self._sci_to_int(filters.get("company_id"))
        if company_id and company_id in self.env.companies.ids:
            domains.append(Domain("company_id", "=", company_id))

        if filters.get("lead_type") in SCI_LEAD_TYPES:
            domains.append(Domain("type", "=", filters["lead_type"]))

        return Domain.AND(domains)

    def _sci_serialize(self, field_names):
        """Plain-data rows built only from fields the user can read.

        Related record names are read in batch and only for records the user can access.
        """
        now = fields.Datetime.now()
        names = {}
        for fname in field_names:
            if self._fields[fname].type == "many2one":
                related = self[fname]._filtered_access("read")
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
            raise ValidationError(self.env._("Choose a valid snooze date and time."))
        if parsed <= fields.Datetime.now():
            raise ValidationError(self.env._("The snooze date and time must be in the future."))
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
