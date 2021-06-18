from odoo import fields, models, api


class IctMediumDesiption(models.Model):
    _name = "ict.medium.description"
    _description = "Icatch Medium Description"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Medium Description", required=True)