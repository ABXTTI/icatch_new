from odoo import fields, models, api


class IctInkType(models.Model):
    _name = "ict.ink.type"
    _description = "Icatch Ink Type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Ink Type", required=True)