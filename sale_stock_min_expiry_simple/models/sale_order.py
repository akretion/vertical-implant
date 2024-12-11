# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    product_expiry_min_days = fields.Integer(
        compute='_compute_product_expiry_min_days',
        string='Minimum Expiry', help="Minimum expiry in days.",
        store=True, readonly=False, precompute=True, tracking=True)

    @api.depends('partner_id', 'company_id')
    def _compute_product_expiry_min_days(self):
        for order in self:
            product_expiry_min_days = False
            if order.partner_id and order.company_id:
                product_expiry_min_days = order.with_company(order.company_id.id).partner_id.commercial_partner_id.product_expiry_min_days
            order.product_expiry_min_days = product_expiry_min_days

    _sql_constraints = [
        (
            'product_expiry_min_days_positive',
            'CHECK(product_expiry_min_days >= 0)',
            'The minimum expiry must be positive or null.')
        ]


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id=group_id)
        if self.order_id and self.order_id.product_expiry_min_days:
            if self.product_id.tracking in ('lot', 'serial') and self.product_id.use_expiry_date:
                vals["product_expiry_min_days"] = self.order_id.product_expiry_min_days
        return vals
