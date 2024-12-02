# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    kit_creation_type_id = fields.Many2one(
        'stock.picking.type', string='Picking Type To create of complete the kits',
        ondelete='restrict', check_company=True)
