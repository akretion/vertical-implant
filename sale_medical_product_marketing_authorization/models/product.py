# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    marketing_authorization_required = fields.Boolean(
        string='Marketing Authorization Required',
        compute='_compute_marketing_authorization_required',
        store=True, readonly=False, precompute=True,
        help="If enabled, this product will require a marketing authorization to be sold.")

    @api.depends('type')
    def _compute_marketing_authorization_required(self):
        for product in self:
            if product.type in ('product', 'consu'):
                product.marketing_authorization_required = True
            else:
                product.marketing_authorization_required = False

    def show_marketing_authorizations(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale_medical_product_marketing_authorization.product_marketing_authorization_action")
        action['domain'] = [('product_ids', 'in', self.product_variant_ids.ids)]
        return action


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def show_marketing_authorizations(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale_medical_product_marketing_authorization.product_marketing_authorization_action")
        action['domain'] = [('product_ids', 'in', self.id)]
        return action
