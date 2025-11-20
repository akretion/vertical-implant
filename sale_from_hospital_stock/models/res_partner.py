# @author: Alexis de Lattre <alexis.delattre@akretion.com>

from odoo import api, fields, models, Command
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)


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
                deposit_location = deposit_route.rule_ids.location_src_id.filtered(lambda loc: loc.detailed_usage == 'deposit')
            partner.deposit_route_id = deposit_route
            partner.deposit_location_id = deposit_location

    def _prepare_hospital_stock_location_vals(self):
        self.ensure_one()
        company = self.env.company
        parent_location = company.deposit_main_location_id
        if not company.deposit_main_location_id:
            wh = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
            if not wh:
                raise UserError(self.env._("There is no warehouse in company %s.") % company.display_name)
            parent_location = wh.view_location_id
        vals = {
            'name': self.env._('Deposit %s') % self.display_name,
            'location_id': parent_location.id,
            'detailed_usage': 'deposit',
            'usage': 'internal',
            'company_id': company.id,
            'partner_id': self.id,
            }
        return vals

    def _prepare_refill_rule_vals_list(self, deposit_location):
        wh = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        # The main rule always exists
        refill_rule_main_vals = self._prepare_refill_rule_first_step_vals(deposit_location, wh)
        rule_vals_list = [refill_rule_main_vals]
        # second step is optional (only in case of pick+ship
        refill_rule_second_step_vals = self._prepare_refill_rule_second_step(deposit_location, wh)
        if refill_rule_second_step_vals:
            rule_vals_list.append(refill_rule_second_step_vals)
        # third step is optional (onlu in case of pick+pack+ship)
        refill_rule_third_step_vals = self._prepare_refill_rule_third_step(deposit_location, wh)
        if refill_rule_third_step_vals:
            rule_vals_list.append(refill_rule_third_step_vals)
        return rule_vals_list

    def _prepare_refill_rule_first_step_vals(self, deposit_location, wh):
        refill_rule_deposit_vals = {
            "name": self.env._("Refill deposit %(partner_name)s", partner_name=self.display_name),
            "company_id": self.env.company.id,
            "warehouse_id": wh.id,
            "action": "pull",
            "location_src_id": wh.lot_stock_id.id,
            "location_dest_id": deposit_location.id,
            "procure_method": "make_to_stock",
        }
        if wh.delivery_steps == "ship_only":
            refill_rule_deposit_vals["picking_type_id"] = wh.out_type_id.id
        else:
            refill_rule_deposit_vals["picking_type_id"] = wh.pick_type_id.id
        return refill_rule_deposit_vals

    def _prepare_refill_rule_second_step(self, deposit_location, wh):
        second_step_vals = False
        if wh.delivery_steps == "pick_ship": 
            second_step_vals = {
                "name": self.env._("output => deposit %(partner_name)s", partner_name=self.name),
                "company_id": self.env.company.id,
                "warehouse_id": wh.id,
                "action": "push",
                "location_src_id": wh.wh_output_stock_loc_id.id,
                "location_dest_id": deposit_location.id,
                "picking_type_id": wh.out_type_id.id,
            }
        # in case of pick_pack_ship, the second rule is in fact fully generic
        # and should already be available and global, that is why we do not create it
        # (output => packing)
        return second_step_vals

    def _prepare_refill_rule_third_step(self, deposit_location, wh):
        third_step_vals = False
        if wh.delivery_steps == "pick_pack_ship": 
            third_step_vals = {
                "name": self.env._("output => deposit %(partner_name)s", partner_name=self.name),
                "company_id": self.env.company.id,
                "warehouse_id": wh.id,
                "action": "push",
                "location_src_id": wh.wh_pack_stock_loc_id.id,
                "location_dest_id": deposit_location.id,
                "picking_type_id": wh.out_type_id.id,
            }
        return third_step_vals

            


    def _prepare_hospital_stock_route_vals(self, deposit_location):
        company = self.env.company
        rules_vals_list = [{
            'name': self.env._('From %s to Customers') % self.display_name,
            'company_id': company.id,
            'warehouse_id': False,
            'action': 'pull',
            'location_src_id': deposit_location.id,
            'location_dest_id': self.property_stock_customer.id,
            'procure_method': 'make_to_stock',
            'picking_type_id': company.deposit_stock_out_type_id.id,
            'partner_address_id': self.id,
            }]
        rules_vals_list += self._prepare_refill_rule_vals_list(deposit_location)
        deposit_route_vals = {
            'name': self.env._('Ship from %s') % deposit_location.display_name,
            'company_id': company.id,
            'sequence': 40,
            'rule_ids': [Command.create(vals) for vals in rules_vals_list],
            'product_selectable': False,
            'product_categ_selectable': False,
            'warehouse_selectable': False,
            'sale_selectable': True,
            'partner_id': self.id,
            'detailed_type': 'ship_from_deposit',
            }
        return deposit_route_vals

    def button_create_deposit_route(self):
        self.ensure_one()
        assert not self.deposit_route_id
        assert not self.parent_id
        company = self.env.company
        if not company.deposit_stock_out_type_id:
            raise UserError(self.env._("Picking Type for Orders from Deposit is not configured on company %s.") % company.name)
        # create location
        domain = [('company_id', '=', company.id), ('partner_id', '=', self.id)]
        existing_loc = self.env['stock.location'].search(domain + [('detailed_usage', '=', 'deposit')], limit=1)
        if existing_loc:
            raise UserError(self.env._("A deposit already exists for partner %(partner)s: %(location)s.", partner=self.display_name, location=existing_loc.display_name))
        loc_vals = self._prepare_hospital_stock_location_vals()
        deposit_location = self.env['stock.location'].create(loc_vals)
        logger.info('Deposit location created %s ID %d', deposit_location.display_name, deposit_location.id)
        self.message_post(
            body=self.env._("Deposit <a href=# data-oe-model=stock.location data-oe-id=%(location_id)s>%(location_name)s</a> created.", location_id=deposit_location.id, location_name=deposit_location.display_name))
        # create route
        existing_route = self.env['stock.route'].search(domain + [('detailed_type', '=', 'ship_from_deposit')], limit=1)
        if existing_route:
            raise UserError(self.env._("A route to ship from deposit already exists for partner %(partner)s: %(route)s.", partner=self.display_name, route=existing_route.display_name))
        deposit_route_vals = self._prepare_hospital_stock_route_vals(deposit_location)
        deposit_route = self.env['stock.route'].create(deposit_route_vals)
        logger.info('Deposit route created %s ID %d', deposit_route.display_name, deposit_route.id)
        self.message_post(
            body=self.env._("Route <a href=# data-oe-model=stock.route data-oe-id=%(route_id)s>%(route_name)s</a> created.", route_id=deposit_route.id, route_name=deposit_route.display_name))
