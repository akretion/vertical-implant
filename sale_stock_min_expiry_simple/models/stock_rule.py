# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    # inspired by stock_restrict_lot
    def _get_custom_move_fields(self):
        # Used to create stock.move from procurement
        fields = super()._get_custom_move_fields()
        fields += ["product_expiry_min_days"]
        return fields

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        new_move_vals = super()._push_prepare_move_copy_values(move_to_copy, new_date)
        new_move_vals["product_expiry_min_days"] = move_to_copy.product_expiry_min_days
        return new_move_vals
