
from odoo import fields, models, api
from odoo.exceptions import ValidationError
import datetime



class SaleOrder(models.Model):
    _inherit = "sale.order"

    def create_tax_purchase_order(self):
        var = self.env["create.purchase.order.lines.draft"]
        product_obj = self.env["product.product"].search([('name', '=', 'Visibility Tax')])
        if not product_obj:
            raise ValidationError("'Visibility Tax' Does not exist in Product. First Create the Product.!!!!")
        id = self.id
        existing = var.search([('so_ref', '=', id)])
        if existing:
            for rec in existing:
                rec.unlink()
        for rec in self.order_line:
            var.sudo().create({
                "product_id": product_obj[0].id,
                "location": rec.i_shop.id,
                "description": rec.i_description,
                "city": rec.i_city.id,
                "mediadescription": rec.i_mediadescription.id,
                "mediumdescription": rec.i_medium_description.id,
                "type": rec.x_type,
                "uom": rec.x_uom,
                "width": rec.i_width,
                "height": rec.i_height,
                "sqrft": rec.i_sqrfeet,
                "qty": rec.i_qty,
                "totalsqrfeet": rec.i_totalsqrfeet,
                "tentative_start_date": rec.i_tentative_start_date,
                "tentative_end_date": rec.i_tentative_end_date,
                "duration": rec.i_duration,
                # "po_created": rec.po_created,
                "so_ref": id,
                "order_line_id": rec.id,
            })
        return var.create_purchase_order(id)

    def create_purchase_order(self):
        var = self.env["create.purchase.order.lines.draft"]
        id = self.id
        existing = var.search([('so_ref', '=', id)])

        if existing:
            for rec in existing:
                rec.unlink()
        for rec in self.order_line:
            req_service_purchase_product_id = self.env['product.product'].search([('default_code', '=', (rec.product_id.default_code + "-P"))])
            if rec.product_id.require_service_purchase_product:
                if not req_service_purchase_product_id:
                    raise ValidationError("Required Service Purchase Product for "+ rec.product_id.name + "[" + rec.product_id.default_code + "]" + " does not exist !!!!")
            var.sudo().create({
                "product_id": req_service_purchase_product_id.id if req_service_purchase_product_id else rec.product_id.id,
                "location": rec.i_shop.id,
                "description": rec.i_description,
                "city": rec.i_city.id,
                "mediadescription": rec.i_mediadescription.id,
                "mediumdescription": rec.i_medium_description.id,
                "type": rec.x_type,
                "uom": rec.x_uom,
                "width": rec.i_width,
                "height": rec.i_height,
                "sqrft": rec.i_sqrfeet,
                "qty": rec.i_qty,
                "totalsqrfeet": rec.i_totalsqrfeet,
                "tentative_start_date": rec.i_tentative_start_date,
                "tentative_end_date": rec.i_tentative_end_date,
                "duration": rec.i_duration,
                "po_created": rec.po_created,
                "so_ref": id,
                "order_line_id": rec.id,
            })
        return var.create_purchase_order(id)


