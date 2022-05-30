odoo.define('pos_home_delivery.HomeDelivery', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    let core = require('web.core');
	let _t = core._t;
    const Registries = require('point_of_sale.Registries');

    class HomeDelivery extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }

        async onClick() {
            var self = this;
			var order = this.env.pos.get_order();

			var partner_id = false
			if (order.get_client() != null)
				partner_id = order.get_client();

			if (!partner_id) {
				self.showPopup('ErrorPopup', {
					'title': _t('Unknown customer'),
					'body': _t('You cannot use Home Delivery. Select customer first.'),
				});
				return;
			}       

			var orderlines = order.orderlines.models;
			if(orderlines.length < 1){
				self.showPopup('ErrorPopup',{
					'title': _t('Empty Order !'),
					'body': _t('Please select some products'),
				});
				return false;
			}
			
			self.showPopup('DeliveryOrderWidget', {
				'title': _t('Home Delivery Order'),
				'name' : order.get_div_name(),
				'email' : order.get_div_email(),
				'mobile' : order.get_div_mobile(),
				'address' : order.get_div_location(),
				'street' : order.get_div_street(),
				'city' : order.get_div_city(),
				'zip' : order.get_div_zip(),
				'delivery_date' : order.get_delivery_date(),
				'person_id' : order.get_div_person(),
				'order_note' : order.get_div_note(),
			});
        }
    }
    HomeDelivery.template = 'HomeDelivery';

    ProductScreen.addControlButton({
        component: HomeDelivery,
        condition: function() {
            return this.env.pos.config.pos_verify_delivery;
        },
    });

    Registries.Component.add(HomeDelivery);

    return HomeDelivery;
});
