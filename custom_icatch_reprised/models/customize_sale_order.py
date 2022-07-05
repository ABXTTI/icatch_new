import datetime

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_roll = fields.Boolean("Is Roll")
    is_mm = fields.Boolean("Is MM")
    size_sqrft = fields.Float(string="Size Sqrfeet")
    x_is_units = fields.Boolean("Is Unit")
    x_is_ooh = fields.Boolean("Is OOH")
    x_is_mediadescription = fields.Boolean("Is Media Description", default=False)
    x_is_medium_description = fields.Boolean("Is Medium Description", defualt=False)
    require_service_purchase_product = fields.Boolean("Required Service Purchase Product")


    @api.model
    def check_default_codes_and_service_purchase_product(self):
        no_default_codes = self.search([('default_code', '=', False)])
        if no_default_codes:
            for product in no_default_codes:
                product.default_code = 100000 + product.id

        if self.require_service_purchase_product:
            exist = self.search([('default_code', '=', (str(self.default_code) + "-P"))])
            if not exist:
                obj = self.env["product.template"].create({'name': self.name,
                                                           'purchase_ok': True,
                                                           'sale_ok': False,
                                                           'type': 'service',
                                                           })
                obj.default_code = self.default_code + "-P"

    def check_service_purchase_product(self):
        self.check_default_codes_and_service_purchase_product()

