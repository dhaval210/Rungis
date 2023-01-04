odoo.define('metro_sales_tour.kanban_column', function (require) {
'use strict';

var KanbanColumn = require('web.KanbanColumn');
var SaleTourKanbanColumnProgressBar = require('metro_sales_tour.kanban_column_progressbar');
var rpc = require('web.rpc');

var SaleTourKanbanRenderer = KanbanColumn.extend({
    template: 'SaleTourKanban.Group',
    events: _.extend(KanbanColumn.prototype.events, {
        'click .o_kanban_map': '_openInGoogleMap'
    }),
    start: function () {
        var defs = [this._super.apply(this, arguments)];
        if (this.barOptions) {
            this.$header.find('.o_kanban_counter').remove()
            this.$el.addClass('o_kanban_has_progressbar');
            this.progressBar = new SaleTourKanbanColumnProgressBar(this, this.barOptions, this.data);
            defs.push(this.progressBar.appendTo(this.$header));
        }
        return $.when.apply($, defs);
    },
    _openInGoogleMap: function(ev){
        let partners = []
        for(let rec of this.data_records){
            let id = rec.data.partner_id.data.id
            if(!partners.includes(id)){
                partners.push(id);
            }
        }
        let base_url = 'https://www.google.com/maps/dir/' + this.tour_name
        rpc.query({
            model: 'res.partner',
            method: 'read',
            args: [partners, ['street', 'city', 'country_id']],
        }).then(data => {
            for(let loc of data){
                base_url += `/${loc.street},+${loc.city},+${loc.country_id[1]}`
            }
            window.open(base_url, '_blank');
        });
    }
})

return SaleTourKanbanRenderer

});