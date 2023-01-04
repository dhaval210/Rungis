odoo.define('tis_web.ProductConfiguratorMixin', function (require) {
'use strict';
    var dom = require('web.dom_ready');
    var core = require('web.core');
    var utils = require('web.utils');
    var ajax = require('web.ajax');
    var _t = core._t;
    var sAnimations = require('website.content.snippets.animation');
    sAnimations.registry.WebsiteSale.include({
        events: _.extend({}, sAnimations.registry.WebsiteSale.prototype.events, {
            'click a.js_add_cart_json': '_onClickAddCartJSON',
            'change input.cw_quantity': '_changeCustomQuantity',
            'change input.quantity': '_onClickAddCartJSON_'
        }),
        check_has_cw_uom_weight: function(pid){
            return this._rpc({
                route: "/shop/cart/check_has_uom_field",
                params: {
                    product_id: this.last_product_id || pid
                },
            });
        },
        _onClickAddCartJSON_: function(ev){
            ev.preventDefault();
            this.check_has_cw_uom_weight().done(function(res){
                if(res > 0){
                    var $link = $(ev.currentTarget);
                    var newQty = parseFloat($link.val()||0,0,10);
                    var $nextinput_group = $link.parent().next().next();
                    var $nextinput = $nextinput_group.find('input');
                    var old_val = parseFloat($nextinput.data('cw_qty'));
                    var new_val = old_val * newQty;
                    new_val = new_val && new_val.toFixed(4) || 0
                    $nextinput.val(new_val).trigger('change');
                }
            });
        },

        onClickAddCartJSON: function(ev){
            ev.preventDefault();
            var self = this;
            var _super = this._super;
            var $link = $(ev.currentTarget);
            var $input = $link.closest('.input-group').find("input");
            var pid =  parseInt($input.data('product-id'), 10);
            var min = parseFloat($input.data("min") || 0);
            var max = parseFloat($input.data("max") || Infinity);
            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val() || 0, 10);
            if($input.hasClass('cw_quantity')){
                quantity = ($link.has(".fa-minus").length ? -0.1 : 0.1) + parseFloat($input.val() || 0, 10);
            }
            var newQty = quantity > min ? (quantity < max ? quantity : max) : min;
            var $nextinput_group = $link.parent().parent().next().next();
            var $nextinput = $nextinput_group.find('input');
            var old_val = parseFloat($nextinput.data('cw_qty'));
            var new_val = old_val * newQty;
            if($link.find('i').hasClass("fa-minus")){
                new_val = old_val * newQty;
            }
            new_val = new_val && new_val.toFixed(4) || 0;
            if($input.hasClass('cw_quantity')){
                newQty = newQty.toFixed(4);
                $input.val(newQty).trigger('change');
            }
            this.check_has_cw_uom_weight(pid).done(function(res){
                if(res > 0){
                    $input.val(newQty).trigger('change');
                    return false;
                }
                else{
                    $input.val(newQty).trigger('change');
                }
            });

        },

        _changeCustomQuantity: function(ev){
            var self = this;
            var $input = $(ev.currentTarget);
            var pid =  parseInt($input.data('product-id'), 10);
            if ($input.data('update_change')) {
                return;
            }
            var value = parseInt($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 1;
            }
            var $dom = $input.closest('tr');
            var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
            var line_id = parseInt($input.data('line-id'), 10);
            var productIDs = [parseInt($input.data('product-id'), 10)];
            var qty = parseFloat($input.val());
            self._rpc({
                route: "/shop/cart/update_json_cw",
                params: {
                    line_id: line_id,
                    product_id: parseInt($input.data('product-id'), 10),
                    set_qty: qty
                },
            });
        },

        _changeCartQuantity: function ($input, value, $dom_optional, line_id, productIDs) {
            var self = this;
            var pid =  parseInt($input.data('product-id'), 10);
            var _super = self._super;
            this.check_has_cw_uom_weight(pid).done(function(res){
                _.each($dom_optional, function (elem) {
                    $(elem).find('.js_quantity').text(value);
                    productIDs.push($(elem).find('span[data-product-id]').data('product-id'));
                });
                $input.data('update_change', true);
                if(res > 0){
                    setTimeout(function(){
                        var $next_input = $('input.cw_quantity[data-line-id="'+line_id+'"]');
                        var old_value = $next_input.val();
                        var qty = parseFloat(value) * parseFloat($next_input.data('cw_qty'));
                        qty = qty && qty.toFixed(4) || 0;
                        $next_input.val(qty).trigger('change');
                        $next_input.data('update_change', false);
                    },5);
                }
                else{
                    setTimeout(function(){
                        var $next_input = $('input.cw_quantity[data-line-id="'+line_id+'"]');
                        var old_value = $next_input.val();
                        $next_input.val(old_value).trigger('change');
                        $next_input.data('update_change', false);
                    },5);
                }
                
                self._rpc({
                route: "/shop/cart/update_json",
                params: {
                    line_id: line_id,
                    product_id: parseInt($input.data('product-id'), 10),
                    set_qty: value
                   },
                 }).then(function (data) {
                    $input.data('update_change', false);
                    var check_value = parseInt($input.val() || 0, 10);
                    if (isNaN(check_value)) {
                        check_value = 1;
                   }
                    if (value !== check_value) {
                        $input.trigger('change');
                        return;
                    }
                    var $q = $(".my_cart_quantity");
                    if (data.cart_quantity) {
                        $q.parents('li:first').removeClass('d-none');
                    }
                    else {
                        window.location = '/shop/cart';
                    }
                    $q.html(data.cart_quantity).hide().fadeIn(600);
                    $input.val(data.quantity);
                    $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);

                    $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
                    $(".js_cart_summary").first().before(data['website_sale.short_cart_summary']).end().remove();

                    if (data.warning) {
                        var cart_alert = $('.oe_cart').parent().find('#data_warning');
                        if (cart_alert.length === 0) {
                            $('.oe_cart').prepend('<div class="alert alert-danger alert-dismissable" role="alert" id="data_warning">'+
                                '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning + '</div>');
                        }
                        else {
                            cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning);
                        }
                        $input.val(data.quantity);
                    }
                });
            });
        },
    })

});
