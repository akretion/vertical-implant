# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)
from collections import defaultdict


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # inherit the field of sale_order_route
    route_id = fields.Many2one(
        domain="[('partner_id', 'in', (commercial_partner_id, False)), ('company_id', 'in', (company_id, False)), ('sale_selectable', '=', True)]")
    ship_from_hospital_deposit = fields.Boolean(related='route_id.ship_from_hospital_deposit', store=True)
    ship_from_hospital_loan = fields.Boolean(related='route_id.ship_from_hospital_loan', store=True)
    refill_deposit = fields.Boolean(
        default=True, string='Ré-approvisionnement du dépôt', tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    refill_picking_ids = fields.One2many(
        'stock.picking', 'refill_sale_id', string='Bons de réapprovisionnement du dépôt')
    refill_picking_count = fields.Integer(
        compute='_compute_refill_picking_count', string='Nb de bons de réapprovisionnement du dépôt')
    return_picking_ids = fields.One2many(
        'stock.picking', 'return_sale_id', string='Bons de retour du prêt')
    return_picking_count = fields.Integer(
        compute='_compute_return_picking_count', string='Nb de bons de retour du prêt')

    @api.depends('refill_picking_ids')
    def _compute_refill_picking_count(self):
        rg_res = self.env['stock.picking'].read_group(
            [('refill_sale_id', 'in', self.ids)], ['refill_sale_id'], ['refill_sale_id'])
        mapped_data = dict(
            [(x['refill_sale_id'][0], x['refill_sale_id_count']) for x in rg_res])
        for order in self:
            order.refill_picking_count = mapped_data.get(order.id, 0)

    def action_view_refill_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(self.refill_picking_ids) == 1:
            action.update({
                'res_id': self.refill_picking_ids.id,
                'view_id': False,
                'views': False,
                'view_mode': 'form,tree,kanban,calendar,pivot,graph,activity',
                })
        else:
            action['domain'] = [('id', 'in', self.refill_picking_ids.ids)]
        return action

    @api.depends('return_picking_ids')
    def _compute_return_picking_count(self):
        rg_res = self.env['stock.picking'].read_group(
            [('return_sale_id', 'in', self.ids)], ['return_sale_id'], ['return_sale_id'])
        mapped_data = dict(
            [(x['return_sale_id'][0], x['return_sale_id_count']) for x in rg_res])
        for order in self:
            order.return_picking_count = mapped_data.get(order.id, 0)

    def action_view_return_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(self.return_picking_ids) == 1:
            action.update({
                'res_id': self.return_picking_ids.id,
                'view_id': False,
                'views': False,
                'view_mode': 'form,tree,kanban,calendar,pivot,graph,activity',
                })
        else:
            action['domain'] = [('id', 'in', self.return_picking_ids.ids)]
        return action

    def _generate_refill_picking(self):
        self.ensure_one()
        assert self.route_id.ship_from_hospital_deposit or self.route_id.ship_from_hospital_loan
        spo = self.env['stock.picking']
        existing_refill_pickings = spo.search([
            ('state', 'not in', ('done', 'cancel')),
            ('refill_sale_id', '=', self.id),
            ])
        if existing_refill_pickings:
            raise UserError(
                "Il existe déjà des bons de transfert de ré-approvisionnement de "
                "dépôt (%s) liés à cette commande %s. "
                "Vous devez d'abord les annuler."
                % (', '.join([p.name for p in existing_refill_pickings]), self.name))
        company_id = self.company_id.id
        lot_stock_id = self.warehouse_id.lot_stock_id.id
        if self.ship_from_hospital_deposit:
            deposit_location = self.route_id.rule_ids[0].location_src_id
            assert deposit_location.company_id.id == company_id
            assert deposit_location.hospital
        elif self.ship_from_hospital_loan:
            deposit_location = self.warehouse_id.lot_stock_id
        move_ids = []
        origin = _('Refill deposit %s') % self.name
        for l in self.order_line.filtered(lambda x: not x.display_type and x.product_id.type == 'product'):
            move_ids.append(Command.create({
                'company_id': company_id,
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'product_uom': l.product_uom.id,
                'name': l.product_id.display_name,
                'location_id': lot_stock_id,
                'location_dest_id': deposit_location.id,
                'warehouse_id': self.warehouse_id.id,
                'origin': origin,
                }))
        picking = spo.create({
            'company_id': company_id,
            'partner_id': self.partner_shipping_id.id,
            "sale_id": False,
            "refill_sale_id": self.id,
            'origin': origin,
            "move_type": "direct",
            'location_id': lot_stock_id,
            'location_dest_id': deposit_location.id,
            'picking_type_id': self.warehouse_id.out_type_id.id,
            'move_ids': move_ids,
            })
        picking.action_confirm()

    def _generate_loan_return(self):
        self.ensure_one()
        assert self.route_id.ship_from_hospital_loan
        spo = self.env['stock.picking']
        existing_return_pickings = spo.search([
            ('state', 'not in', ('done', 'cancel')),
            ('return_sale_id', '=', self.id),
            ])
        if existing_return_pickings:
            raise UserError(
                "Il existe déjà des bons de transfert de retour de "
                "prêt (%s) liés à cette commande %s. "
                "Vous devez d'abord les annuler."
                % (', '.join([p.name for p in existing_return_pickings]), self.name))
        company_id = self.company_id.id
        loan_location = self.route_id.rule_ids[0].location_src_id
        lot_stock_id = self.warehouse_id.lot_stock_id.id
        move_ids = []
        origin = _('Return loan %s') % self.name
        location_content = self.env["stock.quant"].read_group(
            domain=[("location_id", "=", loan_location.id)],
            fields=[
                "product_id",
                "quantity:sum",
            ],
            groupby=["product_id"],
            orderby="id",
            lazy=False,
        )
        lines = self.env["sale.order.line"].read_group(
            domain=[
                ("order_id", "=", self.id),
                ("display_type", "=", False),
                ("product_id.type", "=", "product"),
            ],
            fields=[
                "product_id",
                "product_uom_qty:sum",
            ],
            groupby=["product_id"],
            orderby="id",
            lazy=False,
        )
        lines = defaultdict(float)
        for l in self.order_line.filtered(lambda x: not x.display_type and x.product_id.type == 'product'):
            lines[l.product_id.id] += l.product_uom_qty
        for group in location_content:
            product = self.env["product.product"].browse(group["product_id"][0]).exists()
            qty = group.get("quantity") - lines[product.id]
            if not qty:
                continue
            move_ids.append(Command.create({
                'company_id': company_id,
                'product_id': product.id,
                'product_uom_qty': qty,
                'product_uom': product.uom_id.id,
                'name': product.display_name,
                'location_id': loan_location.id,
                'location_dest_id': lot_stock_id,
                'warehouse_id': self.warehouse_id.id,
                'origin': origin,
                }))
        picking = spo.create({
            'company_id': company_id,
            'partner_id': self.partner_shipping_id.id,
            "sale_id": False,
            "return_sale_id": self.id,
            'origin': origin,
            "move_type": "direct",
            'location_id': loan_location.id,
            'location_dest_id': lot_stock_id,
            'picking_type_id': self.warehouse_id.int_type_id.id,
            'move_ids': move_ids,
            })
        picking.action_confirm()

    def _action_confirm(self):
        for order in self:
            if (order.ship_from_hospital_deposit or order.ship_from_hospital_loan) and order.refill_deposit:
                order._generate_refill_picking()
            if order.ship_from_hospital_loan:
                order._generate_loan_return()
        return super()._action_confirm()

    def _action_cancel(self):
        for order in self:
            for picking in order.refill_picking_ids:
                if picking.state not in ('done', 'cancel'):
                    picking.action_cancel()
        return super()._action_cancel()
