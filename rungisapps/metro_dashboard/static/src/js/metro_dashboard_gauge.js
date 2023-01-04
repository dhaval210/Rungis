odoo.define("metro_dashboard.GaugeWidget", function(require) {

    let Gauge = require("web_kanban_gauge.widget");

    Gauge.include({
        _render: function() {
            // Only modify the gauge widget when our model is loaded
            if (this.model == "metro.dashboard.tile") {
                // Get Max Value of Gauge Widget
                let max_value = this.recordData.target;
                // If value is bigger than max_value, set it's value to max_value
                // If value is lower than 0, set it's value to 0
                // Prevents overflow
                if (this.value > max_value || this.value < 0) {
                    let old_val = this.value;
                    this.value = this.value > max_value ? max_value : 0;
                    // Call super() method, so that the gauge widget HTML is built
                    this._super();
                    // Change the center value to current progress
                    // The normal Gauge widget pulls the value from this.value
                    // Since we changed it, it would show the maximum value of the gauge widget
                    let text = this.$("text")[1];
                    // text.innerHTML = this.shortNumber(old_val);

                    if (this.attrs.class == "days30") {
                        text.innerHTML = this.recordData.result_short
                    } else {
                        text.innerHTML = this.recordData.result_short90
                    }

                    if (this.recordData.suffix == "%") {
                        text.innerHTML += "%";
                    }
                    return
                }
            }
            this._super();
        }
    });

});