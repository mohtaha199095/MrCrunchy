# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)

class ProductDeliveryCharge(models.Model):
	_inherit = 'product.product'
	
	is_home_delivery_charge = fields.Boolean('Delivery Charge')


class PosConfig(models.Model):
	_inherit = 'pos.config'

	pos_verify_delivery = fields.Boolean(string='Home Delivery')


class AccountJournal(models.Model):
	_inherit = 'account.journal'

	is_home_delivery = fields.Boolean('Use as Home Delivery', help='if you use this journal as home delivery, it will not create any payment entries for that order')


class account_journal(models.Model):
	_inherit = 'pos.payment.method'

	is_home_delivery = fields.Boolean(string='Use as Home Delivery',related='cash_journal_id.is_home_delivery',readonly=False)  


	@api.model
	def create(self,vals):
		methods = self.search_count([('is_home_delivery','=',True)])
		if 'is_home_delivery' in vals:
			if vals.get('is_home_delivery') == True:
				if methods >= 1:
					raise UserError(_("Already one payment selected as home delivery , you can not create multiple home delivery methods."))
		return super(account_journal,self).create(vals)


	def write(self,vals):
		methods = self.search_count([('is_home_delivery','=',True)])
		if 'is_home_delivery' in vals:
			if vals.get('is_home_delivery') == True:
				if methods >= 1:
					raise UserError(_("Already one payment selected as home delivery , you can not create multiple home delivery methods."))
		return super(account_journal,self).write(vals)

class PosOrder(models.Model):
	_inherit = 'pos.order'

	delivery_order = fields.Boolean(string='Is Home Delivery Order')

	def write(self, vals):
		for order in self:
			if order.name == '/' and order.delivery_order :
				vals['name'] = order.config_id.sequence_id._next()
		return super(PosOrder, self).write(vals)

	@api.model
	def _order_fields(self, ui_order):
		res = super(PosOrder, self)._order_fields(ui_order)
		res['delivery_order'] = ui_order.get('delivery') or False
		return res
	
	@api.model
	def create_from_ui(self, orders, draft=False):
		pos_order_ids = super(PosOrder, self).create_from_ui(orders, draft=False)
		for order in pos_order_ids:
			order_rec = self.browse(order.get('id'))
			ref_order = [o['data'] for o in orders if o['data'].get('name') == order_rec.pos_reference]
			delivery_ids = self.env['pos.delivery.order'].sudo().search([('order_no', '=', order_rec.pos_reference)])
			if delivery_ids:
				delivery_ids.write({'pos_order_id': order.get('id')})
				order_rec.write({'state': 'done'})
		return pos_order_ids

	def _process_payment_lines(self, pos_order, order, pos_session, draft):
		"""Create account.bank.statement.lines from the dictionary given to the parent function.

		If the payment_line is an updated version of an existing one, the existing payment_line will first be
		removed before making a new one.
		:param pos_order: dictionary representing the order.
		:type pos_order: dict.
		:param order: Order object the payment lines should belong to.
		:type order: pos.order
		:param pos_session: PoS session the order was created in.
		:type pos_session: pos.session
		:param draft: Indicate that the pos_order is not validated yet.
		:type draft: bool.
		"""
		prec_acc = order.pricelist_id.currency_id.decimal_places

		order_bank_statement_lines= self.env['pos.payment'].search([('pos_order_id', '=', order.id)])
		order_bank_statement_lines.unlink()
		if not order.delivery_order :
			for payments in pos_order['statement_ids']:
				if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
					order.add_payment(self._payment_fields(order, payments[2]))

		order.amount_paid = sum(order.payment_ids.mapped('amount'))

		if not draft and not float_is_zero(pos_order['amount_return'], prec_acc):
			cash_payment_method = pos_session.payment_method_ids.filtered('is_cash_count')[:1]
			if not cash_payment_method:
				raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
			return_payment_vals = {
				'name': _('return'),
				'pos_order_id': order.id,
				'amount': -pos_order['amount_return'],
				'payment_date': fields.Date.context_today(self),
				'payment_method_id': cash_payment_method.id,
			}
			order.add_payment(return_payment_vals)


	@api.model
	def _process_order(self, order, draft, existing_order):
		"""Create or update an pos.order from a given dictionary.

		:param dict order: dictionary representing the order.
		:param bool draft: Indicate that the pos_order is not validated yet.
		:param existing_order: order to be updated or False.
		:type existing_order: pos.order.
		:returns: id of created/updated pos.order
		:rtype: int
		"""
		order = order['data']
		pos_session = self.env['pos.session'].browse(order['pos_session_id'])
		if pos_session.state == 'closing_control' or pos_session.state == 'closed':
			order['pos_session_id'] = self._get_valid_session(order).id

		pos_order = False
		if not existing_order:
			pos_order = self.create(self._order_fields(order))
		else:
			pos_order = existing_order
			pos_order.lines.unlink()
			order['user_id'] = pos_order.user_id.id
			pos_order.write(self._order_fields(order))

		pos_order = pos_order.with_company(pos_order.company_id)
		self = self.with_company(pos_order.company_id)
		self._process_payment_lines(order, pos_order, pos_session, draft)

		if not draft and not pos_order.delivery_order:
			try:
				pos_order.action_pos_order_paid()
			except psycopg2.DatabaseError:
				# do not hide transactional errors, the order(s) won't be saved!
				raise
			except Exception as e:
				_logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

		pos_order._create_order_picking()
		if pos_order.to_invoice and pos_order.state == 'paid':
			pos_order.action_pos_order_invoice()

		return pos_order.id