import datetime
from odoo import api, models, fields
from odoo.exceptions import ValidationError
from datetime import date

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange('partner_id')
    def onchange_parnterid(self):
        self.x_brand = ""
        self.x_campaign = ""

    survey_ref = fields.Many2one("survey.sale.order", string="Survey Ref.")
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

    @api.onchange('x_brand')
    def onchange_brand(self):
        self.x_campaign = ""
        if not self.x_brand.parent_id:
            self.x_brand.parent_id = self.partner_id.id

    x_brand = fields.Many2one('ict.brand', string="Brand", store=True)



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    survey_ref = fields.Many2one("survey.sale.order", string="Survey ID", related="survey_line_id.survey_so_ref")
    survey_line_id = fields.Many2one("survey.sale.order.line", string="Survey Line ID")
    i_description = fields.Char(string="Description")
    map_link = fields.Char("MAP")
    x_uom = fields.Selection([('squarefeet', 'Sqr.Ft.'), ('inches', 'Inches')], 'Measure', default="")
    x_type = fields.Selection([('ooh', 'OOH'), ('unit', 'Unit')], 'Type')
    x_is_ooh = fields.Boolean(related="product_id.x_is_ooh")
    i_tentative_start_date = fields.Date(string="Tentative"
                                                "start Date")
    i_tentative_end_date = fields.Date(string="Tentative"
                                              "End Date")

    @api.depends('i_tentative_start_date', 'i_tentative_end_date')
    def cal_duration(self):
        print("Line Number -------- 58 -----------------")
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
        print("Line Number ------------ 87 -------------------")
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
            if rec.x_uom == "inches":
                rec.i_sqrfeet = rec.i_width * rec.i_height / 144
            else:
                rec.i_sqrfeet = rec.i_width * rec.i_height

    i_sqrfeet = fields.Float(string="Sqr.Feet", compute='compute_sqfeet', store=True)

    i_qty = fields.Float(string="Qty.ICT")

    @api.depends('i_qty', 'i_sqrfeet', 'x_uom')
    def compute_total_qty(self):
        for rec in self:
            if rec.x_type == "unit":
                rec.quantity = rec.i_qty * 1
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet
            elif rec.x_type == "ooh":
                rec.quantity = rec.i_qty * 1
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet
            else:
                rec.quantity = rec.i_qty * rec.i_sqrfeet
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet

    quantity = fields.Float(string="Total Sqr.Feet/Qty", compute='compute_total_qty')
    i_totalsqrfeet = fields.Float(string="Total Sqr.ft./Qty.", compute='compute_total_qty')

    @api.onchange('product_template_id')
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