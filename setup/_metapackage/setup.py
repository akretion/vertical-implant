import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-akretion-vertical-implant",
    description="Meta package for akretion-vertical-implant Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-sale_from_hospital_stock>=16.0dev,<16.1dev',
        'odoo-addon-sale_medical_product_marketing_authorization>=16.0dev,<16.1dev',
        'odoo-addon-sale_stock_min_expiry_simple>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
