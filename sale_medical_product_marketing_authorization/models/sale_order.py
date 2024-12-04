# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    missing_marketing_authorization_products = fields.Char(
        compute='_compute_missing_marketing_authorization_products')

    @api.depends('partner_id', 'order_line.product_id')
    def _compute_missing_marketing_authorization_products(self):
        for order in self:
            disallowed_product_names = False
            if order.partner_id:
                auth_product_ids = order._sale_get_authorized_product_ids()
                disallowed_products = self.env['product.product']
                for line in order.order_line:
                    if (
                            line.product_id.marketing_authorization_required and
                            line.product_id.id not in auth_product_ids):
                        disallowed_products |= line.product_id
                if disallowed_products:
                    disallowed_product_names = ', '.join([(p.default_code or p.name) for p in disallowed_products])
            order.missing_marketing_authorization_products = disallowed_product_names

    def _action_confirm(self):
        for order in self:
            if order.missing_marketing_authorization_products:
                raise UserError(_(
                    "%(order)s cannot be confirmed because "
                    "the following products don't have a valid "
                    "marketing authorization: %(products)s.",
                    order=order.display_name,
                    products=order.missing_marketing_authorization_products))
        return super()._action_confirm()

    def _sale_get_authorized_product_ids(self, date=None):
        self.ensure_one()
        return self._get_authorized_product_ids(
            self.commercial_partner_id.id,
            self.commercial_partner_id.country_id.id,
            self.company_id.id,
            date=date)

    @api.model
    def _get_authorized_product_ids(self, commercial_partner_id, country_id, company_id, date=None):
        self.ensure_one()
        if date is None:
            date = fields.Date.context_today(self)
        domain = expression.AND([
            [('company_id', '=', company_id)],
            expression.OR([
                [('partner_id', '=', commercial_partner_id)],
                expression.AND([
                    [('partner_id', '=', False)],
                    [('country_ids', 'in', country_id)]
                    ])
                ])
            ])
        rules_partner_country = self.env['product.marketing.authorization'].search_read(
            domain, ['product_ids'])
        rules_partner_country_ids = [x['id'] for x in rules_partner_country]
        periods = self.env['product.marketing.authorization.period'].search_read([
            ('start_date', '<=', date),
            ('end_date', '>=', date),
            ('parent_id', 'in', rules_partner_country_ids),
            ], ['parent_id'])
        rules_partner_country_date_ids = [period['parent_id'][0] for period in periods]
        product_ids = set()
        for auth in rules_partner_country:
            if auth['id'] in rules_partner_country_date_ids:
                product_ids.update(auth['product_ids'])
        return list(product_ids)
