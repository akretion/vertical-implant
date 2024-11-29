# @author: Alexis de Lattre <alexis.delattre@akretion.com>

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loan_route_id = fields.Many2one('stock.route', compute='_compute_loan', string="Route de prêt")
    loan_location_id = fields.Many2one('stock.location', compute='_compute_loan', string="Prêt")

    @api.depends_context('company')
    def _compute_loan(self):
        for partner in self:
            loan_route = False
            loan_location = False
            if not partner.parent_id:
                loan_route = self.env['stock.route'].search([('partner_id', '=', partner.id), ('company_id', '=', self.env.company.id), ('detailed_type', '=', "ship_from_loan")], limit=1)
                if loan_route and loan_route.rule_ids and loan_route.rule_ids[0].location_src_id and loan_route.rule_ids[0].location_src_id.detailed_usage == "loan":
                    loan_location = loan_route.rule_ids[0].location_src_id
            partner.loan_route_id = loan_route
            partner.loan_location_id = loan_location

    def button_create_loan_route(self):
        self.ensure_one()
        assert not self.loan_route_id
        assert not self.parent_id
        company = self.env.company
        if not company.deposit_stock_out_type_id:
            raise UserError(f"Type d'opération pour les ventes depuis un hôpital non configuré sur la société {company.name}.")
        wh = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        if not wh:
            raise UserError("Aucun entrepôt dans la société %s." % company.display_name)
        # create location
        partner_name = self.name
        if self.ref:
            partner_name += f' {self.ref}'
        domain = [('company_id', '=', company.id), ('partner_id', '=', self.id)]
        existing_loc = self.env['stock.location'].search(domain + [('detailed_usage', '=', 'loan')], limit=1)
        if existing_loc:
            raise UserError(f"Un emplacement prêt existe déjà pour le partenaire {self.display_name} : {existing_loc.display_name}.")
        loc_vals = {
            'name': f'Prêt {partner_name}',
            'location_id': wh.view_location_id.id,
            'usage': 'internal',
            'company_id': company.id,
            'partner_id': self.id,
            'detailed_usage': "loan",
            }
        loan_location = self.env['stock.location'].create(loc_vals)
        self.message_post(
            body=f"Prêt <a href=# data-oe-model=stock.location data-oe-id={loan_location.id}>{loan_location.display_name}</a> créé.")
        # create route
        existing_route = self.env['stock.route'].search(domain + [('detailed_type', '=', "ship_from_loan")], limit=1)
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
            'picking_type_id': company.deposit_stock_out_type_id.id,
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
            'detailed_type': "ship_from_loan",
            }
        loan_route = self.env['stock.route'].create(loan_route_vals)
        self.message_post(
            body=f"Route <a href=# data-oe-model=stock.route data-oe-id={loan_route.id}>{loan_route.display_name}</a> created.")
