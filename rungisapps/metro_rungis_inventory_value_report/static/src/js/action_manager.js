odoo.define('metro_rungis_inventory_value_report.action_manager', function (require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');
var crash_manager = require('web.crash_manager');

ActionManager.include({
    _executexlsxReportDownloadAction: function (action) {
        framework.blockUI();
        var def = $.Deferred();
        session.get_file({
            url: '/xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            error: function () {
                crash_manager.rpc_error.apply(crash_manager, arguments);
                def.reject();
            },
            complete: framework.unblockUI,
        });
        return def;
    },
    _handleAction: function (action, options) {
        if (action.type === 'ir_actions_xlsx_download') {
            return this._executexlsxReportDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);
    	},
    });
});
