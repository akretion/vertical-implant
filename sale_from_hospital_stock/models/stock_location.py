# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    hospital_type = fields.Selection(selection=[('deposit', "Dépôt"), ('loan', 'Prêt')], string='Hospital Location')
    partner_id = fields.Many2one(
        'res.partner', string='Partner', check_company=True,
        domain=[('parent_id', '=', False)], ondelete='restrict')

    @api.constrains('hospital_type', 'usage')
    def _check_hospital_type(self):
        for loc in self:
            if loc.hospital_type and loc.usage != 'internal':
                raise ValidationError(_(
                    "For stock location '%s', the option 'Hospital Type' is enabled "
                    "although it is not an internal location.") % loc.display_name)
