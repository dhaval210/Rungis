odoo.define('metro_gate_management.BasicModel', function (require) {
    "use strict";
    var BasicModel = require('web.BasicModel');

    BasicModel.include({
        OPEN_GROUP_LIMIT: 30, // after this limit, groups are automatically folded
    })
});
