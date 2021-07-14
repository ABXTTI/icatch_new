from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class ProductTemplate(models.Model):
    _inherit = "product.template"
    x_is_units = fields.Boolean("Is Unit")
    x_is_ooh = fields.Boolean("Is OOH")
    x_is_mediadescription = fields.Boolean("Is Media Description", default=False)
    x_is_medium_description = fields.Boolean("Is Medium Description", defualt=False)


# class MrpBomLine(models.Model):
#     _inherit = "mrp.bom.line"
#
#     x_is_mediadescription = fields.Boolean(string="Is Media Description", related="product_id.x_is_mediadescription")
#     x_is_medium_description = fields.Boolean("Is Medium Description", related="product_id.x_is_medium_description")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('partner_id')
    def onchange_parnterid(self):
        self.x_brand = ""
        self.x_campaign = ""

    purchase_order_ids = fields.One2many('purchase.order', 'x_origin', string="Purchase Orders")
    x_ntn = fields.Char(string="NTN", related="partner_id.vat")
    x_strn = fields.Char(string="STRN", related="partner_id.strn")
    x_mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    x_phone = fields.Char(string="Phone", related="partner_id.phone")
    x_email = fields.Char(string="Email", related="partner_id.email")

    @api.onchange('x_campaign')
    def onchange_campaign(self):
        if not self.x_campaign.related_brand:
            self.x_campaign.related_brand = self.x_brand.id
        if not self.x_campaign.related_customer:
            self.x_campaign.related_customer = self.partner_id.id

    x_campaign = fields.Many2one('ict.campaign', string="Campaign", required=False)


    # @api.depends('x_campaign')
    # def get_brand(self):
    #     self.x_brand = self.x_campaign.related_brand

    @api.onchange('x_brand')
    def onchange_brand(self):
        self.x_campaign = ""
        if not self.x_brand.parent_id:
            self.x_brand.parent_id = self.partner_id.id

    x_brand = fields.Many2one('ict.brand', string="Brand", store=True, required=True, readonly=False)

    # ######################### Create BOM ###############################################
    def action_confirm(self):
        for rec in self.order_line:
            is_manufacture = rec.product_id.route_ids.search([('name', '=', "Manufacture")])
            if is_manufacture:
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', rec.product_id.id)])
                if bom_id:
                    line_ids = bom_id.bom_line_ids
                    if line_ids:
                        for line in line_ids:
                            if line.product_id.x_is_mediadescription or line.product_id.x_is_medium_description:
                                line.unlink()
                    if not rec.po:
                        if rec.i_mediadescription and rec.i_medium_description:
                            lines = []
                            product = self.env['product.product'].search(
                                [('name', '=', rec.i_medium_description.name)])
                            if product:
                                lines.append((0, 0, {'product_id': product.id}))
                            product1 = self.env['product.product'].search(
                                [('name', '=', rec.i_mediadescription.name)])
                            if product1:
                                lines.append((0, 0, {'product_id': product1.id}))

                            bom_id.bom_line_ids = lines
                    if rec.po:
                        if rec.i_mediadescription and rec.i_medium_description:
                            lines = []
                            product = self.env['product.product'].search(
                                [('name', '=', rec.i_mediadescription.name)])
                            if product:
                                lines.append((0, 0, {'product_id': product.id}))

                            bom_id.bom_line_ids = lines
                else:
                    bom = self.env['mrp.bom']
                    bom.create({
                        'product_tmpl_id': rec.product_id.id,
                    })
                    if not rec.po:
                        if rec.i_mediadescription and rec.i_medium_description:
                            lines = []
                            product = self.env['product.product'].search(
                                [('name', '=', rec.i_medium_description.name)])
                            if product:
                                lines.append((0, 0, {'product_id': product.id}))
                            product1 = self.env['product.product'].search(
                                [('name', '=', rec.i_mediadescription.name)])
                            if product1:
                                lines.append((0, 0, {'product_id': product1.id}))

                            bom_id.bom_line_ids = lines
                    if rec.po:
                        if rec.i_mediadescription and rec.i_medium_description:
                            lines = []
                            product = self.env['product.product'].search(
                                [('name', '=', rec.i_mediadescription.name)])
                            if product:
                                lines.append((0, 0, {'product_id': product.id}))

                            bom_id.bom_line_ids = lines


        # ######################################################
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    map_link = fields.Char("MAP")
    po = fields.Boolean(string="PO")
    po_created = fields.Boolean(string="PO Created", default=False)
    x_uom = fields.Selection([('squarefeet', 'Sqr.Ft.'), ('inches', 'Inches')], 'Measure', default="")
    x_type = fields.Selection([('ooh', 'OOH'), ('unit', 'Unit')], 'Type')
    x_is_ooh = fields.Boolean(related="product_id.x_is_ooh")
    i_tentative_start_date = fields.Date(string="Tentative"
                                                "start Date")
    i_tentative_end_date = fields.Date(string="Tentative"
                                                "End Date")
    @api.depends('i_tentative_start_date', 'i_tentative_end_date')
    def cal_duration(self):
        for rec in self:
            if rec.i_tentative_start_date and rec.i_tentative_end_date:
                if rec.i_tentative_start_date > rec.i_tentative_end_date:
                    raise ValidationError("Start Date cannot be earlier than End Date!!!!!!")
                else:
                    delta = rec.i_tentative_end_date - rec.i_tentative_start_date
                    print(type(delta))
                    rec.i_duration = delta.days + 1

    i_duration = fields.Float(string="Duration", compute="cal_duration", store=True)
    i_lamination = fields.Boolean(string="Lamination")
    i_fabrication = fields.Boolean(string="Fabrination")

    @api.onchange('i_medium_description')
    def onchange_i_mediumdescription(self):
        # print("111111111111111111111111111111111111111111111111")
        if not self.product_id and self.i_medium_description.related_product:
            raise ValidationError("Please Select Product First.")
        else:
            if not self.i_medium_description.related_product:
                self.i_medium_description.related_product = self.product_id.id
                print("33333333333333333333333333333333333333333333")
    i_medium_description = fields.Many2one('ict.medium.description', string="Medium Description")
    i_city = fields.Many2one('ict.city', string="City")
    i_shop = fields.Many2one('ict.shop', string="Location")

    @api.onchange('i_mediadescription')
    def onchange_i_mediadescription(self):
        print("111111111111111111111111111111111111111111111111")
        if not self.product_id and self.i_mediadescription.related_product:
            raise ValidationError("Please Select Product First.")
        else:
            if not self.i_mediadescription.related_product:
                self.i_mediadescription.related_product = self.product_id.id
                print("33333333333333333333333333333333333333333333")

    i_mediadescription = fields.Many2one('ict.media.description', string="Media Description")
    i_printer = fields.Many2one('ict.printer', string="Printer")
    i_resolution = fields.Many2one('ict.resolution', string="Resolution")
    i_inktype = fields.Many2one('ict.ink.type', string="Ink Type")
    i_size = fields.Char(string="Size")
    i_width = fields.Float(string="Width", default=1)
    i_height = fields.Float(string="Height", default=1)

    @api.depends('i_width', 'i_height', 'x_uom')
    def compute_sqfeet(self):
        for rec in self:
            if rec.x_uom:
                if rec.x_uom == "squarefeet":
                    rec.i_sqrfeet = rec.i_width * rec.i_height
                elif rec.x_uom == "inches":
                    rec.i_sqrfeet = (rec.i_width * rec.i_height)/144

    i_sqrfeet = fields.Float(string="Sqr.Feet", compute='compute_sqfeet', store=True)

    i_qty = fields.Float(string="Qty.ICT")

    @api.onchange('product_id')
    def on_product_change(self):
        for rec in self:
            rec.i_medium_description = ""
            rec.i_mediadescription = ""
            if rec.product_id.x_is_units:
                rec.x_type = "unit"
                rec.x_uom = ""
            elif rec.x_is_ooh:
                rec.x_type = "ooh"
            else:
                rec.x_uom = "squarefeet"
                rec.x_type = ""

    @api.depends('i_qty', 'i_sqrfeet', 'x_uom')
    def compute_total_qty(self):
        for rec in self:
            if rec.x_type == "unit":
                rec.product_uom_qty = rec.i_qty * 1
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet
            elif rec.x_type == "ooh":
                rec.product_uom_qty = rec.i_qty * 1
                # rec.product_uom_qty = rec.i_duration
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet
            else:
                rec.product_uom_qty = rec.i_qty * rec.i_sqrfeet
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet

    product_uom_qty = fields.Float(string="Total Sqr.Feet/Qty", compute='compute_total_qty', store=True)
    i_totalsqrfeet = fields.Float(string="Total Sqr.ft./Qty.", compute='compute_total_qty', store=True)