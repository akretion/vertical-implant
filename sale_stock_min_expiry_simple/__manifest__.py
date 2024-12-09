# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Stock Min Expiry Simple',
    'version': '16.0.1.0.0',
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'summary': 'Per-order configuration of a minimum expiry delay',
    'author': 'Akretion',
    'maintainers': ['alexis-via'],
    "development_status": "Mature",
    'website': 'https://github.com/akretion/vertical-implant',
    'depends': ['sale_stock', 'product_expiry_simple'],
    'data': [
        'views/sale_order.xml',
        'views/stock_move.xml',
        'views/stock_picking.xml',
        'views/res_partner.xml',
        'views/stock_picking_type.xml',
    ],
    'installable': True,
}
