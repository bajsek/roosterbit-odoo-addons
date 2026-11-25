from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _load_pos_data_models(self, config_id):
        data = super()._load_pos_data_models(config_id)
        if self.config_id.module_pos_restaurant:
            data += ["pos.table.reservation"]
        return data
