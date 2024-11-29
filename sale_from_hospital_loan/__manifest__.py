# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale From Hospital Loan',
    'version': '16.0.1.0.0',
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'summary': "Sale from hospital's remote stock (as a loan)",
    'author': 'Akretion',
    'maintainers': ['alexis-via'],
    "development_status": "Mature",
    'website': 'https://github.com/akretion/vertical-implant',
    'depends': ["sale_from_hospital_stock"],
    'data': [
        "views/res_partner.xml",
        "views/sale_order.xml",
    ],
    'installable': True,
}
