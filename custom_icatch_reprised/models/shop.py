from odoo import fields, models, api


class IctShop(models.Model):
    _name = "ict.shop"
    _description = "Shops"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Shop", required=True)
