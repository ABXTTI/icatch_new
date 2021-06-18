from odoo import fields, models

class IctBrand(models.Model):
    _name = "ict.brand"
    _description = "iCatch Brands"
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True)
    parent_id = fields.Many2one('res.partner', string="Customer")
