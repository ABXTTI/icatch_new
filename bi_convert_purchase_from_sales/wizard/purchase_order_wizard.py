# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from odoo import api, fields, models, _
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class createpurchaseorder(models.TransientModel):
	_name = 'create.purchaseorder'
	_description = "Create Purchase Order"

	new_order_line_ids = fields.One2many('getsale.orderdata', 'new_order_line_id',string="Order Line")
	partner_id = fields.Many2one('res.partner', string='Vendor', required = True)
	date_order = fields.Datetime(string='Order Date', required=True, copy=False, default=fields.Datetime.now)
	
	@api.model
	def default_get(self,  default_fields):
		res = super(createpurchaseorder, self).default_get(default_fields)
		data = self.env['sale.order'].browse(self._context.get('active_ids',[]))
		update = []
		for record in data.order_line:
			if record.po and not record.po_created:
				# print("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
				if not record.product_id.default_code:
					raise ValidationError("Internal Reference for the Product Does Not Exist")
				p_product = self.env['product.product'].search([('default_code', '=', (record.product_id.default_code + "p"))])
				if len(p_product) > 1:
					raise ValidationError("Duplicate Products /Or products with same Internal Reference in Products List !!!!!!")
				elif len(p_product) < 1:
					raise ValidationError("Purchasable Product Does Not Exist e.g. 1022p for 1022")

				update.append((0, 0, {
								'product_id': p_product.id,
								'product_uom': record.product_uom.id,
								'order_id': record.order_id.id,
								'name': record.name,
								'i_qty': record.i_qty,
								'product_qty': record.product_uom_qty,
								'price_unit': record.price_unit,
								'product_subtotal': record.price_subtotal,
								'i_shop': record.i_shop.id,
								'i_city': record.i_city.id,
								'i_mediadescription': record.i_mediadescription.id,
								'i_medium_description': record.i_medium_description.id,
								'i_size': record.i_size,
								'i_width': record.i_width,
								'i_height': record.i_height,
								'po': record.po,
								'po_created': record.po_created,
								}))
		if not update:
			raise ValidationError("Lines not Left / Selected for Creating Purchase Order !!!!!!!!!")
		if update:
			res.update({'new_order_line_ids':update})
			return res

	def action_create_purchase_order(self):
		self.ensure_one()
		res = self.env['purchase.order'].browse(self._context.get('id',[]))
		value = []
		so = self.env['sale.order'].browse(self._context.get('active_id'))
		pricelist = self.partner_id.property_product_pricelist
		partner_pricelist = self.partner_id.property_product_pricelist
		sale_order_name = ""
		for data in self.new_order_line_ids:
			sale_order_name = data.order_id.name
			if not sale_order_name:
				sale_order_name = so.name
			if partner_pricelist:
				product_context = dict(self.env.context, partner_id=self.partner_id.id, date=self.date_order, uom=data.product_uom.id)
				final_price, rule_id = partner_pricelist.with_context(product_context).get_product_price_rule(data.product_id, data.product_qty or 1.0, self.partner_id)

			else:
				final_price = data.product_id.standard_price
			if data.po and not data.po_created:
				value.append([0,0,{
									'product_id' : data.product_id.id,
									'name' : data.name,
									'i_qty' : data.i_qty,
									'product_qty' : data.product_qty,
									'order_id':data.order_id.id,
									'product_uom' : data.product_uom.id,
									'taxes_id' : data.product_id.supplier_taxes_id.ids,
									'date_planned' : data.date_planned,
									'price_unit' : final_price,
									'i_shop' : data.i_shop.id,
									'i_city' : data.i_city.id,
									'i_mediadescription' : data.i_mediadescription.id,
									'i_medium_description' : data.i_medium_description.id,
									'i_size': data.i_size,
									'i_width' : data.i_width,
									'i_height' : data.i_height,
									}])

		ref = so.order_line.search([('po', '=', True), ('order_id', '=', so.id)])
		for rec in ref:
			if rec.po and not rec.po_created:
				rec.po_created = True

		print(ref, "TTTTTTTTTTTTTTYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
		# print(self.abc)

		if value:
			res.create({
							'partner_id' : self.partner_id.id,
							'date_order' : str(self.date_order),
							'order_line':value,
							'origin' : sale_order_name,
							'partner_ref' : sale_order_name,
							'x_origin': so.id,
							'x_campaign': data.x_campaign.id,
							'x_brand': data.x_brand.id,
						})

			return res


class Getsaleorderdata(models.TransientModel):
	_name = 'getsale.orderdata'
	_description = "Get Sale Order Data"

	new_order_line_id = fields.Many2one('create.purchaseorder')
		
	product_id = fields.Many2one('product.product', string="Product", required=True)
	name = fields.Char(string="Description")
	product_qty = fields.Float(string='Quantity', required=True)
	date_planned = fields.Datetime(string='Scheduled Date', default = datetime.today())
	product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure')
	order_id = fields.Many2one('sale.order', string='Order Reference', ondelete='cascade', index=True)
	price_unit = fields.Float(string='Unit Price', digits='Product Price')
	product_subtotal = fields.Float(string="Sub Total", compute='_compute_total')
	i_shop = fields.Many2one('ict.shop', string="Location")
	i_city = fields.Many2one('ict.city', string="City")
	i_mediadescription = fields.Many2one('ict.media.description', string="Media Description")
	i_medium_description = fields.Many2one('ict.medium.description', string="Medium Description")
	i_size = fields.Char(string="Size")
	i_width = fields.Float(string="Width", default=1)
	i_height = fields.Float(string="Height", default=1)
	i_qty = fields.Float(string="i_qty")
	x_campaign = fields.Many2one('ict.campaign', string="Campaign")
	x_brand = fields.Many2one('ict.brand', string="Brand")
	po = fields.Boolean(string="PO")
	po_created = fields.Boolean(string="PO Created")

	@api.depends('product_qty', 'price_unit')
	def _compute_total(self):
		for record in self:
			record.product_subtotal = record.product_qty * record.price_unit
