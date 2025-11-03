# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductMarketingAuthorizationEnable(models.TransientModel):
    _name = "product.marketing.authorization.enable"
    _description = "Enable Marketing Authorization on Product"

    product_template_id = fields.Many2one("product.template", string="Product", required=True, readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_model') == "product.product":
            product = self.env['product.product'].browse(self._context.get('active_id'))
            template = product.product_tmpl_id
            res['product_template_id'] = product.product_tmpl_id.id
        elif self._context.get('active_model') == "product.template":
            template = self.env['product.template'].browse(self._context.get('active_id'))
            res['product_template_id'] = template.id
        if template.marketing_authorization_required:
            raise UserError(_("Marketing Authorization is already enabled on product '%s'.") % template.display_name)
        if template.type not in ('product', 'consu'):
            raise UserError(_(
                "You cannot enable a Marketing Authorization for '%s' "
                "because it is a service product.") % template.display_name)
        return res

    def run(self):
        self.ensure_one()
        if self.product_template_id.type not in ('product', 'consu'):
            raise UserError(_(
                "You cannot enable a Marketing Authorization for '%s' "
                "because it is a service product.") % self.product_template_id.display_name)
        self.product_template_id.write({'marketing_authorization_required': True})
        msg = _("Marketing Authorization enabled.")
        self.product_template_id.message_post(body=msg)
        for product in self.product_template_id.product_variant_ids:
            product.message_post(body=msg)
