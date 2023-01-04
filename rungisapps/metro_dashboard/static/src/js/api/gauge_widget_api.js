odoo.define("metro_dashbaord.gauge_api", function(require) {
    "use strict";

    $(document).ready(function() {
        let gaugeTags = $(".gauge");
        
        for (let i = 0; i < gaugeTags.length; i++) {
            // Get necessary parameters
            let curr = $(gaugeTags[i])
            const tile_id = gaugeTags[i].id.split("_")[1];
            let value, max_value, suffix, label;
            try {
                value = Number(curr.find(".current").html());
                label = curr.find(".label").html();
                max_value = Number(curr.find(".target").html());
                suffix = curr.find("#suffix_"+tile_id).html();
            } catch(err) {
                console.log(err);
                return;
            }

            // Empty the Gauge div
            curr.empty();

            // Gauge Widget Code
            var degree = Math.PI/180,
                width = 200,
                height = 150,
                outerRadius = Math.min(width, height)*0.5,
                innerRadius = outerRadius*0.7,
                fontSize = height/7;

            var arc = d3.svg.arc()
                    .innerRadius(innerRadius)
                    .outerRadius(outerRadius)
                    .startAngle(-90*degree);

            // Create SVG Element
            let svg = d3.select(gaugeTags[i])
                .insert("svg")
                .attr("width", '100%')
                .attr("height", '100%')
                .attr('viewBox','0 0 '+width +' '+height )
                .attr('preserveAspectRatio','xMinYMin')
                .append("g")
                .attr("transform", "translate(" + (width/2) + "," + (height-(width-height)/2-12) + ")");

            function addText(text, fontSize, dx, dy) {
                return svg.append("text")
                    .attr("text-anchor", "middle")
                    .style("font-size", fontSize+'px')
                    .attr("dy", dy)
                    .attr("dx", dx)
                    .text(text);
            }
            // top title
            addText("Current Value", 16, 0, -outerRadius-16).style("font-weight",'bold');

            // center value
            if (suffix == "%") {
                addText(label + "%", fontSize, 0, -2).style("font-weight",'bold');
            } else {
                addText(label, fontSize, 0, -2).style("font-weight",'bold');
            }
            

            // bottom label
            addText(0, 8, -(outerRadius+innerRadius)/2, 12);
            // addText("", 8, 0, 12);
            addText(max_value, 8, (outerRadius+innerRadius)/2, 12);

            // chart
            svg.append("path")
                .datum({endAngle: Math.PI/2})
                .style("fill", "#ddd")
                .attr("d", arc);
                
            var ratio = max_value ? value/max_value : 0;
            var hue = Math.round(ratio*120);

            // Foreground
            if (value > max_value) {
                svg.append("path")
                    .datum({endAngle: (90*degree)})
                    .style("fill", "hsl("+ hue + ",80%,50%)")
                    .attr("d", arc)
            } else if (value < 0) {
                svg.append("path")
                    .datum({endAngle: (-90*degree)})
                    .style("fill", "hsl("+hue+",80%,50%)")
                    .attr("d", arc)
            } else {
                svg.append("path")
                    .datum({endAngle: ((value / max_value - 0.5) * Math.PI)})
                    .style("fill", "hsl("+ hue +",80%,50%)")
                    .attr("d", arc);
            }
        }
    })
});