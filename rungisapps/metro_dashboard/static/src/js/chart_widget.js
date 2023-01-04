odoo.define("metro_dashboard.Chart", function(require) {
    "use strict";

    const Widget = require("web.Widget");
    const widget_registry = require("web.widget_registry");
    const ChartBase = require("metro_dashboard.ChartBase")

    let ChartWidget = Widget.extend({
        template: "metro_dashboard.chart_template",
        xmlDependencies: [
            "/metro_dashboard/static/src/xml/metro_chart_template.xml"
        ],
        init: function(parent) {
            this._super(parent);

            // Initialize most important variables
            this.keys = parent.recordData.keys || "";

            // Convert the string of keys sperated by a komma
            // Into an array
            if (this.keys != "") {
                this.keys = this.keys.split("\\s").map((elem) => elem.trim());
            }

            this.data = {
                "result": parent.recordData.result || "[]",
                "keys": this.keys,
                "name": parent.recordData.name,
                "visualisation": parent.recordData.visualisation,
                "suffix": parent.recordData.suffix,
                "data_source": parent.recordData.data_source
            }
        },
        start: function() {
            const canvas = this.el.children[0]

            this.data["canvas"] = canvas
            
            let chart = new ChartBase(this.data)
            chart.generateChart()

            return $.when(this._super());
        },
    });

    // Add to registry for using it later with the
    // widget tag
    widget_registry.add("metro_dashboard_chart", ChartWidget);

    return ChartWidget;
});