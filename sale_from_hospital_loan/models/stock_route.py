# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockRoute(models.Model):
    _inherit = 'stock.route'

    detailed_type = fields.Selection(selection_add=[
        ("ship_from_loan", "Ship From Hospital Loan")])

    @api.depends('detailed_type', 'partner_id')
    def _check_detailed_type(self):
        for route in self:
            if route.detailed_type == 'ship_from_deposit' and not route.partner_id:
                raise ValidationError(_(
                    "The route '%s' is a route 'Ship From Hospital Loan', "
                    "so a partner must be set.") % route.display_name)
        return super()._check_detailed_type()
