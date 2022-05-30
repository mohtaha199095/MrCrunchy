odoo.define('pos_home_delivery.DatetimeSelectWidget', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    // formerly DatetimeSelectWidgetWidget
    class DatetimeSelectWidget extends AbstractAwaitablePopup {

        constructor() {
            super(...arguments);
        }

        mounted() {
            $('#del_date').datetimepicker({
                format: 'YYYY-MM-DD HH:mm:ss',
                inline: true,
                sideBySide: true
            });
        }

        async select() {
            this.props.resolve({ confirmed: true, payload: null });
            this.trigger('close-popup');
        }

        cancel() {
            this.props.resolve({ confirmed: false, payload: null });
            this.trigger('close-popup');
        }
    }
    DatetimeSelectWidget.template = 'DatetimeSelectWidget';
    DatetimeSelectWidget.defaultProps = {
        confirmText: 'Select',
        cancelText: 'Cancel',
        title: 'Select Date',
        body: '',
    };

    Registries.Component.add(DatetimeSelectWidget);

    return DatetimeSelectWidget;
});
