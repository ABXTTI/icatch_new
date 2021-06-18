from odoo import api, models, fields
from odoo.exceptions import ValidationError
from datetime import date

class ProformaSaleOrder(models.Model):
    _name = "proforma.sale.order"
    _description = "Create Proforma Sale Order/Quotation"


    partner_id = fields.Many2one("res.partner", string="Customer")
    x_ntn = fields.Char(string="NTN", related="partner_id.vat")
    x_strn = fields.Char(string="STRN", related="partner_id.strn")
    x_mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    x_phone = fields.Char(string="Phone", related="partner_id.phone")
    x_email = fields.Char(string="Email", related="partner_id.email")
    x_campaign = fields.Many2one("ict.campaign", string="Campaign", required=True)