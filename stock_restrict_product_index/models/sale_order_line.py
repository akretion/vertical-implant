# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_index_ids = fields.Many2many(
        "product.index",
        string="Indices de plan",
        copy=False,
        compute="_compute_product_index_ids",
        store=True,
        readonly=False,
    )

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id=group_id)
        if self.product_index_ids:
            vals["restrict_index_ids"] = [(6, 0, self.product_index_ids.ids)]
        return vals

    @api.depends("product_id")
    def _compute_product_index_ids(self):
        for sol in self:
            if sol.product_id != sol.product_index_ids.product_id:
                sol.product_index_ids = [(6, 0, [])]
