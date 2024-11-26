# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    deposit_stock_out_type_id = fields.Many2one(
        'stock.picking.type', string='Opération de stock pour vente depuis dépôt',
        ondelete='restrict', check_company=True)
    loan_stock_out_type_id = fields.Many2one(
        'stock.picking.type', string='Opération de stock pour vente depuis prêt',
        ondelete='restrict', check_company=True)
