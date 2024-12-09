# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    min_expiry_raise = fields.Boolean(
        string='Block if under Minimum Expiry',
        help="If this option is enabled, Odoo will raise an error upon picking "
        "validation if the selected lot is under the minimum expiry.")
