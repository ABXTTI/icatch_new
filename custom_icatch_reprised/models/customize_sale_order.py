from odoo import api, models, fields
from odoo.exceptions import ValidationError
from datetime import date

class ProductTemplate(models.Model):
    _inherit = "product.template"
    x_is_units = fields.Boolean("Is Unit")
    x_is_ooh = fields.Boolean("Is OOH")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    purchase_order_ids = fields.One2many('purchase.order', 'x_origin', string="Purchase Orders")
    x_ntn = fields.Char(string="NTN", related="partner_id.vat")
    x_strn = fields.Char(string="STRN", related="partner_id.strn")
    x_mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    x_phone = fields.Char(string="Phone", related="partner_id.phone")
    x_email = fields.Char(string="Email", related="partner_id.email")
    x_campaign = fields.Many2one('ict.campaign', string="Campaign", required=False)


    @api.depends('x_campaign')
    def get_brand(self):
        self.x_brand = self.x_campaign.related_brand

    x_brand = fields.Many2one('ict.brand', string="Brand", compute='get_brand', store=True, required=True, readonly=False)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    po = fields.Boolean(string="PO")
    po_created = fields.Boolean(string="PO Created", default=False)
    x_uom = fields.Selection([('squarefeet', 'Sqr.Ft.'), ('inches', 'Inches'), ('ooh', 'OOH'), ('unit', 'Unit')], 'Measure', default='unit')
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
    i_medium_description = fields.Many2one('ict.medium.description', string="Medium Description")
    i_city = fields.Many2one('ict.city', string="City")
    i_shop = fields.Many2one('ict.shop', string="Location")
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
                if rec.x_uom == "squarefeet" or rec.x_uom == "ooh" or rec.x_uom == "unit":
                    rec.i_sqrfeet = rec.i_width * rec.i_height
                elif rec.x_uom == "inches":
                    rec.i_sqrfeet = (rec.i_width * rec.i_height)/144

    i_sqrfeet = fields.Float(string="Sqr.Feet", compute='compute_sqfeet', store=True)

    i_qty = fields.Float(string="Qty.ICT")

    @api.onchange('product_id')
    def on_product_change(self):
        for rec in self:
            rec.po_created = False
            rec.po = False
            rec.i_shop = ""
            rec.i_city = ""
            rec.i_medium_description = ""
            rec.i_mediadescription = ""
            rec.i_width = 1
            rec.i_height = 1
            if rec.product_id.x_is_units:
                rec.x_uom = "unit"
            elif rec.x_is_ooh:
                rec.x_uom = "ooh"
            else:
                rec.x_uom = "squarefeet"

    @api.depends('i_qty', 'i_sqrfeet', 'x_uom')
    def compute_total_qty(self):
        for rec in self:
            if rec.product_id.x_is_units or rec.x_is_ooh:
                rec.product_uom_qty = rec.i_qty * 1
                rec.i_totalsqrfeet = 1
            else:
                rec.product_uom_qty = rec.i_qty * rec.i_sqrfeet
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet

    product_uom_qty = fields.Float(string="Total Sqr.Feet/Qty", compute='compute_total_qty', store=True)
    i_totalsqrfeet = fields.Float(string="Total Sqr.ft./Qty.", compute='compute_total_qty', store=True)