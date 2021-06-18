from odoo import fields, models, api


class IctCity(models.Model):
    _name = "ict.city"
    _description = "City"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="City", required=True)