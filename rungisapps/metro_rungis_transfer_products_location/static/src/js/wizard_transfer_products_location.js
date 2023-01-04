odoo.define("metro_rungis_transfer_products_location.wizard_transfer_products_location", function(require) {
    "use strict"

    let Field = require("web.basic_fields").FieldChar
    let registry = require("web.field_registry")
    let core = require("web.core")

    let FieldLocationChar = Field.extend({
        events: {
            "textInput": "_textInputEvent",
            "keydown": "_keyDown",
        },
        _textInputEvent: function(e) {
            let barcode = $(e.currentTarget).val() || e.originalEvent.data;
            // If user enters something, don't try to find a location by the barcode.
            // If entered value has at least 3 characters, the function will be executed (when user enters, usually 1 character is returned)
            if (!barcode || barcode.length < 3 || barcode.isNaN) {
                // Overwriting that function seems to disable the generation of the dropdown
                // this._super.apply(this, arguments)
                return
            }
            const self = this;
            this._rpc({
                model: 'stock.location.transfer.wizard',
                method: 'get_location_by_barcode',
                args: [barcode]
            }).then((res) => {
                self._setValue({
                    id: res
                });
                if (!res) {
                    console.error("No location found for barcode " + barcode)
                }
            },(err)=>{
            console.log(err);
            })
        },
        _keyDown: function(e) {
            if(e.keyCode ==13 || e.keyCode == 9){
            let barcode = $(e.currentTarget).val() || e.originalEvent.data;
            // If user enters something, don't try to find a location by the barcode.
            // If entered value has at least 3 characters, the function will be executed (when user enters, usually 1 character is returned)
            if (!barcode || barcode.length < 3 || barcode.isNaN) {
                // Overwriting that function seems to disable the generation of the dropdown
                // this._super.apply(this, arguments)
                return
            }
            const self = this;
            this._rpc({
                model: 'stock.location.transfer.wizard',
                method: 'get_location_by_barcode',
                args: [barcode]
            }).then((res) => {
                self._setValue({
                    id: res
                });
                if (!res) {
                    console.error("No location found for barcode " + barcode)
                }
            },(err)=>{
            console.log(err);
            })}
        },
    });

    registry.add("location_barcode_field", FieldLocationChar)
});
