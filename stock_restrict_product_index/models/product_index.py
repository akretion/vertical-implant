# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductIndex(models.Model):
    _name = 'product.index'
    _description = "Product indexes"

    name = fields.Char()
    product_id = fields.Many2one("product.product")

    _sql_constraints = [
        ('product_index_name_product_uniq', 'unique(name, product_id)', 'Error, it is not possible to have 2 product indexes with the same name for a same product'),
    ]

