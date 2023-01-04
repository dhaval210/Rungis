odoo.define('metro_datepickerfix.datepicker', function (require) {
    "use strict";

    var DateWidget = require('web.datepicker').DateWidget;

    DateWidget.include({

        start: function(parent, options) {
            this.options['focusOnShow'] = false;
            this.options['ignoreReadonly'] = true;
            this.$input = this.$('input.o_datepicker_input');
            this.__libInput++;
            this.$el.datetimepicker(this.options);
            this.__libInput--;
            this._setReadonly(true);
        },

        /**
         * @private
         * @param {boolean} readonly
         */
        _setReadonly: function (readonly) {
            this.readonly = readonly;
            this.$input.prop('readonly', this.readonly);
        },
    });
});