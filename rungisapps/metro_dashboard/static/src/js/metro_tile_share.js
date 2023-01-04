odoo.define("metro_dashboard.share", function(require) {

    const Widget = require("web.Widget");
    const widget_registry = require("web.widget_registry");
    const ajax = require("web.ajax");

    let ShareButton = Widget.extend({
        template: "metro_dashboard.share_button",
        xmlDependencies: [
            "/metro_dashboard/static/src/xml/metro_share_button_template.xml",
        ],
        init: function(parent) {
            this._super(parent);
            this.db = "";
            this.dashboard_view = false;
            this.parent_el = parent.$el;
        },
        willStart: function() {
            const self = this;
            // Get the name of the database
            ajax.jsonRpc("/metro_dashboard/get_db_name", "call", {})
                .then(function(res) {
                    self.db = res["db"];
                });

            return this._super();
        },
        start: function() {

            this.$(".metro_dashboard_share_link").click({"self": this}, this._btnClickedShareLink);
            this.$(".metro_dashboard_share_iframe").click({"self": this}, this._btnClickedShareIframe);

            // Call super with a promise
            return $.when(this._super());
        },
        _generateURL: function() {
            // Get necessary values for building the link
            let id;
            if (typeof this.id == "string") {
                id = this.id;
            } else {
                id = this.el.parentElement.id.split("_")[2];
            }

            const domain = this.el.baseURI.split("/");

            let url = domain[0] + "//"+ domain[2] +"/metro_dashboard/api/tile/"+ id;
            
            // If there is a db specified use it
            if (this.db != "") {
                url += "?db="+this.db;
            }

            console.log("[ShareButton] Generated URL: " + url)

            return url;
        },
        _copyToClipboard: function(txt) {
            console.log("[ShareButton] Copying to clipboard...")
            let dummy = document.createElement("input");
            document.body.appendChild(dummy);

            dummy.value = txt;
            dummy.select();

            document.execCommand("copy");
            document.body.removeChild(dummy);
            console.log("[ShareButton] Successfully copied to clipboard!")
        },
        _btnClickedShareLink: function(event) {
            // Get class object
            let self;
            if (typeof event.data != "undefined") {
                self = event.data.self;
            } else {
                self = event;
            }

            let url = self._generateURL()

            self._copyToClipboard(url);
        },
        _btnClickedShareIframe: function(event) {
            let self;
            if (typeof event.data != "undefined") {
                self = event.data.self;
            } else {
                self = event;
            }
            let width = 300, height = 300;

            // Get the right sizing if we are inside the dashboard view
            if (self.parent_el.hasClass("oe_kanban_card")) {
                let buttonbar_height = self.parent_el.find(".button_bar").outerHeight();
                width = self.parent_el.outerWidth();
                let tile_height = self.parent_el.outerHeight();
                const ratio = (tile_height - buttonbar_height) / width;
                // Since double_width field is not available here we
                // use the value inbetween the two available tile sizes
                if (width > 450) {
                    width = 610;
                } else {
                    width = 310;
                }
                // The button bar is not displayed in the API so substract the height of it
                // The header on the API is a little bit smaller (roundabout 10px)
                height = width * ratio;
            }

            let url = self._generateURL();

            const node = "<iframe width='"+ width +"px' height='"+ height +"px' src='"+ url +"'></iframe>";

            self._copyToClipboard(node);
        }
    });

    widget_registry.add("metro_share_button", ShareButton);

    return ShareButton;

});