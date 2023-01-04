/* global angular */

angular.module('mobile_app_picking').factory(
    'ScanMoveModel', [
    '$q', 'jsonRpc',
    function ($q, jsonRpc) {

        return {
            get_list: function (picking) {
                // Get moves for a given picking
                var self = this;

                return jsonRpc.call(
                    'mobile.app.picking', 'get_moves', [{ 'picking': picking }]
                ).then(function (moves) {
                    moves.forEach(function (move) {
                        self.compute_state(move);
                    });

                    return moves;
                });
            },

            compute_state: function (move) {
                if (move.qty_done === 0) {
                    move.state = 'unset';
                    move.display_state = 'display_allways';
                } else if (move.qty_done < move.qty_expected) {
                    move.state = 'pending';
                    move.display_state = 'display_allways';
                } else if (move.qty_done === move.qty_expected) {
                    move.state = 'done';
                    move.display_state = 'display';
                } else {
                    move.state = 'too_much';
                    move.display_state = 'display_allways';
                }
            },

            save_line: function (move, qtyDone, isLocation = false) {
                var self = this;
                var qtyDoneFloat = parseFloat(qtyDone, 10);
                var cw_qty_done = move.cw_qty_done;
                if (isLocation) {
                    cw_qty_done = move.product_cw_uom_qty;
                }
                return jsonRpc.call(
                    'mobile.app.picking', 'save_line',
                    [{ 'move': move, 'qty_done': qtyDoneFloat, 'lot_mhd': move.lot_mhd, 'lot_name': move.lot_name, 'pack_number': move.pack_number, 'cw_qty_done': cw_qty_done, 'location_dest_id': move.location_dest_id }]
                ).then(function (res) {
                    move.qty_done = qtyDoneFloat;
                    self.compute_state(move);
                    return res;
                });
            },

            new_location_line: function (move) {
                if (!move.lot_mhd && move.pack_mhd) {
                    move.lot_mhd = move.pack_mhd;
                }
                return jsonRpc.call(
                    'mobile.app.picking', 'save_new_line',
                    [move]
                ).then(function (res) {
                    // self.compute_state(move);
                    return res;
                });
            },

            generate_picking_pdf: function (picking_id) {

                return jsonRpc.call(
                    'mobile.app.picking', 'print_picking', [picking_id.toString()]
                ).then(function (res) {
                    return res;
                });

            },

            picking_by_scan: function (barcode, operation, picking) {
                return jsonRpc.call(
                    'mobile.app.picking', 'get_picking_by_scan', [barcode, operation, picking]
                ).then(function (res) {
                    return res;
                });
            },

            get_by_id: function (pickingId, moveId) {
                return this.get_list({ 'id': pickingId }).then(function (moves) {
                    var foundMove = false;
                    moves.forEach(function (move) {
                        if (move.id === moveId) {
                            foundMove = move;
                        }
                    });
                    return foundMove;
                });
            },

            set_move_vals: function (barcode) {
                var qty_scope = angular.element(document.getElementById('qty_done'));
                var weight_scope = angular.element(document.getElementById('weight'));
                var lot_scope = angular.element(document.getElementById('lot'));
                var mhd_scope = angular.element(document.getElementsByClassName('md-datepicker-input'));                    
                // var pack_scope = angular.element(document.getElementById('pack'));

                var controller_scope = angular.element(document.getElementById('main_move')).scope();
                console.log(controller_scope.data);

                // get values from gs1 barcode by rpc
                return jsonRpc.call(
                    'mobile.app.picking', 'decode_gs1_barcode',
                    [barcode]
                ).then(function (res) {
                    if (res === false) {
                        controller_scope.data.errorMessage = 'not a gs1 barcode.';
                    } else {
                        var set_value = false;
                        controller_scope.data.errorMessage = '';
                        if (qty_scope.length && res.qty != false) {
                            qty_scope.val(res.qty);
                            // controller_scope.data.currentMove.qty_done = res.qty;
                            controller_scope.data.inputData = res.qty;                      
                            set_value = true;
                        }
                        if (weight_scope.length && res.weight != false && controller_scope.data.currentMove.catch_weight_ok) {
                            weight_scope.val(res.weight);
                            // controller_scope.data.currentMove.cw_qty_done = res.weight;
                            controller_scope.data.catchWeight = res.weight;
                            set_value = true;
                        }
                        if (lot_scope.length && res.lot != false) {
                            lot_scope.val(res.lot);
                            controller_scope.data.lotName = res.lot;
                            set_value = true;
                        }
                        if (mhd_scope.length && res.mhd != false) {
                            mhd_scope.val(res.mhd);
                            controller_scope.data.bestBefore = res.mhd;
                            set_value = true;
                        }
                        // if (pack_scope.length && res.pack != false) {
                        //     pack_scope.val(res.pack); 
                        //     controller_scope.data.packNumber = res.pack;
                        // }
                        if (!set_value) {
                            controller_scope.data.errorMessage = 'no valid data in gs1 barcode.';
                        }
                    }
                });
            }

        };
    }]);
