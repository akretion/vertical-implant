# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    refill_sale_id = fields.Many2one('sale.order', string='Sale Order which Triggers the Refill', check_company=True, readonly=True)
