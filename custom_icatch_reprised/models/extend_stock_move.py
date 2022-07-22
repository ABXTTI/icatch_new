from odoo import models, fields, api
import json
import time
from ast import literal_eval
from collections import defaultdict
from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date

class StockMove(models.Model):
    _inherit = "stock.move"

    i_shop = fields.Many2one("ict.shop", string="Location")
    i_description = fields.Char(string="Description")
    i_city = fields.Many2one("ict.city", string="City")
    i_mediadescription = fields.Many2one("ict.media.description", string="Media Description")
    i_medium_description = fields.Many2one("ict.medium.description", string="Medium Description")

    i_width = fields.Float(string="Width")
    i_height = fields.Float(string="Height")
    i_sqrfeet = fields.Float(string="Sqr.Feet", compute="cal_sqrfeet")

    @api.depends('i_width', 'i_height')
    def cal_sqrfeet(self):
        for rec in self:
            rec.i_sqrfeet = rec.i_width * rec.i_height

    i_qty = fields.Float(string="Qty")
    i_totalsqrfeet = fields.Float(string="Total Sqrft./Qty")
    map_link = fields.Char(string="MAP")


class StockPicking(models.Model):
    _inherit = "stock.picking"


    def auto_assign_serial_numbers(self):
        if self.picking_type_id.code == "incoming":
            lines = self.move_ids_without_package
            for rec in lines:
                if rec.product_id.tracking == 'lot':
                    if rec.product_id.is_roll and not rec.move_line_nosuggest_ids:
                        sr = list(range(0,int(rec.i_qty)))
                        print(sr)

                        qty_set = rec.product_uom_qty / rec.i_qty
                        if rec.i_totalsqrfeet != rec.product_uom_qty:
                            raise ValidationError("Total Square Feet / Liter and Quantity doesn't Match")
                        records = []
                        for record in sr:
                            records.append((0, 0 ,{
                                                    'product_id': rec.product_id.id,
                                                    'location_id': rec.location_id.id,
                                                    'product_uom_id': rec.product_id.uom_po_id.id if rec.product_id.uom_po_id else rec.product_id.uom_id.id,
                                                    'picking_id': rec.picking_id.id,
                                                    'move_id': rec.id,
                                                    'location_dest_id': rec.location_dest_id.id,
                                                    'lot_name': rec.picking_id.origin + "-W-" + str(rec.i_width) + "-" + str(record+1),
                                                    'qty_done': qty_set
                                            }))
                        print(records)
                        rec.move_line_nosuggest_ids = records



    #overringing button_validate function
    def button_validate(self):
        self.auto_assign_serial_numbers()
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)
        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()
        return True