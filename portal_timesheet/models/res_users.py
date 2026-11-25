from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    portal_timesheet_enabled = fields.Boolean(
        string="Portal Time Entry",
        help="Allow this portal user to log time on tasks they follow or are "
        "assigned to.",
    )
