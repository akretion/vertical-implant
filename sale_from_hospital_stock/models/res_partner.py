# @author: Alexis de Lattre <alexis.delattre@akretion.com>

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    deposit_route_id = fields.Many2one('stock.route', compute='_compute_deposit', string="Route de vente depuis dépôt")
    loan_route_id = fields.Many2one('stock.route', compute='_compute_loan', string="Route de prêt")
    deposit_location_id = fields.Many2one('stock.location', compute='_compute_deposit', string="Dépôt")
    loan_location_id = fields.Many2one('stock.location', compute='_compute_load', string="Prêt")

    # depend on company
    @api.depends('deposit_route_id')
    @api.depends_context('company')
    def _compute_deposit(self):
        for partner in self:
            deposit_route = False
            deposit_location = False
            if not partner.parent_id:
                deposit_route = self.env['stock.route'].search([('partner_id', '=', partner.id), ('company_id', '=', self.env.company.id), ('ship_from_hospital_deposit', '=', True)], limit=1)
                if deposit_route and deposit_route.rule_ids and deposit_route.rule_ids[0].location_src_id and deposit_route.rule_ids[0].location_src_id.hospital_type == "deposit":
                    deposit_location = deposit_route.rule_ids[0].location_src_id
            partner.deposit_route_id = deposit_route
            partner.deposit_location_id = deposit_location

    @api.depends_context('company')
    def _compute_loan(self):
        for partner in self:
            loan_route = False
            loan_location = False
            if not partner.parent_id:
                loan_route = self.env['stock.route'].search([('partner_id', '=', partner.id), ('company_id', '=', self.env.company.id), ('ship_from_hospital_loan', '=', True)], limit=1)
                if loan_route and loan_route.rule_ids and loan_route.rule_ids[0].location_src_id and loan_route.rule_ids[0].location_src_id.hospital_type == "loan":
                    loan_location = loan_route.rule_ids[0].location_src_id
            partner.loan_route_id = loan_route
            partner.loan_location_id = loan_location

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
        existing_loc = self.env['stock.location'].search(domain + [('hospital_type', '=', 'deposit')], limit=1)
        if existing_loc:
            raise UserError(f"Un dépôt existe déjà pour le partenaire {self.display_name} : {existing_loc.display_name}.")
        loc_vals = {
            'name': f'Dépôt {partner_name}',
            'location_id': wh.view_location_id.id,
            'usage': 'internal',
            'company_id': company.id,
            'partner_id': self.id,
            'hospital_type': 'deposit',
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
        import pdb; pdb.set_trace();
        deposit_delivery_picking_type = self.env["stock.picking.type"].create({
            "name": f"Send Deposit to hospital - {partner_name}",
            "code": "internal",
            "sequence_code": "DEP/" + ((self.ref and self.ref.upper()) or (self.name and self.name[:3].upper())),
            "warehouse_id": deposit_location.warehouse_id.id,
            "show_entire_packs": True,
            "default_location_src_id": deposit_location.warehouse_id.lot_stock_id.id,
            "default_location_dest_id": deposit_location.id,
        })
        self.message_post(
            body=f"Picking Type <a href=# data-oe-model=stock.picking.type data-oe-id={deposit_delivery_picking_type.id}>{deposit_delivery_picking_type.name}</a> created.")

    def button_create_loan_route(self):
        self.ensure_one()
        assert not self.loan_route_id
        assert not self.parent_id
        company = self.env.company
        if not company.loan_stock_out_type_id:
            raise UserError(f"Type d'opération pour les ventes depuis un prêt non configuré sur la société {company.name}.")
        wh = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        if not wh:
            raise UserError("Aucun entrepôt dans la société %s." % company.display_name)
        # create location
        partner_name = self.name
        if self.ref:
            partner_name += f' {self.ref}'
        domain = [('company_id', '=', company.id), ('partner_id', '=', self.id)]
        existing_loc = self.env['stock.location'].search(domain + [('hospital_type', '=', 'loan')], limit=1)
        if existing_loc:
            raise UserError(f"Un emplacement prêt existe déjà pour le partenaire {self.display_name} : {existing_loc.display_name}.")
        loc_vals = {
            'name': f'Prêt {partner_name}',
            'location_id': wh.view_location_id.id,
            'usage': 'internal',
            'company_id': company.id,
            'partner_id': self.id,
            'hospital_type': "loan",
            }
        loan_location = self.env['stock.location'].create(loc_vals)
        self.message_post(
            body=f"Prêt <a href=# data-oe-model=stock.location data-oe-id={loan_location.id}>{loan_location.display_name}</a> créé.")
        # create route
        existing_route = self.env['stock.route'].search(domain + [('ship_from_hospital_loan', '=', True)], limit=1)
        if existing_route:
            raise UserError(f"Une route de vente depuis dépôt existe déjà pour le partenaire {self.display_name} : {existing_route.display_name}.")
        pull_rule_loan = {
            'name': f'From loan {partner_name} to customers',
            'company_id': company.id,
            'warehouse_id': False,
            'action': 'pull',
            'location_src_id': loan_location.id,
            'location_dest_id': self.property_stock_customer.id,
            'procure_method': 'make_to_stock',
            'picking_type_id': company.loan_stock_out_type_id.id,
            'partner_address_id': self.id,
            }
        loan_route_vals = {
            'name': 'Sale from hospital loan %s' % partner_name,
            'company_id': company.id,
            'sequence': 40,
            'rule_ids': [Command.create(pull_rule_loan)],
            'product_selectable': False,
            'product_categ_selectable': False,
            'warehouse_selectable': False,
            'sale_selectable': True,
            'partner_id': self.id,
            'ship_from_hospital_loan': True,
            }
        loan_route = self.env['stock.route'].create(loan_route_vals)
        self.message_post(
            body=f"Route <a href=# data-oe-model=stock.route data-oe-id={loan_route.id}>{loan_route.display_name}</a> created.")
        loan_delivery_picking_type = self.env["stock.picking.type"].create({
            "name": f"Send Loan to hospital - {partner_name}",
            "code": "internal",
            "sequence_code": "DEP/" + ((self.ref and self.ref.upper()) or (self.name and self.name[:3].upper())),
            "warehouse_id": loan_location.warehouse_id.id,
            "show_entire_packs": True,
            "default_location_src_id": loan_location.warehouse_id.lot_stock_id.id,
            "default_location_dest_id": loan_location.id,
        })
        self.message_post(
            body=f"Picking Type <a href=# data-oe-model=stock.picking.type data-oe-id={loan_delivery_picking_type.id}>{loan_delivery_picking_type.name}</a> created.")
