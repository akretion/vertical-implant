# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_expiry_min_days = fields.Integer(
        string='Minimum Expiry', help="Minimum expiry in days.")
    product_use_expiry_date = fields.Boolean(
        related='product_id.use_expiry_date', string="Product Has an Expiry Date")

    # inspired by stock_restrict_lot
    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals["product_expiry_min_days"] = self.product_expiry_min_days
        return vals

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append("product_expiry_min_days")
        return distinct_fields

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        # inject stock move ID in context
        self = self.ensure_one()
        return super(StockMove, self.with_context(min_expiry_simple_stock_move_id=self.id))._update_reserved_quantity(need, available_quantity, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)

    def _split(self, qty, restrict_partner_id=False):
        vals_list = super()._split(qty, restrict_partner_id=restrict_partner_id)
        if vals_list and self.product_expiry_min_days:
            vals_list[0]["product_expiry_min_days"] = self.product_expiry_min_days
        return vals_list
