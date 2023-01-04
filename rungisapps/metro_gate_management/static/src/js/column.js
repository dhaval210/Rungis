odoo.define('metro_gate_management.picking_kanban_column', function (require) {
    'use strict';
    var KanbanController = require('web.KanbanController');

    KanbanController.include({

        /**
         * @private
         * @param {OdooEvent} event
         */
        _onAddRecordToColumn: function (event) {
            var self = this;
            this._super.apply(this, arguments);
            self.trigger_up("reload");
        },
    });
});