class CreatePurchaseOrderLinesDraft(models.TransientModel):
    _name = "create.purchase.order.lines.draft"

    partner_id = fields.Many2one('res.partner', string="Vendor")
    so_ref = fields.Char(string="SO Ref.")
    order_line_id = fields.Char("Order Line Id")
    product_id = fields.Many2one('product.product', string="Product")
    location = fields.Many2one('ict.shop', string="Location")
    description = fields.Char(string="Description")
    city = fields.Many2one('ict.city', string="City")
    po_created = fields.Boolean(string="PO Created")
    mediadescription = fields.Many2one('ict.media.description', string="Media Description")
    mediumdescription = fields.Many2one('ict.medium.description')
    type = fields.Selection([('ooh', 'OOH'), ('unit', 'Unit')], 'Type')
    uom = fields.Selection([('squarefeet', 'Sqr.Ft.'), ('inches', 'Inches')], 'Measure', default="")
    width = fields.Float(string="Width")
    height = fields.Float(string="height")
    sqrft = fields.Float(string="Sqr.Feet")
    qty = fields.Float(string="Qty")
    totalsqrfeet = fields.Float(string="Total Sqr/Qty")
    tentative_start_date = fields.Date(string="Tentative"
                                              "start Date")
    tentative_end_date = fields.Date(string="Tentative"
                                            "End Date")
    duration = fields.Float(string="Duration")

    @api.model
    def create_purchase_order(self, id):
        print("Its Working !!!!!!!!!!!!!!!!!!!!")
        print(id)

        return {
            'name': "action_draft_order_lines_wizard",
            'view_mode': 'tree',
            'view_id': False,
            'res_model': 'create.purchase.order.lines.draft',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': "[('po_created', '!=', True), ('so_ref', '=', %s)]" % id,
            'views': False,
            'context': "{}",
        }

    def purchase_order_create(self):
        print("Very Good @@@@")
        purchase_order = None
        active_ids = self.env.context.get('active_ids', [])
        sale_order_id = self.search([('id', '=', active_ids[0])]).so_ref
        sale_order = self.env['sale.order'].search([('id', '=', sale_order_id)])
        customer_id = sale_order.partner_id.id
        brand_id = sale_order.x_brand.id
        campaign_id = sale_order.x_campaign.id
        vendors_ids = []
        for rec in active_ids:
            record = self.search([('id', '=', rec)])
            if record.partner_id.id not in vendors_ids:
                vendors_ids.append(record.partner_id.id)
                print(vendors_ids)

        for vendor in vendors_ids:
            values = []
            for id in active_ids:
                record = self.search([('id', '=', id)])
                sale_order_line_id = self.env['sale.order.line'].search([('id', '=', record.order_line_id)])
                sale_order_line_id.po_created = True
                if record and record.partner_id.id == vendor:
                    req_service_purchase_product = self.env['product.product'].search([('default_code', '=', (record.product_id.default_code + "-P"))])
                    if not req_service_purchase_product:
                        raise ValidationError("Required Service Purchase Product Does Not Exist For "+ record.product_id.name +"["+ record.product_id.default_code +"].")
                    values.append([0, 0, {
                        "product_id": req_service_purchase_product.id,
                        "i_shop": record.location.id,
                        "i_city": record.city.id,
                        "i_mediadescription": record.mediadescription.id,
                        "x_uom": record.uom,
                        "i_width": record.width,
                        "i_height": record.height,
                        "i_sqrfeet": record.sqrft,
                        "i_qty": record.qty,
                    }])
            # print(values)

            res = self.env['purchase.order']
            purchase_order = res.create({
                                    'partner_id': vendor,
                                    'date_order': datetime.datetime.today(),
                                    'order_line': values,
                                    'origin': sale_order_id,
                                    'partner_ref': sale_order.id,
                                    'x_origin': sale_order.id,
                                    'x_customername': sale_order.partner_id.id,
                                    'x_campaign': sale_order.x_campaign.id,
                                    'x_brand': sale_order.x_brand.id,
                                })
        return {
            'name': "purchase_rfq",
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'existing',
            # 'domain': "[('po_created', '!=', True), ('so_ref', '=', %s)]" % id,
            'views': False,
            'res_id': purchase_order.id,
            'context': "{}",
        }

    def get_active_ids(self):
        return self.env.context.get('active_ids', [])

    def select_vendor(self):
        active_ids = self.get_active_ids()
        new_id = self.env['select.vendor'].create({'active_line_ids': active_ids})
        for id in new_id:
            new_id = id

        return {
            'name': "select_vendor_wizard",
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'select.vendor',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'views': False,
            'res_id': new_id.id,
            'context': {},
        }


class SelectVendor(models.TransientModel):
    _name = "select.vendor"

    vendor_id = fields.Many2one('res.partner', "Vendor")
    active_line_ids = fields.Char(string="Active Ids")
    so_ref = fields.Char(string="SO Ref")

    @api.onchange('vendor_id')
    def select_vendor(self):
        convert_to_list = self.active_line_ids.strip('][').split(",")
        so_id = self.env['create.purchase.order.lines.draft'].search([('id', '=', convert_to_list[0])])
        self.so_ref = so_id.so_ref
        print(so_id.so_ref)
        for rec in convert_to_list:
            var = self.env['create.purchase.order.lines.draft'].search([('id', '=', rec)])
            print(var)
            if var:
                var.partner_id = self.vendor_id.id

    def view_change(self):
        print(self.so_ref)

        return {
            'name': "action_draft_order_lines_wizard",
            'view_mode': 'tree',
            'view_id': False,
            'res_model': 'create.purchase.order.lines.draft',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': "[('partner_id', '!=', False), ('so_ref', '=', %s)]" % self.so_ref,
            # 'domain': "[('so_ref', '=', %s)]" % self.so_ref,
            'views': False,
            'context': {},
        }
