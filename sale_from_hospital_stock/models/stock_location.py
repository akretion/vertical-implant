# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    # Inspired by detailed_type from product.template... but a bit different because not required
    detailed_usage = fields.Selection([
        ('deposit', 'Deposit')], string="Detailed Location Type")
    usage = fields.Selection(compute="_compute_usage", store=True, readonly=False, precompute=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner', check_company=True,
        domain=[('parent_id', '=', False)], ondelete='restrict')

    def _detailed_usage_mapping(self):
        return {
            "deposit": "internal",
            }

    @api.depends('detailed_usage')
    def _compute_usage(self):
        usage_mapping = self._detailed_usage_mapping()
        for location in self:
            if location.detailed_usage:
                location.usage = usage_mapping[location.detailed_usage]
