from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        fields = super()._get_custom_move_fields()
        fields += ["restrict_index_ids"]
        return fields

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        values = super()._push_prepare_move_copy_values(move_to_copy, new_date)
        values["restrict_index_ids"] = [(6, 0, move_to_copy.restrict_index_ids.ids)]
        return values
