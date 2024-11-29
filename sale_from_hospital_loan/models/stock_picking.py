# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    return_sale_id = fields.Many2one('sale.order', string='Sale Order which Triggers the Return', check_company=True, readonly=True)
