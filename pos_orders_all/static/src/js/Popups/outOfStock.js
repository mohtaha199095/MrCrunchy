// outOfStock
odoo.define('pos_orders_all.outOfStock', function(require) {
	'use strict';

	const ErrorPopup = require('point_of_sale.ErrorPopup');
	const Registries = require('point_of_sale.Registries');

	class outOfStock extends ErrorPopup {
		go_back_screen() {
			this.showScreen('ProductScreen');
			this.trigger('close-popup');
		}

	}
	
	outOfStock.template = 'outOfStock';
	outOfStock.defaultProps = {
		// confirmText: 'Ok',
		// cancelText: 'Cancel',
		title: 'Unknown customer',
		body: 'You cannot Create Purchase Order. Select customer first.',
	};

	Registries.Component.add(outOfStock);

	return outOfStock;
});
