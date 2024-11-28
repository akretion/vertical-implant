# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # inherit the field of sale_order_route
    route_id = fields.Many2one(
        domain="[('partner_id', 'in', (commercial_partner_id, False)), ('company_id', 'in', (company_id, False)), ('sale_selectable', '=', True)]")
    route_detailed_type = fields.Selection(related='route_id.detailed_type', store=True)
    refill_deposit = fields.Boolean(
        default=True, string='Refill Deposit', tracking=True,
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    refill_picking_ids = fields.One2many(
        'stock.picking', 'refill_sale_id', string='Refill Deposit Pickings')
    refill_picking_count = fields.Integer(
        compute='_compute_refill_picking_count', string='Number of Refill Deposit Pickings')

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

    def _generate_refill_picking(self):
        self.ensure_one()
        assert self.route_id.detailed_type == 'ship_from_deposit'
        spo = self.env['stock.picking']
        existing_refill_pickings = spo.search([
            ('state', 'not in', ('done', 'cancel')),
            ('refill_sale_id', '=', self.id),
            ])
        if existing_refill_pickings:
            raise UserError(_(
                "Refill deposit pickings (%(pickings)s) linked to order %(order)s already exists. "
                "You must cancel them and try again.",
                pickings=', '.join([p.name for p in existing_refill_pickings]),
                order=self.name))
        company_id = self.company_id.id
        lot_stock_id = self.warehouse_id.lot_stock_id.id
        deposit_location = self.route_id.rule_ids[0].location_src_id
        assert deposit_location.company_id.id == company_id
        assert deposit_location.detailed_usage == 'deposit'
        move_ids = []
        picking_origin = self.name
        if self.client_order_ref:
            picking_origin = f"{self.name} / {self.client_order_ref}"
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
                'origin': _('Refill Deposit %s') % self.name,
                }))
        picking = spo.create({
            'company_id': company_id,
            'partner_id': self.partner_shipping_id.id,
            "sale_id": False,
            "refill_sale_id": self.id,
            'origin': picking_origin,
            "move_type": "direct",
            'location_id': lot_stock_id,
            'location_dest_id': deposit_location.id,
            'picking_type_id': self.warehouse_id.out_type_id.id,
            'move_ids': move_ids,
            })
        picking.action_confirm()

    def _action_confirm(self):
        for order in self:
            if order.route_detailed_type == 'ship_from_deposit' and order.refill_deposit:
                order._generate_refill_picking()
        return super()._action_confirm()

    def _action_cancel(self):
        for order in self:
            for picking in order.refill_picking_ids:
                if picking.state not in ('done', 'cancel'):
                    picking.action_cancel()
        return super()._action_cancel()
