odoo.define('pos_home_delivery.ActionpadWidget', function(require) {
	"use strict";

	const models = require('point_of_sale.models');
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const Session = require('web.Session');
	const chrome = require('point_of_sale.Chrome');
	let rpc = require('web.rpc');
	const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
	const NumberBuffer = require('point_of_sale.NumberBuffer');
	const { useListener } = require('web.custom_hooks');
	const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
	const { useState } = owl.hooks;
	let core = require('web.core');
	let _t = core._t;
	const ProductScreen = require('point_of_sale.ProductScreen'); 

	const BiProductScreen = (ProductScreen) =>
	class extends ProductScreen {
		constructor() {
			super(...arguments);
		}

		async _clickProduct(event) { 
			var self = this;
			var delivery = this.env.pos.get_order().delivery;
			if(delivery == false){
				super._clickProduct(event);
			}else{
				self.showPopup('ErrorPopup', {
					'title': _t('Add New Product'),
					'body': _t('This order already create home delivery , you can not add new product.'),
				});
			}
		}
	};
});