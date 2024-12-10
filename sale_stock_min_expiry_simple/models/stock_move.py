# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date
from datetime import timedelta


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
        self = self.ensure_one()
        # inject stock move ID in context
        return super(StockMove, self.with_context(min_expiry_simple_stock_move_id=self.id))._update_reserved_quantity(need, available_quantity, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)

    def _get_available_quantity(
            self, location_id, lot_id=None, package_id=None, owner_id=None,
            strict=False, allow_negative=False):
        self = self.ensure_one()
        # inject stock move ID in context
        return super(StockMove, self.with_context(min_expiry_simple_stock_move_id=self.id))._get_available_quantity(location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict, allow_negative=allow_negative)

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        self._check_min_expiry()
        return res

    def _check_min_expiry(self):
        for move in self:
            if (
                    move.picking_id and
                    move.picking_id.picking_type_id.min_expiry_raise and
                    move.product_expiry_min_days and
                    move.product_id.use_expiry_date):
                today = fields.Date.context_today(self)
                # at that step, the stock.move.line with qty_done=0 have already been deleted
                for move_line in move.move_line_ids:
                    if not move_line.lot_id:
                        raise UserError(_(
                            "Picking %(picking)s: missing lot for product '%(product)s'.",
                            product=move.product_id.display_name,
                            picking=move.picking_id.display_name
                            ))
                    if not move_line.lot_id.expiry_date:
                        raise UserError(_(
                            "Picking %(picking)s: missing expiry date on lot %(lot)s "
                            "for product '%(product)s'.",
                            lot=move_line.lot_id.display_name,
                            product=move.product_id.display_name,
                            picking=move.picking_id.display_name))
                    limit_date = today + timedelta(move.product_expiry_min_days)
                    if move_line.lot_id.expiry_date < limit_date:
                        raise UserError(_(
                            "Picking %(picking)s: you cannot select lot %(lot)s "
                            "for product '%(product)s' because the stock move is "
                            "configured with a minimum expiry delay of "
                            "%(min_expiry_days)s days, so the minimum expiry date "
                            "is %(min_expiry_date)s.",
                            lot=move_line.lot_id.display_name,
                            product=move.product_id.display_name,
                            min_expiry_days=move.product_expiry_min_days,
                            min_expiry_date=format_date(self.env, limit_date),
                            picking=move.picking_id.display_name))
