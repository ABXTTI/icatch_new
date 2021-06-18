from odoo import fields, models, api


class IctResolution(models.Model):
    _name = "ict.resolution"
    _description = "Icatch Resolution"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Resolution", required=True)