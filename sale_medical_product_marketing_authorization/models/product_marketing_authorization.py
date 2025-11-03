# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date
from textwrap import shorten


class ProductMarketingAuthorization(models.Model):
    _name = 'product.marketing.authorization'
    _description = 'Product Marketing Authorization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    _check_company_auto = True

    sequence = fields.Integer()
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', ondelete='cascade', required=True, index=True,
        default=lambda self: self.env.company, tracking=True)
    ref = fields.Char(string="Reference", tracking=True, copy=False)
    partner_id = fields.Many2one(
        'res.partner', string='Distributor', ondelete='restrict', index=True, copy=False,
        domain=[('parent_id', '=', False), ('is_company', '=', True)], tracking=True,
        help="If empty, selling to any partner in the listed countries is allowed.")
    product_ids = fields.Many2many(
        'product.product', string='Products', required=True, tracking=True,
        domain=[('marketing_authorization_required', '=', True)],
        check_company=True)
    product_ids_str = fields.Char(compute="_compute_product_ids_str", string="Products as Text", store=True)
    country_ids = fields.Many2many(
        'res.country', string='Countries', required=True, tracking=True, copy=False)
    # country_ids_str is store=False because country name is translatable
    country_ids_str = fields.Char(compute="_compute_country_ids_str", string="Countries as Text", store=False)
    period_ids = fields.One2many(
        'product.marketing.authorization.period', 'parent_id',
        string='Periods', tracking=True, copy=False)
    duration_type = fields.Selection([
        ('period', 'Periods'),
        ('illimited', 'Illimited'),
        ], default='period', required=True, tracking=True)
    end_date = fields.Date(compute='_compute_end_date', store=True)
    notes = fields.Html(copy=False)

    @api.constrains('duration_type', 'period_ids')
    def _check_product_marketing_authorization(self):
        for auth in self:
            if auth.duration_type == 'illimited' and auth.period_ids:
                raise ValidationError(_(
                    "Product Marketing Authorization '%s' is configured "
                    "as illimited, so it should not have any period defined.")
                    % auth.display_name)

    @api.depends('product_ids.default_code', 'product_ids.name')
    def _compute_product_ids_str(self):
        for auth in self:
            product_list = [p.default_code or p.name for p in auth.product_ids]
            product_ids_str_full = ", ".join(product_list)
            auth.product_ids_str = shorten(product_ids_str_full, 60, placeholder='...')

    @api.depends('country_ids')
    def _compute_country_ids_str(self):
        country_id2name = {
            c['id']: c['name'] for c in self.env['res.country'].search_read([], ['name'])}
        for auth in self:
            country_list = [country_id2name[c_id] for c_id in auth.country_ids.ids]
            country_ids_str_full = ", ".join(country_list)
            auth.country_ids_str = shorten(country_ids_str_full, 50, placeholder='...')

    @api.depends('period_ids.end_date', 'duration_type')
    def _compute_end_date(self):
        for auth in self:
            end_date = False
            if auth.duration_type == 'period' and auth.period_ids:
                end_date = max([p.end_date for p in auth.period_ids])
            auth.end_date = end_date

    def copy_data(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = _("%s (copy)") % self.name
        return super().copy_data(default=default)

    # Enable tracking in chatter on M2M fields that have tracking=True
    # taken from https://www.odoo.com/fr_FR/forum/sales-4/how-to-add-tracking-for-many2many-field-odoo15-205288
    def _mail_track(self, tracked_fields, initial_values):
        updated_fields, tracking_value_ids = super()._mail_track(tracked_fields, initial_values)
        if len(updated_fields) > len(tracking_value_ids):
            for updated_field in updated_fields:
                if tracked_fields[updated_field]['type'] in ['one2many', 'many2many']:
                    field = self.env['ir.model.fields']._get(self._name, updated_field)
                    vals = {
                        'field': field.id,
                        'field_desc': field.field_description,
                        'field_type': field.ttype,
                        'tracking_sequence': field.tracking,
                        'old_value_char': ', '.join(initial_values[updated_field].mapped('display_name')),
                        'new_value_char': ', '.join(self[updated_field].mapped('display_name')),
                    }
                    tracking_value_ids.append(Command.create(vals))
        return updated_fields, tracking_value_ids

    @api.depends('product_ids_str', 'country_ids_str')
    def name_get(self):
        res = []
        for auth in self:
            dname = f"🚦 {auth.product_ids_str} 🌐 {auth.country_ids_str}"
            res.append((auth.id, dname))
        return res


class ProductMarketingAuthorizationPeriod(models.Model):
    _name = 'product.marketing.authorization.period'
    _description = 'Product Marketing Authorization Period'
    _order = 'parent_id, start_date desc'

    parent_id = fields.Many2one(
        'product.marketing.authorization', ondelete='cascade')
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @api.constrains('start_date', 'end_date', 'parent_id')
    def _check_periods(self):
        for period in self:
            if period.start_date and period.end_date and period.parent_id:
                if period.start_date > period.end_date:
                    raise ValidationError(_(
                        "The end date (%(end_date)s) must be after the start date (%(start_date)s).",
                        end_date=format_date(self.env, period.end_date),
                        start_date=format_date(self.env, period.start_date)))
                existing = self.search([
                    ('id', '!=', period.id),
                    ('parent_id', '=', period.parent_id.id),
                    ('end_date', '>=', period.start_date),
                    ('start_date', '<=', period.end_date),
                    ], limit=1)
                if existing:
                    raise ValidationError(_(
                        "An existing period (%(existing)s) conflicts with period %(period)s.",
                        existing=existing.display_name, period=period.display_name
                        ))

    def name_get(self):
        res = []
        for period in self:
            name = ''
            if period.start_date and period.end_date:
                name = f"{format_date(self.env, period.start_date)} → {format_date(self.env, period.end_date)}"
            res.append((period.id, name))
        return res
