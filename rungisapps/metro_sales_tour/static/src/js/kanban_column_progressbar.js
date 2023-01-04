odoo.define('metro_sales_tour.kanban_column_progressbar', function (require) {
'use strict';

var KanbanColumnProgressBar = require('web.KanbanColumnProgressBar');
var utils = require('web.utils');
var rpc = require('web.rpc');

var SaleTourKanbanColumnProgressBar = KanbanColumnProgressBar.extend({
    init: function (parent, options, columnState) {
        this._super.apply(this, arguments);
        this.parent = parent;
        this.capacity = 0;
    },
    willStart: async function(){
        let res = await this._super.apply(this, arguments);
        if(this.columnState.res_id){
            await rpc.query({
                model: this.parent.relation,
                method: 'read',
                args: [[this.columnState.res_id], ['capacity', 'street', 'city', 'country_id']],
            }).then(data => {
                this.capacity = data[0].capacity;
                let country = data.country_id ? data.country_id[1]: ''
                this.parent.tour_name = `${data.street},+${data.city},+${country}`
            });
        }
        return res
    },
    _render: function () {
        this._super.apply(this, arguments)
        let $bars = this.$bars;
        let capacity = this.capacity || 1
        let percentage = this.totalCounterValue > 0 ?  Math.round(((this.totalCounterValue / capacity) * 100) * 100) / 100 : 0
        if(percentage > 100){
            this.$($bars.danger[0]).css({width: '100%'});
            this.$($bars.danger[0]).attr('data-original-title', 'more than ' +100 + '%');
            this.$($bars.success[0]).css({width: '0%'});
        } else {
            this.$($bars.success[0]).css({width: `${percentage}%`});
            this.$($bars.success[0]).attr('data-original-title', percentage+ '%');
            this.$($bars.danger[0]).css({width: '0%'});
        }
        var start = this.prevTotalCounterValue;
        var end = this.totalCounterValue;
        if (start !== undefined && (end > start || this.activeFilter) && this.ANIMATE) {
            $({currentValue: start}).animate({currentValue: end}, {
                duration: 1000,
                start: function () {
                    self.$counter.addClass(animationClass);
                },
                step: function () {
                    self.$number.html(_getCounterHTML(this.currentValue) + ' kg');
                },
                complete: function () {
                    self.$number.html(_getCounterHTML(this.currentValue) + ' kg');
                    self.$counter.removeClass(animationClass);
                },
            });
        } else {
            this.$number.html(_getCounterHTML(end) + ' kg');
        }

        function _getCounterHTML(value) {
            return utils.human_number(value, 0, 3);
        }
    },
})

return SaleTourKanbanColumnProgressBar

});