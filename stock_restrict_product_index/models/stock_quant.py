# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from datetime import timedelta


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    index_id = fields.Many2one("product.index", related="lot_id.index_id", store=True, index="btree")

    def _get_gather_domain(self, product, location, lot_id=None, package_id=None, owner_id=None, strict=False):
        domain = super()._get_gather_domain(product, location, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        if product.tracking == 'lot' and self._context.get('product_index_ids'):
            domain.append(('index_id', 'in', self._context['product_index_ids']))
        return domain
