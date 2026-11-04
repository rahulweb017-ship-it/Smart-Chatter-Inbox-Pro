from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sci_include_untriaged = fields.Boolean(
        string="Include untriaged leads in Smart Chatter Inbox",
        config_parameter="sd_smart_chatter_inbox.include_untriaged",
        help="When enabled, every active lead/opportunity you can access appears in the queue as "
        "Needs Action until it is triaged. When disabled, only leads with an explicit inbox status appear.",
    )
