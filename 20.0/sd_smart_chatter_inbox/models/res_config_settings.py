from odoo import api, fields, models

from .crm_lead import SCI_AUTO_DETECT_OFF_PARAM


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sci_include_untriaged = fields.Boolean(
        string="Include untriaged leads in Smart Chatter Inbox",
        config_parameter="sd_smart_chatter_inbox.include_untriaged",
        help="When enabled, every active lead/opportunity you can access appears in the queue as "
        "Needs Action until it is triaged. When disabled, only leads with an explicit inbox status appear.",
    )
    # Stored inverted ("disable" parameter) so that detection is on when the parameter is absent.
    sci_auto_detect = fields.Boolean(
        string="Detect customer replies automatically",
        help="A customer email or message moves the lead to Needs Action and marks it Unanswered. "
        "A reply from your team moves it from Needs Action to Waiting. Internal notes are ignored.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        res["sci_auto_detect"] = not self.env["ir.config_parameter"].sudo().get_bool(SCI_AUTO_DETECT_OFF_PARAM)
        return res

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_bool(SCI_AUTO_DETECT_OFF_PARAM, not self.sci_auto_detect)
