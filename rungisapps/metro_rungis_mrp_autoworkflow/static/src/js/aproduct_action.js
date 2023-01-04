odoo.define('metro_rungis_mrp_autoworkflow.aproduct_action', function(require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');

    var aproductAutoWorkflow = AbstractAction.extend({
        init: function (parent, action) {
            this._super(parent, action);
            this.active_ids = action.context.active_ids;
        },

        willStart: async function(){
            await rpc.query({
                model: 'stock.production.lot',
                method: 'aproduct_auto_workflow',
                args: [this.active_ids],
            }).then(function(result){
                if(result.length > 0){
                    new Dialog(this, {
                        size: 'large',
                        title: "Not done Aproducts",
                        $content: $(QWeb.render('metro_rungis_mrp_autoworkflow.notDone', {values: result}))
                    }).open();
                }
            });
            return this._super(parent, action);
        }
    });

    core.action_registry.add('aproduct_auto_workflow', aproductAutoWorkflow);
});
