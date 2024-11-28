# @author: Alexis de Lattre <alexis.delattre@akretion.com>

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    deposit_route_id = fields.Many2one('stock.route', compute='_compute_deposit', string="Route for Orders from Deposit")
    deposit_location_id = fields.Many2one('stock.location', compute='_compute_deposit', string="Deposit")

    # depend on company
    @api.depends_context('company')
    def _compute_deposit(self):
        for partner in self:
            deposit_route = False
            deposit_location = False
            if not partner.parent_id:
                deposit_route = self.env['stock.route'].search([('partner_id', '=', partner.id), ('company_id', '=', self.env.company.id), ('detailed_type', '=', 'ship_from_deposit')], limit=1)
                if deposit_route and deposit_route.rule_ids and deposit_route.rule_ids[0].location_src_id and deposit_route.rule_ids[0].location_src_id.detailed_usage == 'deposit':
                    deposit_location = deposit_route.rule_ids[0].location_src_id
            partner.deposit_route_id = deposit_route
            partner.deposit_location_id = deposit_location

    def button_create_deposit_route(self):
        self.ensure_one()
        assert not self.deposit_route_id
        assert not self.parent_id
        company = self.env.company
        if not company.deposit_stock_out_type_id:
            raise UserError(_("Picking Type for Orders from Deposit is not configured on company %s.") % company.name)
        wh = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        if not wh:
            raise UserError(_("There is no warehouse in company %s.") % company.display_name)
        # create location
        partner_name = self.name
        if self.ref:
            partner_name += f' {self.ref}'
        domain = [('company_id', '=', company.id), ('partner_id', '=', self.id)]
        existing_loc = self.env['stock.location'].search(domain + [('detailed_usage', '=', 'deposit')], limit=1)
        if existing_loc:
            raise UserError(_("A deposit already exists for partner %(partner)s: %(location)s.", partner=self.display_name, location=existing_loc.display_name))
        loc_vals = {
            'name': _('Deposit %s') % partner_name,
            'location_id': wh.view_location_id.id,
            'detailed_usage': 'deposit',
            'usage': 'internal',
            'company_id': company.id,
            'partner_id': self.id,
            }
        deposit_location = self.env['stock.location'].create(loc_vals)
        self.message_post(
            body=_("Deposit <a href=# data-oe-model=stock.location data-oe-id=%(location_id)s>%(location_name)s</a> created.", location_id=deposit_location.id, location_name=deposit_location.display_name))
        # create route
        existing_route = self.env['stock.route'].search(domain + [('detailed_type', '=', 'ship_from_deposit')], limit=1)
        if existing_route:
            raise UserError(_("A route for sale from deposit already exists for partner %(partner)s: %(route)s.", partner=self.display_name, route=existing_route.display_name))
        pull_rule_deposit = {
            'name': _('From %s to Customers') % self.display_name,
            'company_id': company.id,
            'warehouse_id': False,
            'action': 'pull',
            'location_src_id': deposit_location.id,
            'location_dest_id': self.property_stock_customer.id,
            'procure_method': 'make_to_stock',
            'picking_type_id': company.deposit_stock_out_type_id.id,
            'partner_address_id': self.id,
            }
        deposit_route_vals = {
            'name': _('Ship from %s') % loc_vals['name'],
            'company_id': company.id,
            'sequence': 40,
            'rule_ids': [Command.create(pull_rule_deposit)],
            'product_selectable': False,
            'product_categ_selectable': False,
            'warehouse_selectable': False,
            'sale_selectable': True,
            'partner_id': self.id,
            'detailed_type': 'ship_from_deposit',
            }
        deposit_route = self.env['stock.route'].create(deposit_route_vals)
        self.message_post(
            body=_("Route <a href=# data-oe-model=stock.route data-oe-id=%(route_id)s>%(route_name)s</a> created.", route_id=deposit_route.id, route_name=deposit_route.display_name))
