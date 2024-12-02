# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock Restrict Product Index',
    'version': '16.0.1.0.0',
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'summary': 'Restrict reservation of specific lot depending on its product index',
    'author': 'Akretion',
    'maintainers': ['florian-dacosta'],
    "development_status": "Alpha",
    'website': 'https://github.com/akretion/vertical-implant',
    'depends': ['sale_stock'],
    'data': [
        "security/ir.model.access.csv",
        "views/sale_order.xml",
        "views/stock_picking.xml",
        "views/stock_move.xml",
        "views/product_index.xml",
        "views/stock_lot.xml",
    ],
    'installable': True,
}
