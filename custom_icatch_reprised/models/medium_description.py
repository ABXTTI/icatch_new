from odoo import fields, models, api


class IctMediumDesiption(models.Model):
    _name = "ict.medium.description"
    _description = "Icatch Medium Description"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Medium Description", required=True)
    related_product = fields.Many2one('product.product', string="Product")

    @api.model
    def create(self, vals):
        print("its working")
        product = self.env['product.template']
        exist = product.search([('name', '=', vals['name'])])
        if not exist:
            product.create({
                'name': vals['name'],
                'type': "product",
                'sale_ok': False,
                'purchase_ok': True,
                'x_is_mediadescription': True,
            })
        return super(IctMediumDesiption, self).create(vals)