odoo.define("metro_dashboard.TimeframeDropdown", function(require) {
    "use strict"

    const Widget = require("web.Widget")
    const widget_registry = require("web.widget_registry")

    const timeframeDropdown = Widget.extend({
        template: "metro_dashboard.tile_timeframe_dropdown",
        xmlDependencies: [
            "/metro_dashboard/static/src/xml/metro_dashboard_timeframe_dropdown.xml",
        ],
        init: function(parent) {
            this._super(parent)

            this.value = parent.recordData.result
            this.value90 = parent.recordData.result90
            this.parent = parent
        },
        start: function() {
            const days30Btn = this.el.children[1].children[0]
            const days90Btn = this.el.children[1].children[1]
            const dropdownButton = this.el.children[0]
            const elems30 = this.parent.$(".days30")
            const elems90 = this.parent.$(".days90")

            days30Btn.addEventListener("click", function() {
                dropdownButton.innerHTML = "<i class='fa fa-clock-o'></i> Last 30 days"

                for (let i = 0; i < elems30.length; i++) {
                    $(elems30[i]).attr("hidden", false)
                }

                for (let i = 0; i < elems90.length; i++) {
                    $(elems90[i]).attr("hidden", true)
                }
            })

            days90Btn.addEventListener("click", function() {
                dropdownButton.innerHTML = "<i class='fa fa-clock-o'></i> Last 90 days"

                for (let i = 0; i < elems30.length; i++) {
                    $(elems30[i]).attr("hidden", true)
                }

                for (let i = 0; i < elems90.length; i++) {
                    $(elems90[i]).attr("hidden", false)
                }
            })

            return $.when(this._super())
        }
    })

    widget_registry.add("tile_timeframe_dropdown", timeframeDropdown)
    return timeframeDropdown

})