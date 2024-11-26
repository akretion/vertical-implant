# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    refill_sale_id = fields.Many2one('sale.order', string='Sale Order which Triggers the Refill', check_company=True, readonly=True)
    return_sale_id = fields.Many2one('sale.order', string='Sale Order which Triggers the Return', check_company=True, readonly=True)
    # for delivery report
    source_sale_id = fields.Many2one('sale.order', compute='_compute_source_sale_id')

    @api.depends('refill_sale_id', 'sale_id')
    def _compute_source_sale_id(self):
        for picking in self:
            picking.source_sale_id = picking.refill_sale_id or picking.sale_id
