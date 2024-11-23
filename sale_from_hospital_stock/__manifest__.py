# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale From Hospital Stock',
    'version': '16.0.1.0.0',
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'summary': "Sale from hospital's remote stock",
    'author': 'Akretion',
    'maintainers': ['alexis-via'],
    "development_status": "Mature",
    'website': 'https://github.com/akretion/vertical-implant',
    'depends': ['sale_order_route', 'sale_commercial_partner'],
    'data': [
        'views/sale_order.xml',
        'views/res_partner.xml',
        'views/stock_route.xml',
        'views/stock_location.xml',
        'views/stock_picking.xml',
        'wizards/res_config_settings_view.xml',
    ],
    'installable': True,
}
