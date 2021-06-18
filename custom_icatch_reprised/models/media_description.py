from odoo import fields, models, api


class IctMediaDescription(models.Model):
    _name = "ict.media.description"
    _description = "Icatch Media Description"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Media Description", required=True)
    related_product = fields.Many2one('product.product', string="Product")