from odoo import fields, models, api


class IctPrinter(models.Model):
    _name = "ict.printer"
    _description = "Icatch Printer"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Printer", required=True)