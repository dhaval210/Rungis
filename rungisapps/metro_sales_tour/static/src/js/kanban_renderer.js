odoo.define('metro_sales_tour.kanban_renderer', function (require) {
'use strict';

var KanbanRenderer = require('web.KanbanRenderer');
var KanbanView = require('web.KanbanView');
var SaleTourKanbanColumn = require('metro_sales_tour.kanban_column');
var view_registry = require('web.view_registry');

var SaleTourKanbanRenderer = KanbanRenderer.extend({
    config: _.extend(KanbanRenderer.prototype.config, {
        KanbanColumn: SaleTourKanbanColumn
    })
})

var SaleTourKanbanView = KanbanView.extend({
    config: _.extend(KanbanView.prototype.config, {
        Renderer: SaleTourKanbanRenderer
    })
})

view_registry.add('sale_tour_kanban', SaleTourKanbanView);

return SaleTourKanbanColumn

});