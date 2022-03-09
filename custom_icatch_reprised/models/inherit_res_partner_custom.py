from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    strn = fields.Char(string="STRN")