from odoo import models, fields, api

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