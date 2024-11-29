# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class StockLocation(models.Model):
    _inherit = 'stock.location'

    detailed_usage = fields.Selection(selection_add=[
        ('loan', 'Hospital Loan')])

    def _detailed_usage_mapping(self):
        res = super()._detailed_usage_mapping()
        res["loan"] = "internal"
        return res
