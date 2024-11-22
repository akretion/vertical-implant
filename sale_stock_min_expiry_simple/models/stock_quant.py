# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from datetime import timedelta


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _get_gather_domain(self, product, location, lot_id=None, package_id=None, owner_id=None, strict=False):
        domain = super()._get_gather_domain(product, location, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        if product.tracking == 'lot' and product.use_expiry_date and self._context.get('min_expiry_simple_stock_move_id'):
            move = self.env['stock.move'].browse(self._context['min_expiry_simple_stock_move_id'])
            assert move.product_id == product
            if move.sale_line_id and move.sale_line_id.order_id and move.location_dest_id.usage == "customer":
                expiry_date_min = fields.Date.context_today(self) + timedelta(move.sale_line_id.order_id.product_expiry_min_days)
                domain.append(('expiry_date', '>=', expiry_date_min))
        return domain
