odoo.define('pos_home_delivery.pos_delivery', function (require) {
	"use strict";

	var core = require('web.core');
	var _t = core._t;
	var models = require('point_of_sale.models');
	var rpc = require('web.rpc');


	models.load_models({
		model:  'product.product',
		fields: ['display_name', 'list_price','price','pos_categ_id', 'taxes_id', 'barcode', 'default_code',
		'to_weight', 'uom_id', 'description_sale', 'description', 'categ_id', 'product_tmpl_id','tracking','is_home_delivery_charge'],
			domain: [['sale_ok','=',true],['available_in_pos','=',true]], //['is_home_delivery_charge','=',true]
			loaded: function(self, product_delivery){
				self.product_delivery = product_delivery;
				self.get_products = [];
				self.get_products_by_id = [];
			},   
		});


	var _super_posmodel = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		
		initialize: function (session, attributes) {
			var product_model = _.find(this.models, function(model){ return model.model === 'res.partner'; });
			product_model.fields.push('street2');

			var payment_method = _.find(this.models, function(model){ return model.model === 'pos.payment.method'; });
			payment_method.fields.push('is_home_delivery');
			return _super_posmodel.initialize.call(this, session, attributes);
		},
		
	});

	var posorder_super = models.Order.prototype;
	models.Order = models.Order.extend({
		initialize: function(attr, options) {
			posorder_super.initialize.call(this,attr,options);
			this.d_name = this.d_name || "";
			this.mobile = this.mobile || "";
			this.email = this.email || "";
			this.address = this.address || "";
			this.street = this.street || "";
			this.city = this.city || "";
			this.zip = this.zip || "";
			this.delivery_date = this.delivery_date || "";
			this.person_id = this.person_id || "";
			this.order_note = this.order_note || "";
			this.delivery = this.delivery || false;
		},
		set_delivery_data: function(fields){
			this.d_name = fields.d_name;
			this.mobile = fields.mobile;
			this.email = fields.email;
			this.address = fields.address;
			this.street = fields.street;
			this.city = fields.city;
			this.zip = fields.zip || "";
			this.delivery_date = fields.delivery_date;
			this.person_id = fields.person_id;
			this.order_note = fields.order_note;
			this.trigger('change',this);
		},
		set_delivery_status: function(delivery){
			this.delivery = delivery;
			this.trigger('change',this);
		},
		get_delivery_status: function(delivery){
			return this.delivery;
		},
		get_div_name:function(d_name){
			return this.d_name;
		},
		get_div_email:function(email){
			return this.email;
		},
		get_div_mobile:function(mobile){
			return this.mobile;
		},
		get_div_location:function(address){
			return this.address;
		},
		get_div_street:function(street){
			return this.street;
		},
		get_div_city:function(city){
			return this.city;
		},
		get_div_zip:function(zip){
			return this.zip;
		},
		get_delivery_date:function(delivery_date){
			return this.delivery_date;
		},
		get_div_person:function(person_id){
			return this.person_id;
		},
		get_div_note:function(order_note){
			return this.order_note;
		},
		export_as_JSON: function() {
			var json = posorder_super.export_as_JSON.apply(this,arguments);
			json.d_name = this.get_div_name();
			json.email = this.get_div_email();
			json.mobile = this.get_div_mobile();
			json.address = this.get_div_location();
			json.street = this.get_div_street();
			json.city = this.get_div_city();
			json.zip = this.get_div_zip();
			json.delivery_date = this.get_delivery_date();
			json.person_id = this.get_div_person();
			json.order_note = this.get_div_note();
			json.delivery = this.get_delivery_status();
			return json;
		},
		init_from_JSON: function(json){
			posorder_super.init_from_JSON.apply(this,arguments);
			this.set_delivery_data(json);
			this.delivery = json.delivery;
			
		},
	});

});
