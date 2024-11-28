# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockRoute(models.Model):
    _inherit = 'stock.route'

    detailed_type = fields.Selection([
        ('ship_from_deposit', 'Ship From Deposit')])
    partner_id = fields.Many2one(
        'res.partner', string='Partner', check_company=True,
        domain=[('parent_id', '=', False)], ondelete='restrict')

    @api.depends('detailed_type', 'partner_id')
    def _check_detailed_type(self):
        for route in self:
            if route.detailed_type == 'ship_from_deposit' and not route.partner_id:
                raise ValidationError(_(
                    "The route '%s' has a detailed type 'Ship From Deposit', "
                    "so a partner must be set.") % route.display_name)
