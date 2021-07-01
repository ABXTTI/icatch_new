from odoo import fields, models, api


class IctMediaDescription(models.Model):
    _name = "ict.media.description"
    _description = "Icatch Media Description"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Media Description", required=True)
    related_product_purchase = fields.Many2one('product.product', string="Related Purchase Product")
    related_product = fields.Many2one('product.product', string="Product")

    @api.model
    def create(self, vals):
        print("its working")
        product = self.env['product.template']
        product.create({
            'name': vals['name'],
            'type': "product",
            'sale_ok': False,
            'purchase_ok': True,
            'x_is_mediadescription': True,
        })
        return super(IctMediaDescription, self).create(vals)