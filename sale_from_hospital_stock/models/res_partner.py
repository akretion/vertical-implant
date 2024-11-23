# @author: Alexis de Lattre <alexis.delattre@akretion.com>

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    deposit_route_id = fields.Many2one('stock.route', compute='_compute_deposit', string="Route de vente depuis dépôt")
    deposit_location_id = fields.Many2one('stock.location', compute='_compute_deposit', string="Dépôt")

    # depend on company
    @api.depends('deposit_route_id')
    @api.depends_context('company')
    def _compute_deposit(self):
        for partner in self:
            deposit_route = False
            deposit_location = False
            if not partner.parent_id:
                deposit_route = self.env['stock.route'].search([('partner_id', '=', partner.id), ('company_id', '=', self.env.company.id), ('ship_from_hospital_deposit', '=', True)], limit=1)
                if deposit_route and deposit_route.rule_ids and deposit_route.rule_ids[0].location_src_id and deposit_route.rule_ids[0].location_src_id.hospital:
                    deposit_location = deposit_route.rule_ids[0].location_src_id
            partner.deposit_route_id = deposit_route
            partner.deposit_location_id = deposit_location

    def button_create_deposit_route(self):
        self.ensure_one()
        assert not self.deposit_route_id
        assert not self.parent_id
        company = self.env.company
        if not company.deposit_stock_out_type_id:
            raise UserError(f"Type d'opération pour les ventes depuis dépôt non configuré sur la société {company.name}.")
        wh = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        if not wh:
            raise UserError("Aucun entrepôt dans la société %s." % company.display_name)
        # create location
        partner_name = self.name
        if self.ref:
            partner_name += f' {self.ref}'
        domain = [('company_id', '=', company.id), ('partner_id', '=', self.id)]
        existing_loc = self.env['stock.location'].search(domain + [('hospital', '=', True)], limit=1)
        if existing_loc:
            raise UserError(f"Un dépôt existe déjà pour le partenaire {self.display_name} : {existing_loc.display_name}.")
        loc_vals = {
            'name': f'Dépôt {partner_name}',
            'location_id': wh.view_location_id.id,
            'usage': 'internal',
            'company_id': company.id,
            'partner_id': self.id,
            'hospital': True,
            }
        deposit_location = self.env['stock.location'].create(loc_vals)
        self.message_post(
            body=f"Dépôt <a href=# data-oe-model=stock.location data-oe-id={deposit_location.id}>{deposit_location.display_name}</a> créé.")
        # create route
        existing_route = self.env['stock.route'].search(domain + [('ship_from_hospital_deposit', '=', True)], limit=1)
        if existing_route:
            raise UserError(f"Une route de vente depuis dépôt existe déjà pour le partenaire {self.display_name} : {existing_route.display_name}.")
        pull_rule_deposit = {
            'name': f'From deposit {partner_name} to customers',
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
            'name': 'Sale from hospital deposit %s' % partner_name,
            'company_id': company.id,
            'sequence': 40,
            'rule_ids': [Command.create(pull_rule_deposit)],
            'product_selectable': False,
            'product_categ_selectable': False,
            'warehouse_selectable': False,
            'sale_selectable': True,
            'partner_id': self.id,
            'ship_from_hospital_deposit': True,
            }
        deposit_route = self.env['stock.route'].create(deposit_route_vals)
        self.message_post(
            body=f"Route <a href=# data-oe-model=stock.route data-oe-id={deposit_route.id}>{deposit_route.display_name}</a> created.")
