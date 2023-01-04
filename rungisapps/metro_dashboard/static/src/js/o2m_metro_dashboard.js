odoo.define("metro_dashboard.o2m_fields", function(require) {
"use strict";
    var core = require('web.core');
    var KanbanRecord = require('web.KanbanRecord');
    var QWeb = core.qweb;
    let ajax = require("web.ajax");

    function appendToTable(self, id, res) {
        for (let i = 0; i < res.length; i++) {
            // Limit float values to 2 decimal places
            const progress = Number.parseFloat(res[i].progress).toFixed(2);
            // Build node, convert with Number(progress) integers to values without decimal places 
            let node = "";
            if (res[i].reached) {
                node = "<tr style='color:#009432;'>"
            } else {
                node = "<tr>"
            }
            node += "<td>"+ res[i].name + "</td><td>"+ Number(progress) +" "+ res[i].suffix +"</td></tr>";
            self.$("#"+id).append(node);
        }
    }

    KanbanRecord.include({
        _render: function() {
        var res = this._super.apply(this, arguments);
        var self = this;
            // Only pull data for the dashboard if it's in the dashboard object
            if (this.modelName == "metro.dashboard.tile") {
                const self = this;
                if (this.recordData.line_count) {
                    ajax.jsonRpc("/web/metro_dashboard/get_table_lines/"+this.recordData.id, "call", {})
                        .then(function(res) {
                            appendToTable(self, "table_body", res["30"])
                            appendToTable(self, "table_body90", res["90"])
                        });
                }
        }
        return res;
        },
    });

    return KanbanRecord;

});