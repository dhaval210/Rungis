odoo.define("metro_hub_management.departure", function (require) {
    "use strict";
    var ListController = require("web.ListController");
    var rpc = require("web.rpc");

    ListController.include({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (!this.$buttons) {
                return;
            }
            var self = this;
            this.$buttons.on("click", ".departure_button", function () {
                rpc
                    .query({
                        model: "transporter.hub",
                        method: "set_departure_times",
                        args: [
                            {
                                arg1: "",
                            },
                        ],
                    })
                    .done(function (result) {
                        self.trigger_up('reload'); // Reload current view
                    });
            });
        },
    });
});