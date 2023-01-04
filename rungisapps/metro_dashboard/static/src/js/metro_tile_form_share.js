odoo.define("metro_dashboard.tile_form_share", function(require) {

    const widget_registry = require("web.widget_registry");
    const ShareBtn = require("metro_dashboard.share");

    const TileShareBtn = ShareBtn.extend({
        template: "metro_dashboard.dashboard_share_button",
        xmlDependencies: [
            "/metro_dashboard/static/src/xml/metro_share_button_template.xml",
        ],
        start: function() {
            const self = this;

            const share_link = this.el;
            const share_iframe = this.el.nextElementSibling;

            share_link.addEventListener("click", function() { self._btnClickedShareLink(self); });
            share_iframe.addEventListener("click", function() { self._btnClickedShareIframe(self); });

            return this._super();
        },
        _generateURL: function() {
            // Get necessary values for building the link
            const id = document.querySelector("[name='id']").innerText;

            this.id = id;

            return this._super();
        }
    });

    widget_registry.add("metro_tile_form_share", TileShareBtn);

    return TileShareBtn;

});