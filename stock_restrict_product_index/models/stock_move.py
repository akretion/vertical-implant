# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    restrict_index_ids = fields.Many2many("product.index")

    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals["restrict_index_ids"] = [(6, 0, self.restrict_index_ids.ids)]
        return vals

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append("restrict_index_ids")
        return distinct_fields

    def _get_available_quantity(
        self,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
        allow_negative=False,
    ):
        self.ensure_one()
        index_ids = False
        if self.restrict_index_ids:
            index_ids = self.restrict_index_ids.ids
        return super(StockMove, self.with_context(product_index_ids=index_ids))._get_available_quantity(
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
            allow_negative=allow_negative,
        )

    def _update_reserved_quantity(
        self,
        need,
        available_quantity,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=True,
    ):
        self.ensure_one()
        index_ids = False
        if self.restrict_index_ids:
            index_ids = self.restrict_index_ids.ids
        return super(StockMove, self.with_context(product_index_ids=index_ids))._update_reserved_quantity(
            need,
            available_quantity,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

    def _split(self, qty, restrict_partner_id=False):
        vals_list = super()._split(qty, restrict_partner_id=restrict_partner_id)
        if vals_list and self.restrict_index_ids:
            vals_list[0]["restrict_index_ids"] = [(6, 0, self.restrict_index_ids.ids)]
        return vals_list

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        self._check_product_index_consistent_with_restriction()
        return res

    def _check_product_index_consistent_with_restriction(self):
        """
        Check that the lot set on move lines
        is the same as the restricted lot set on the move
        """
        for move in self:
            if not (move.restrict_index_ids and move.move_line_ids):
                continue
            move_line_index = move.mapped("move_line_ids.lot_id.index_id")
            if move.restrict_index_ids and move_line_index not in move.restrict_index_ids:
                raise UserError(
                    _(
                        "The lot(s) %(move_line_lot)s being moved is "
                        "inconsistent with the restriction on "
                        "product indexes %(move_restrict_index)s set on the move",
                        move_line_lot=", ".join(move.move_line_ids.lot_id.mapped("display_name")),
                        move_restrict_index=move.restrict_index_ids.mapped('display_name'),
                    )
                )

