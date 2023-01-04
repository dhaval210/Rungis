odoo.define("metro_dashboard.dashboard_share", function(require) {

    const Widget = require("web.Widget");
    const widget_registry = require("web.widget_registry");
    const ajax = require("web.ajax");

    let DashboardShareButton = Widget.extend({
        template: "metro_dashboard.dashboard_share_button",
        xmlDependencies: [
            "/metro_dashboard/static/src/xml/metro_share_button_template.xml",
        ],
        init: function(parent) {
            this._super(parent);
            this.db = "";
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
            // Get data from parent or
            // Get data from fields
            const link_btn = $(this.$el[0]);
            const iframe_btn = $(this.$el[2]);

            link_btn.click({"self": this}, this.shareLink);
            iframe_btn.click({"self": this}, this.shareIFrame);

            return $.when(this._super());
        },
        shareLink: function(event) {
            const self = event.data.self;

            const url = self._generateUrl();

            self._copyToClipboard(url);
        },
        shareIFrame: function(event) {
            const self = event.data.self;

            const url = self._generateUrl();
            const node = "<iframe width='800px' height='600px' src='"+ url +"'></iframe>";

            self._copyToClipboard(node);
        },
        _generateUrl: function() {
            // Using document.getElementsByTagName because
            // the jQuery selector is not working
            const id = document.querySelector("[name='id']").innerText;
            const domain = this.el.baseURI.split("/");

            let url = domain[0] + "//"+ domain[2] +"/metro_dashboard/api/dashboard/"+ id;
            
            // If there is a db specified use it
            if (this.db != "") {
                url += "?db="+this.db;
            }

            console.log("[ShareButton] Generated URL: " + url)

            return url;
        },
        _copyToClipboard: function(txt) {
            let dummy = document.createElement("input");
            document.body.appendChild(dummy);

            dummy.value = txt;
            dummy.select();

            document.execCommand("copy");
            document.body.removeChild(dummy);
        }
    });

    widget_registry.add("metro_dashboard_share_button", DashboardShareButton);

    return DashboardShareButton;
});