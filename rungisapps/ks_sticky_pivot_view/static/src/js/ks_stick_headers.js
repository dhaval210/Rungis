odoo.define('ks_odoo12_sticky_pivot.stick_header', function (require) {
'use strict';
    var ks_PivotRenderer = require('web.PivotRenderer');
    var ks_PivotController = require('web.PivotController');
    var ks_Session = require('web.session');
    ks_PivotRenderer.include({
        on_attach_callback: function(){
           var ks_sup = this._super.apply(this, arguments);
           var ks_self = this;
           if(ks_Session.ks_pivot_status_header){
                ks_self.ks_stickPivotView(ks_self);
           }
           $("div[class='o_sub_menu']").css("z-index",4);
           return ks_sup
        },
        on_detach_callback: function () {
           var ks_sup = this._super.apply(this, arguments);
           var ks_self=this;
           //Destroy sticky header when user clicks on same tab
           if(ks_Session.ks_pivot_status_header){
               var ks_o_content_area = $(".o_pivot")[0];
               var ks_el = ks_self.$el;
               if(ks_el.parents(".o_dashboard").length===0){
                       ks_el.each(function () {
                               $(this).stickyTableHeadersPivot('destroy');
                        });
                }
            }
           return ks_sup
        },
        _render:function(ev){
           var ks_sup = this._super.apply(this, arguments);
           if(ks_Session.ks_pivot_status_header){
               this.ks_stickPivotView(this);
           }
           return ks_sup
        },
        ks_stickPivotView:function(el){
           var ks_self=el;
           var ks_o_content_area = $(".o_pivot")[0];
           var ks_el = ks_self.$el;
           if(ks_el.parents(".o_dashboard").length===0){
                   ks_el.each(function () {
                           $(this).stickyTableHeadersPivot({scrollableArea: ks_o_content_area, fixedOffset: 0.1,stickStatus: ks_Session.ks_pivot_status_header});
                    });
            }
           this.ks_stick_frist_Column();
       },
        ks_stick_frist_Column : function(){
            if(ks_Session.ks_pivot_status_header){
             _.each($(".o_pivot table tbody .o_pivot_header_cell_opened"), function(ks_pivot_cell) {
                    $(ks_pivot_cell).css({
                       'left' : '0',
                       'position' : 'sticky'
                    });
                      $(ks_pivot_cell).css({
                       'position' : ' -webkit-sticky;'
                    });
               });
                _.each($(".o_pivot table tbody .o_pivot_header_cell_closed"), function(ks_pivot_cell) {
                    $(ks_pivot_cell).css({
                       'left' : '0',
                       'position' : 'sticky'
                    });
                     $(ks_pivot_cell).css({
                       'position' : ' -webkit-sticky'
                    });
               });
         }
         else{
            $(".ks_header_cell_cover").css({
                "display":"none",
            })
         }

        },
    });
});

