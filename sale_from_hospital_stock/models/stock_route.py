# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockRoute(models.Model):
    _inherit = 'stock.route'

    ship_from_hospital_deposit = fields.Boolean()
    ship_from_hospital_loan = fields.Boolean()
    partner_id = fields.Many2one(
        'res.partner', string='Partner', check_company=True,
        domain=[('parent_id', '=', False)], ondelete='restrict')

    @api.depends('ship_from_hospital_deposit', 'partner_id')
    def _check_ship_from_hospital_deposit(self):
        for route in self:
            if route.ship_from_hospital_deposit and not route.partner_id:
                raise ValidationError(_(
                    "The route '%s' is a route 'Ship From Hospital Deposit', "
                    "so a partner must be set.") % route.display_name)

    @api.depends('ship_from_hospital_loan', 'partner_id')
    def _check_ship_from_hospital_loan(self):
        for route in self:
            if route.ship_from_hospital_loan and not route.partner_id:
                raise ValidationError(_(
                    "The route '%s' is a route 'Ship From Hospital Loan', "
                    "so a partner must be set.") % route.display_name)
