odoo.define("metro_dashboard.chart_api", function(require) {

    const ChartBase = require("metro_dashboard.ChartBase")

    function getCurrent(obj, canvas) {
        let current = undefined;
        for(let i = 0; i < obj.length; i++) {
            if ($(obj[i]).hasClass("days30") && $(canvas).parent().hasClass("days30")) {
                current = $(obj[i]).html()
            } else if ($(obj[i]).hasClass("days90") && $(canvas).parent().hasClass("days90")) {
                current = $(obj[i]).html()
            }
        }
        return current
    }

    $(document).ready(function() {

        // Get all canvases which are supposed to be charts
        const charts = $(".dashboardChart");
        let results = undefined;
        let keys = undefined;
        let type = undefined;
        let name = undefined;
        let suffix = undefined;
        let curr_key = undefined;

        // Loop through canvases
        for(let i = 0; i < charts.length; i++) {
            // Get the canvas and id
            const canvas = charts.get(i);
            const id = canvas.id.split("_")[1];

            let result = undefined;

            // Get data for the charts while rendering the first one
            if ($(canvas).parent().hasClass("days30")) {
                name = $("#name_"+id).html();
                console.log("Get data for %s", name)
                results = $("#info_"+id+" > .result")

                type = $("#info_"+id+" > .type").html();
                keys = $("#info_"+id+" > .keys") || [];
                suffix = $("#info_"+id+"> .suffix").html() || "";
            }
            // Getting the correct result for the current chart
            result = getCurrent(results, canvas)
            curr_key = getCurrent(keys, canvas)

            if (result != undefined) {
                // Split the string at the commas and remove trailing/leading whitespaces
                let k = curr_key.split("\\s").map((elem) => elem.trim());

                data = {
                    "result": result || "[]",
                    "keys": k || "",
                    "name": name || "Undefined",
                    "visualisation": type,
                    "suffix": suffix || "",
                    "canvas": canvas
                }

                let chart = new ChartBase(data)
                chart.generateChart()
            }

            $("#info_"+id).remove();
        }

    });

});