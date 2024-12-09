============================
Sale Stock Min Expiry Simple
============================

This module is useful for companies that sell products with expiry dates. These companies usually configure FEFO (First Expiry First Out) as reservation method for their stocks. But, for some specific customers, they sometimes have contracts that require them to deliver products that have at least N days before expiry.

With this module, you can configure a minimum expiry delay (in days) on the partner. This information is copied on the sale orders of that partner (and can be modified on the sale order). When the sale order is confirmed, Odoo will only reserve products whose expiry date is after the minimum number of days configured on the sale order.

If the option **Block if under Minimum Expiry** is enabled on the operation type, Odoo will raise an error upon picking validation if the selected lot is under the minimum expiry (to block users that selected lots other than those reserved by Odoo and that selected a lot under the minimum expiry).

Installation
============

This module depends on the OCA module **product_expiry_simple** from `OCA/stock-logistics-workflow <https://github.com/OCA/stock-logistics-workflow>`_.

Credits
=======

Authors
~~~~~~~

* Akretion

Contributors
~~~~~~~~~~~~

* Alexis de Lattre <alexis.delattre@akretion.com>
