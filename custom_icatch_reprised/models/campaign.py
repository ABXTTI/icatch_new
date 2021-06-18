from odoo import fields, models, api


class IctCampaign(models.Model):
    _name = "ict.campaign"
    _description = "Icatch Campaigns"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Campaign", required=True)
    related_brand = fields.Many2one('ict.brand', string="Brand Name")

    @api.depends('related_brand')
    def get_customer(self):
        self.related_customer = self.related_brand.parent_id

    related_customer = fields.Many2one('res.partner', string="Customer Name", compute='get_customer', store=True)
