import datetime

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from datetime import date

class SurveySaleOrder(models.Model):
    _name = "survey.sale.order"
    _description = "Create Survey Sale Order/Quotation"

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: 'New')
    survey_date = fields.Date(string="Survey Date", default=datetime.datetime.today())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    partner_id = fields.Many2one("res.partner", string="Customer")
    client_order_ref = fields.Char(string="Customer PO#")
    x_ntn = fields.Char(string="NTN", related="partner_id.vat")
    x_strn = fields.Char(string="STRN", related="partner_id.strn")
    x_mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    x_phone = fields.Char(string="Phone", related="partner_id.phone")
    x_email = fields.Char(string="Email", related="partner_id.email")

    @api.onchange('x_brand')
    def onchange_brand(self):
        self.x_campaign = ""
        if not self.x_brand.parent_id:
            self.x_brand.parent_id = self.partner_id.id

    x_brand = fields.Many2one("ict.brand", string="Brand", required=True)

    @api.onchange('x_campaign')
    def onchange_campaign(self):
        if not self.x_campaign.related_brand:
            self.x_campaign.related_brand = self.x_brand.id
        if not self.x_campaign.related_customer:
            self.x_campaign.related_customer = self.partner_id.id
        if self.x_campaign.name:
            analytic_account_object = self.env['account.analytic.account']
            analytic_account_exist = analytic_account_object.search([('name', '=', self.x_campaign.name)])
            if analytic_account_exist:
                self.analytic_account_id = analytic_account_exist.id
            else:
                new = analytic_account_object.create({'name': self.x_campaign.name})
                self.analytic_account_id = new.id

    x_campaign = fields.Many2one("ict.campaign", string="Campaign")
    note = fields.Text(string="Note")
    survey_lines = fields.One2many("survey.sale.order.line", "survey_so_ref", string="Survey Lines Sale Order To Be Created:", domain=[["so_created", "=", 0]])
    survey_sale_created_lines = fields.One2many("survey.sale.order.line", 'survey_so_ref', string="Survey Lines Sale Order Created:", domain=[["so_created", "=", 1]])

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
                        'i_height': rec.i_height,
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
            so = sale_order.create({
                'partner_id': self.partner_id.id,
                'client_order_ref': self.client_order_ref,
                'x_brand': self.x_brand.id,
                'x_campaign': self.x_campaign.id,
                'survey_ref': self.id,
                'analytic_account_id': self.analytic_account_id.id,
                'order_line': list,
                })
            return {
                'name': "action_quotations_with_onboarding",
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'target': 'existing',
                # 'domain': "[('po_created', '!=', True), ('so_ref', '=', %s)]" % id,
                'views': False,
                'res_id': so.id,
                'context': "{}",
            }
        print("*********************Function Execution Completed******************************88")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('survey.sale.order.sequence') or 'New'

        result = super(SurveySaleOrder, self).create(vals)
        return result

    def write(self, vals):
        rtn = super(SurveySaleOrder, self).write(vals)
        for rec in self.survey_lines:
            var = str(rec.map_link)
            if var:
                if "https://www.google.com/search?q=" not in var:
                    rec.map_link = "https://www.google.com/search?q=" + var
        return rtn

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

    @api.onchange('i_mediadescription')
    def onchange_i_mediadescription(self):
        # print("111111111111111111111111111111111111111111111111")
        if not self.product_template_id and self.i_mediadescription.related_product:
            raise ValidationError("Please Select Product First.")
        else:
            if not self.i_mediadescription.related_product:
                self.i_mediadescription.related_product = self.product_template_id.id
                # print("33333333333333333333333333333333333333333333")
    i_mediadescription = fields.Many2one("ict.media.description", string="Media Description")

    @api.onchange('i_medium_description')
    def onchange_i_mediumdescription(self):
        # print("111111111111111111111111111111111111111111111111")
        if not self.product_template_id and self.i_medium_description.related_product:
            raise ValidationError("Please Select Product First.")
        else:
            if not self.i_medium_description.related_product:
                self.i_medium_description.related_product = self.product_template_id.id
                # print("33333333333333333333333333333333333333333333")
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

    @api.depends('i_width', 'i_height', 'x_uom')
    def compute_sqfeet(self):
        for rec in self:
            if rec.x_uom == "inches":
                rec.i_sqrfeet = rec.i_width * rec.i_height / 144
            else:
                rec.i_sqrfeet = rec.i_width * rec.i_height

    i_sqrfeet = fields.Float(string="Sqr.Feet", compute="compute_sqfeet")
    i_qty = fields.Float(string="Qty")

    @api.depends('i_qty', 'i_sqrfeet', 'x_uom')
    def compute_total_qty(self):
        for rec in self:
            if rec.x_type == "unit":
                rec.i_totalsqrfeet = rec.i_qty * 1
            elif rec.x_type == "ooh":
                rec.i_totalsqrfeet = rec.i_qty * 1
            else:
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet

    i_totalsqrfeet = fields.Float(string="Total Sqrft./Qty", compute="compute_total_qty")
    product_uom = fields.Many2one("uom.uom", string="UoM")
    price_unit = fields.Float(string="Unit Price")
    tax_id = fields.Many2one("account.tax", string="Taxes")
    price_subtotal = fields.Float(string="Subtotal", compute="cal_subtotal")

    @api.depends('price_unit', 'i_totalsqrfeet', 'i_duration')
    def cal_subtotal(self):
        for rec in self:
            if rec.x_type == "unit":
                rec.price_subtotal = rec.i_qty * rec.price_unit
            elif rec.x_type == "ooh":
                rec.price_subtotal = rec.i_duration / 30 *rec.i_qty * rec.price_unit if rec.i_duration else 0
            else:
                rec.price_subtotal = rec.i_totalsqrfeet * rec.price_unit


    map_link = fields.Char(string="MAP")

    i_tentative_start_date = fields.Date(string="TentativeStart Date")
    i_tentative_end_date = fields.Date(string="TentativeEnd Date")

    @api.depends('i_tentative_start_date', 'i_tentative_end_date')
    def cal_duration(self):
        for rec in self:
            if rec.i_tentative_start_date and rec.i_tentative_end_date:
                if rec.i_tentative_start_date > rec.i_tentative_end_date:
                    raise ValidationError("Start Date cannot be earlier than End Date!!!!!!")
                else:
                    delta = rec.i_tentative_end_date - rec.i_tentative_start_date
                    rec.i_duration = delta.days + 1

    i_duration = fields.Float(string="Duration", compute="cal_duration", store=True)
