from odoo import api, models, fields, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    x_origin = fields.Many2one("sale.order", string="Related Sale Order")

    @api.depends('origin')
    def get_origin(self):
        for rec in self:
            x = self.env['sale.order'].search([('name', '=', rec.origin)])
            if x:
                rec.x_origin = x.id

    x_campaign = fields.Many2one('ict.campaign', string="Campaign", related="x_origin.x_campaign", required=True)

    x_ntn = fields.Char(string="NTN", related="partner_id.vat")
    x_strn = fields.Char(string="STRN", related="partner_id.strn")
    x_mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    x_phone = fields.Char(string="Phone", related="partner_id.phone")
    x_email = fields.Char(string="Email", related="partner_id.email")

    @api.depends('x_campaign')
    def get_brand(self):
        self.x_brand = self.x_campaign.related_brand

    x_brand = fields.Many2one('ict.brand', string="Brand", compute='get_brand', store=True)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    i_medium_description = fields.Many2one('ict.medium.description', string="Media Description")
    i_city = fields.Many2one('ict.city', string="City")
    i_shop = fields.Many2one('ict.shop', string="Location")
    i_mediadescription = fields.Many2one('ict.media.description', string="Media Description")
    i_printer = fields.Many2one('ict.printer', string="Printer")
    i_resolution = fields.Many2one('ict.resolution', string="Resolution")
    i_inktype = fields.Many2one('ict.ink.type', string="Ink Type")
    i_size = fields.Char(string="Size")
    i_width = fields.Float(string="Width", default=1)
    i_height = fields.Float(string="Height", default=1)

    @api.depends('i_width', 'i_height')
    def compute_sqfeet(self):
        for rec in self:
            rec.i_sqrfeet = rec.i_width * rec.i_height

    i_sqrfeet = fields.Float(string="Sqr.Feet", compute='compute_sqfeet', store=True)

    i_qty = fields.Float(string="Qty.ICT")

    @api.depends('i_qty', 'i_sqrfeet')
    def compute_total_qty(self):
        for rec in self:
            if not rec.product_id.x_is_units:
                rec.product_uom_qty = rec.i_qty * rec.i_sqrfeet
            else:
                rec.product_uom_qty = rec.i_qty * 1

    product_uom_qty = fields.Float(string="AQty", compute='compute_total_qty', store=True)