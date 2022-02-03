import datetime

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from datetime import date

class SurveySaleOrder(models.Model):
    _name = "survey.sale.order"
    _description = "Create Survey Sale Order/Quotation"

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: 'New')
    survey_date = fields.Date(string="Survey Date", default=datetime.datetime.today())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    partner_id = fields.Many2one("res.partner", string="Customer")
    x_ntn = fields.Char(string="NTN", related="partner_id.vat")
    x_strn = fields.Char(string="STRN", related="partner_id.strn")
    x_mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    x_phone = fields.Char(string="Phone", related="partner_id.phone")
    x_email = fields.Char(string="Email", related="partner_id.email")
    x_brand = fields.Many2one("ict.brand", string="Brand")
    x_campaign = fields.Many2one("ict.campaign", string="Campaign", required=True)
    note = fields.Text(string="Note")
    survey_lines = fields.One2many("survey.sale.order.line", "survey_so_ref", string="Survey Lines")

    def compute_untaxed_amount(self):
        sum = 0
        tax = 0
        for rec in self.survey_lines:
            sum += rec.price_subtotal
            if rec.tax_id.amount_type == "percent":
                tax += rec.tax_id.amount * rec.price_subtotal / 100
            elif rec.tax_id.amount_type == "division":
                tax += rec.tax_id.amount * rec.price_subtotal / (100 + rec.tax_id.amount)
                sum = sum - tax

        self.amount_untaxed = sum
        self.amount_tax = tax
        self.amount_total = sum + tax

    amount_untaxed = fields.Float(string="Untaxed Amount", compute="compute_untaxed_amount")
    amount_tax = fields.Float(string="Taxes", compute="compute_untaxed_amount")
    amount_total = fields.Float(string="Total", compute="compute_untaxed_amount")

    def action_confirm(self):
        self.state = "confirm"

    def action_reset(self):
        self.state = "draft"

    def action_create_sale_order(self):
        lines = self.survey_lines
        order_lines = self.env['sale.order.line']
        sale_order = self.env['sale.order']
        list = []
        for rec in lines:
            exist = order_lines.search([('survey_line_id', '=', rec.id)])
            if not exist and rec.approve:
                vals = {
                        'product_id': rec.product_template_id.id,
                        'i_shop': rec.i_shop.id,
                        'i_description': rec.i_description,
                        # 'name': rec.i_description,
                        'i_city': rec.i_city.id,
                        'i_mediadescription': rec.i_mediadescription.id,
                        'i_medium_description': rec.i_medium_description.id,
                        'x_type': rec.x_type,
                        'x_uom': rec.x_uom,
                        'i_width': rec.i_width,
                        'i_qty': rec.i_qty,
                        'price_unit': rec.price_unit,
                        'tax_id': rec.tax_id,
                        'map_link': rec.map_link,
                        'i_tentative_start_date': rec.i_tentative_start_date,
                        'i_tentative_end_date': rec.i_tentative_end_date,
                        'survey_line_id': rec.id,
                        }
                list.append((0, 0, vals))
                rec.so_created = True
        print(list)
        if list:
            sale_order.create({
                'partner_id': self.partner_id.id,
                'x_brand': self.x_brand.id,
                'x_campaign': self.x_campaign.id,
                'survey_ref': self.id,
                'order_line': list,
            })
        print("*********************Function Execution Completed******************************88")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('survey.sale.order.sequence') or 'New'

        result = super(SurveySaleOrder, self).create(vals)
        return result

class SurveySaleOrderLine(models.Model):
    _name = "survey.sale.order.line"

    approve = fields.Boolean(string="Approve")
    so_created = fields.Boolean(string="Created")
    survey_so_ref = fields.Many2one("survey.sale.order", "Survey Ref")
    i_shop = fields.Many2one("ict.shop", string="Location")
    i_description = fields.Char(string="Description")
    product_template_id = fields.Many2one("product.template", string="Product", required=True)

    @api.onchange('product_template_id')
    def on_product_change(self):
        for rec in self:
            rec.i_medium_description = ""
            rec.i_mediadescription = ""
            if rec.product_template_id.x_is_units:
                rec.x_type = "unit"
                rec.x_uom = ""
            elif rec.product_template_id.x_is_ooh:
                rec.x_type = "ooh"
            else:
                rec.x_uom = "squarefeet"
                rec.x_type = ""

    i_city = fields.Many2one("ict.city", string="City")
    i_mediadescription = fields.Many2one("ict.media.description", string="Media Description")
    i_medium_description = fields.Many2one("ict.medium.description", string="Medium Description")
    x_type = fields.Selection([
        ('ooh', 'OOH'),
        ('unit', 'Unit'),
    ], string='Type', readonly=True, copy=False, index=True, tracking=3, default="")
    x_uom = fields.Selection([
        ('squarefeet', 'Sqr.Ft.'),
        ('inches', 'Inches'),
    ], string='Measure')
    i_width = fields.Float(string="Width")
    i_height = fields.Float(string="Height")
    i_sqrfeet = fields.Float(string="Sqr.Feet", compute="cal_sqrfeet")

    @api.depends('i_width', 'i_height')
    def cal_sqrfeet(self):
        for rec in self:
            rec.i_sqrfeet = rec.i_width * rec.i_height

    i_qty = fields.Float(string="Qty")

    @api.depends('i_qty', 'i_sqrfeet', 'x_uom')
    def compute_total_qty(self):
        for rec in self:
            if rec.x_type == "unit":
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet
            elif rec.x_type == "ooh":
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet
            else:
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet

    i_totalsqrfeet = fields.Float(string="Total Sqrft./Qty", compute="compute_total_qty")
    product_uom = fields.Many2one("uom.uom", string="UoM")
    price_unit = fields.Float(string="Unit Price")
    tax_id = fields.Many2one("account.tax", string="Taxes")
    price_subtotal = fields.Float(string="Subtotal", compute="cal_subtotal")

    @api.depends('price_unit', 'i_totalsqrfeet')
    def cal_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.i_totalsqrfeet * rec.price_unit

    map_link = fields.Char(string="MAP")
    i_tentative_start_date = fields.Date(string="TentativeStart Date")
    i_tentative_end_date = fields.Date(string="TentativeEnd Date")
    i_duration = fields.Float(string="Duration", readonly=True)