#     ########### Overriding Create Method####
    @api.model_create_multi
    def create(self, vals_list):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        templates = super(ProductTemplate, self).create(vals_list)
        if "create_product_product" not in self._context:
            templates._create_variant_ids()

        # This is needed to set given values to first variant after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            if vals.get('barcode'):
                related_vals['barcode'] = vals['barcode']
            if vals.get('default_code'):
                related_vals['default_code'] = vals['default_code']
            if vals.get('standard_price'):
                related_vals['standard_price'] = vals['standard_price']
            if vals.get('volume'):
                related_vals['volume'] = vals['volume']
            if vals.get('weight'):
                related_vals['weight'] = vals['weight']
            # Please do forward port
            if vals.get('packaging_ids'):
                related_vals['packaging_ids'] = vals['packaging_ids']
            if related_vals:
                template.write(related_vals)
            template['default_code'] = 100000 + template.id
        return templates

    # Overriding Copy Method
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # TDE FIXME: should probably be copy_data
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = _("%s (copy)", self.name)
        default['default_code'] = 100000 + self.id
        default['require_service_purchase_product'] = False
        return super(ProductTemplate, self).copy(default=default)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('partner_id')
    def onchange_parnterid(self):
        self.x_brand = ""
        self.x_campaign = ""

    survey_ref = fields.Many2one("survey.sale.order", string="Survey Ref.")
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
                            elif line.product_id.size_sqrft:
                                line.product_qty = rec.i_totalsqrfeet * line.product_id.size_sqrft
                            else:
                                line.product_qty = 1
                    if rec.product_id.is_mm:
                        if rec.i_mediadescription or rec.i_medium_description:
                            lines = []
                            product = self.env['product.product'].search(
                                [('name', '=', rec.i_medium_description.name)])
                            if product:
                                for p in product:
                                    lines.append((0, 0, {'product_id': p.id,
                                                         'product_qty': (rec.i_sqrfeet * p.size_sqrft) if p.size_sqrft else 1.0}))
                            product1 = self.env['product.product'].search(
                                [('name', '=', rec.i_mediadescription.name)])
                            if product1:
                                for p in product1:
                                    lines.append((0, 0, {'product_id': p.id,
                                                         'product_qty': (rec.i_sqrfeet * p.size_sqrft) if p.size_sqrft else 1.0}))

                            bom_id.bom_line_ids = lines
                    elif not rec.product_id.is_mm:
                        if rec.i_mediadescription or rec.i_medium_description:
                            lines = []
                            product = self.env['product.product'].search(
                                [('name', '=', rec.i_mediadescription.name)])
                            if product:
                                for p in product:
                                    lines.append((0, 0, {'product_id': p.id,
                                                         'product_qty': (rec.i_sqrfeet * p.size_sqrft) if p.size_sqrft else 1.0}))

                            bom_id.bom_line_ids = lines
                else:
                    if rec.product_id.is_mm:
                        if rec.i_mediadescription or rec.i_medium_description:
                            lines = []
                            product = self.env['product.product'].search(
                                [('name', '=', rec.i_medium_description.name)])
                            if product:
                                for p in product:
                                    lines.append((0, 0, {'product_id': p.id}))
                            product1 = self.env['product.product'].search(
                                [('name', '=', rec.i_mediadescription.name)])
                            if product1:
                                for p in product1:
                                    lines.append((0, 0, {'product_id': p.id,
                                                         'product_qty': (rec.i_totalsqrfeet * p.size_sqrft) if p.size_sqrft else 1.0}))

                            # bom_id.bom_line_ids = lines
                            bom = self.env['mrp.bom']
                            bom.create({
                                'product_tmpl_id': rec.product_id.id,
                                'product_uom_id': rec.product_id.uom_id.id,
                                'bom_line_ids': lines
                            })
                    elif not rec.product_id.is_mm:
                        if rec.i_mediadescription or rec.i_medium_description:
                            lines = []
                            product = self.env['product.product'].search(
                                [('name', '=', rec.i_mediadescription.name)])
                            if product:
                                for each in product:
                                    lines.append((0, 0, {'product_id': each.id}))

                            # bom_id.bom_line_ids = lines
                            bom = self.env['mrp.bom']
                            bom.create({
                                'product_tmpl_id': rec.product_id.id,
                                'product_uom_id': rec.product_id.uom_id.id,
                                'bom_line_ids': lines
                            })


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

    survey_ref = fields.Many2one("survey.sale.order", string="Survey ID", related="survey_line_id.survey_so_ref")
    survey_line_id = fields.Many2one("survey.sale.order.line", string="Survey Line ID")
    i_description = fields.Char(string="Description")
    map_link = fields.Char("MAP")
    po = fields.Boolean(string="PO", copy=False)
    po_created = fields.Boolean(string="PO Created", default=False, copy=False)
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
                # print("33333333333333333333333333333333333333333333")
    i_medium_description = fields.Many2one('ict.medium.description', string="Medium Description")
    i_city = fields.Many2one('ict.city', string="City")
    i_shop = fields.Many2one('ict.shop', string="Location")

    @api.onchange('i_mediadescription')
    def onchange_i_mediadescription(self):
        # print("111111111111111111111111111111111111111111111111")
        if not self.product_id and self.i_mediadescription.related_product:
            raise ValidationError("Please Select Product First.")
        else:
            if not self.i_mediadescription.related_product:
                self.i_mediadescription.related_product = self.product_id.id
                # print("33333333333333333333333333333333333333333333")

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
                rec.i_sqrfeet = rec.i_width * rec.i_height /144
            else:
                rec.i_sqrfeet = rec.i_width * rec.i_height


    i_sqrfeet = fields.Float(string="Sqr.Feet", compute='compute_sqfeet', store=True)
    i_qty = fields.Float(string="Qty.ICT")

    @api.depends('i_qty', 'i_sqrfeet', 'x_uom', 'price_subtotal')
    def compute_total_qty(self):
        for rec in self:
            if rec.x_type == "unit":
                rec.product_uom_qty = rec.i_qty * 1
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet
            elif rec.x_type == "ooh":
                rec.product_uom_qty = rec.i_qty * rec.i_duration / 30 if rec.i_duration else 0
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet
            else:
                rec.product_uom_qty = rec.i_qty * rec.i_sqrfeet
                rec.i_totalsqrfeet = rec.i_qty * rec.i_sqrfeet

    product_uom_qty = fields.Float(string="Total Sqr.Feet/Qty", compute='compute_total_qty')
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

    @api.onchange('order_id')
    def on_change_name(self):
        for rec in self:
            rec.po_created = False
