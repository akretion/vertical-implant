# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    hospital = fields.Boolean('Hospital Deposit')
    partner_id = fields.Many2one(
        'res.partner', string='Partner', check_company=True,
        domain=[('parent_id', '=', False)], ondelete='restrict')

    @api.constrains('hospital', 'usage')
    def _check_hospital(self):
        for loc in self:
            if loc.hospital and loc.usage != 'internal':
                raise ValidationError(_(
                    "For stock location '%s', the option 'Hospital Deposit' is enabled "
                    "although it is not an internal location.") % loc.display_name)
