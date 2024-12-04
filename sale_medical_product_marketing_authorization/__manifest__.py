# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Medical Product Marketing Authorisation',
    'version': '16.0.1.0.0',
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'summary': 'Block sale of medical devices without valid marketing authorisation',
    'author': 'Akretion',
    'maintainers': ['alexis-via'],
    "development_status": "Mature",
    'website': 'https://github.com/akretion/vertical-implant',
    'depends': ['sale_commercial_partner'],
    'data': [
        'security/group.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/product.xml',
        'views/product_marketing_authorization.xml',
        'views/sale_order.xml',
    ],
    'installable': True,
}
