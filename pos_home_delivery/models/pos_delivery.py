# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from dateutil import parser
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import logging
from datetime import datetime, date
_logger = logging.getLogger(__name__)

class PosDeliveryOrder(models.Model):
	_name = "pos.delivery.order"
	_rec_name = 'order_no'
	_order = "id desc"
	_inherit = ['mail.thread']
	_description = "POS Delivery Order"

	partner_id = fields.Many2one("res.partner", string='Customer', required=True)
	mobile = fields.Char('Mobile/Phone')
	email = fields.Char('Email')
	address = fields.Char(required=True)
	street = fields.Char()
	city = fields.Char()
	zip = fields.Char(change_default=True)
	state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
	country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
	order_date = fields.Datetime('Order Date', index=True)
	order_no = fields.Char('Order No', required=True, index=True)
	delivery_date = fields.Datetime('Delivery Time', required=True, index=True)
	delivery_lines = fields.One2many('pos.delivery.order.line', 'pos_delivery_id', 'Delivery Order Lines')
	cashier_id = fields.Many2one('res.users', 'Cashier')
	user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
	person_id = fields.Many2one('res.users', 'Delivery Person', required=True, index=True)
	session_id = fields.Many2one('pos.session', 'Session')
	pos_order_id = fields.Many2one('pos.order', 'Order Ref')
	payment_ids = fields.One2many(related='pos_order_id.payment_ids', string='Payments', readonly=True)
	order_note = fields.Text('Order Note')
	partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', help="Delivery address for current sales order.")
	state = fields.Selection([
		('draft', 'New'),
		('in_progress', 'In progress'),
		('delivered', 'Delivered'),
		('paid', 'Paid'),
		('cancel', 'Cancel'),
	], string='States', default='draft', readonly=True)

	def make_in_progress(self):
		self.state = 'in_progress'
		return True

	def make_delivered(self):
		self.state = 'delivered'
		return True

	def make_draft(self):
		self.state = 'draft'
		return True

	def make_cancel(self):
		self.state = 'cancel'
		return True

	def make_delivery_payment(self):
		self.ensure_one()
		delivery_journals = []
		if self.pos_order_id:
			amount = self.pos_order_id.amount_paid  - self.pos_order_id.amount_total
			for journal in self.session_id.config_id.payment_method_ids:
				if journal.is_home_delivery and journal.is_cash_count : 
					delivery_journals.append(journal.id)

			if not delivery_journals:
				raise UserError(_('Please Define Home Delivery Journal..'))
			if amount <= 0.0:
				data = {
					'name': _('Home/Delivery'),
					'amount': -amount,
					'payment_date': fields.Datetime.now(),
					'payment_method_id': delivery_journals[0] if delivery_journals else False,
					'pos_order_id': self.pos_order_id.id,
				}

				self.pos_order_id.add_payment(data)
				# statement_rec = self.pos_order_id.mapped('statement_ids').mapped('statement_id')
				message = _("Your account has been created with amount: %s") % (amount)
				# if statement_rec:
				# 	for stat in statement_rec:
				# 		message = _("Your bank statement <a href=# data-oe-model=account.bank.statement data-oe-id=%d>%s</a> has been created with amount: %s") % (stat.id, stat.name, amount)
				self.message_post(body=message)
				self.write({'state': 'paid'})
			else:
				raise UserError(_('Your delivery order has already paid'))
		else:
			raise UserError(_('POS Order not found !. \n\n Before making payment, You need to validate POS order from front-end'))

	@api.model
	def delivery_order_from_ui(self, data):
		try:
			order_line = []
			order = data.get('order_data', {})
			form_ui = data.get('form_data', {})
			partner = data.get('partner', {})
			other_addrs = data.get('other_addrs')
			for line in data.get('line_data', False):
				order_line.append((0, 0, {'product_id': line.get('product_id', False), 'item_qty': line.get('qty', 0.0), 'item_rate': line.get('price', 0.0), 'item_note': line.get('note', '')}))
		
			if order and order_line and form_ui:
				date_order = order.get('order_date', False)
				date_delivery = form_ui.get('delivery_date', False),
				if date_delivery:
					parse_d_date = parser.parse(''.join(date_delivery)).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
					date_delivery = fields.Datetime.from_string(parse_d_date)
				if date_order:
					parse_o_date = parser.parse(date_order).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
					date_order = fields.Datetime.from_string(parse_o_date)
					delivery_data = {
						'type':'delivery',
						'parent_id': partner['id'],
						'name': form_ui.get('d_name', False),
						'mobile': form_ui.get('mobile', False),
						'email': form_ui.get('email', False),
						'street': form_ui.get('address', False),
						'street2': form_ui.get('street', False),
						'city': form_ui.get('city', False),
						'zip': form_ui.get('zip', False),
					}
				if delivery_data:
					self.env['res.partner'].sudo().create(delivery_data)

				if other_addrs == 0:                
					values = {
						'partner_id': partner['id'] or False,
						'mobile': partner['mobile'] or False,
						'email': partner['email'] or False,
						'address': partner['address'] or False,
						'street': partner['street'] or False,
						'city': partner['city'] or False,
						'zip': partner['zip'] or False,                            
						
						'delivery_date': date_delivery or fields.Datetime.now(),
						'order_note': form_ui.get('order_note', False),
						'person_id': form_ui.get('person_id', False),
						'order_no': order.get('order_no', False),
						'order_date': date_order or fields.Datetime.now(),
						'session_id': order.get('session_id', False),
						'cashier_id': order.get('cashier_id', False),
						'delivery_lines': order_line
					}
					if values:
						h_del = self.env['pos.delivery.order'].sudo().create(values)
				else:
					values = {
						'partner_id': partner['id'] or False,
						'mobile': form_ui.get('mobile', False),
						'email': form_ui.get('email', False),
						'address': form_ui.get('address', False),
						'street': form_ui.get('street', False),
						'city':form_ui.get('city', False),
						'zip': form_ui.get('zip', False),                 
						
						'delivery_date': date_delivery or fields.Datetime.now(),
						'order_note': form_ui.get('order_note', False),
						'person_id': form_ui.get('person_id', False),
						'order_no': order.get('order_no', False),
						'order_date': date_order or fields.Datetime.now(),
						'session_id': order.get('session_id', False),
						'cashier_id': order.get('cashier_id', False),
						'delivery_lines': order_line
					}
					if values:
						h_del = self.env['pos.delivery.order'].sudo().create(values)
						
					
		except Exception as err:
			_logger.error('Error in Home Delivery creation: %s', tools.ustr(err))
		return True


	@api.model
	def delivery_order_from_ui_with_partner(self, partner, order_data, orderlines, date_delivery, notes, delivery_person):
		try:
			order_line = []
			delivery_charge_line = []
			order = order_data
			partner = partner
			#flag = 0
			for line in orderlines:
				order_line.append((0, 0, {'product_id': line.get('product_id', False), 'item_qty': line.get('qty', 0.0), 'item_rate': line.get('price', 0.0), 'item_note': line.get('note', '')}))
			
			if order and order_line and partner:
				date_order = order.get('order_date', False)
				date_delivery = date_delivery or fields.Datetime.now(),
				if date_delivery:
					parse_d_date = parser.parse(''.join(date_delivery)).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
					date_delivery = fields.Datetime.from_string(parse_d_date)
				if date_order:
					parse_o_date = parser.parse(date_order).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
					date_order = fields.Datetime.from_string(parse_o_date)
					values = {
						'partner_id': partner['id'] or False,
						'mobile': partner['mobile'] or partner['phone'] or False,
						'email': partner['email'] or False,
						'address': partner['address'] or False,
						'street': partner['street'] or False,
						'city': partner['city'] or False,
						'zip': partner['zip'] or False,
						'delivery_date': date_delivery or fields.Datetime.now(),
						'order_note': notes,
						'person_id': delivery_person,
						'order_no': order.get('order_no', False),
						'order_date': date_order or fields.Datetime.now(),
						'session_id': order.get('session_id', False),
						'cashier_id': order.get('cashier_id', False),
						'delivery_lines': order_line
					}
				if values:
					h_del = self.env['pos.delivery.order'].sudo().create(values)
					
		except Exception as err:
			_logger.error('Error in Home Delivery creation: %s', tools.ustr(err))

		return True

	def unlink(self):
		for del_order in self.filtered(lambda del_order: del_order.state not in ['draft', 'cancel']):
			raise UserError(_('In order to delete a delivery, it must be new or cancelled.'))
		return super(PosDeliveryOrder, self).unlink()

	@api.returns('self', lambda value: value.id)
	def copy(self, default=None):
		default = dict(default or {}, order_no=_("%s (Copy)") % self.order_no)
		return super(PosDeliveryOrder, self).copy(default=default)


class PosDeliveryOrderLine(models.Model):
	_name = "pos.delivery.order.line"
	_description = "POS Delivery Order Line"

	product_id = fields.Many2one('product.product', 'Product', required=True)
	item_qty = fields.Float('Quantity')
	item_rate = fields.Float('Price', digits=0)
	pos_delivery_id = fields.Many2one('pos.delivery.order', 'Delivery order')
	item_note = fields.Char('Item Note', size=72)
