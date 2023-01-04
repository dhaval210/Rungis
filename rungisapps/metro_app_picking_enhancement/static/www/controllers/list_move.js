/* global angular */

angular.module('mobile_app_picking').controller(
    'ListMoveCtrl', [
    '$scope', '$filter', '$state', '$stateParams', 'PickingModel', 'MoveModel',
    'tools', '$rootScope', 'ScanMoveModel', 'PickingTypeModel', '$location','$anchorScroll',
    function ($scope, $filter, $state, $stateParams, PickingModel, MoveModel, tools, $rootScope, ScanMoveModel, PickingTypeModel, $location, $anchorScroll) {

        $scope.HtmlData = '';
        $scope.data = {
            'picking': null,
            'moves': [],
            'display_all': true,
            'filter': 'display',
            'is_lastScanned': false,
        };
                
        $scope.$on(
        '$stateChangeSuccess',
        function (event, toState, toParams, fromState, fromParams) {
            if ($state.current.name === 'list_move') {
                tools.focus();
                $scope.load_move_picking();
                
            }
        });

        /**
        * Broadcast event on quantity update
        * Load move list in picking
        **/
        $scope.$on('handleBroadcastMoveLoad', function(event, data) {
            $scope.load_move_picking();
        });

        /**
        * Fetch picking details by id
        **/
        $scope.load_move_picking = function () {
            // Show loader
            $rootScope.$broadcast('handleBroadcastSpinner', true);
            
            $scope.data.operationCode = null;
            PickingTypeModel.get_list().then(function (pickingTypes) {
                // Picking type details
                if (pickingTypes.length > 0) {
    
                    pickingTypes.forEach(pickingTypeItem => {
                        var pickingTypeItemId = pickingTypeItem.id;
                        
                        if($rootScope.params.picking_type_id == pickingTypeItemId) {
                            $scope.data.showLocationInfo = pickingTypeItem.show_location_info;
                            $scope.data.operationCode = pickingTypeItem.code;
                            $scope.data.highlightPicking = pickingTypeItem.highlight_picking;
                        }
                    });
                }
            });

            PickingModel.get_by_id(
                $rootScope.params.picking_type_id,
                $rootScope.params.picking_id
                ).then(function (picking) {        
           
                    $scope.data.picking = picking;
                    $scope.load_move_list(picking.id);
                });

        }

        /**
        * Fetch product list in picking
        **/
        $scope.load_move_list = function (picking_id) {
            ScanMoveModel.get_list({id: picking_id})
                .then(function (moves) {
                    $scope.data.is_lastScanned = false;
                    $scope.data.moves = moves;
                    
                    var is_valid = true;
                    moves.forEach(element => {
                        if(element.qty_done != element.qty_expected){
                            is_valid = false;
                        }
                    });
                    
                    $scope.checkValidateBtnClass(is_valid);
                    // Hide loader
                    $rootScope.$broadcast('handleBroadcastSpinner', false);
                }).catch(function(err) {
                    // This case resulted in an endless loading screen, no picking id was given
                    // Hide loader
                    tools.display_loading_end();
                    $rootScope.$broadcast('handleBroadcastSpinner', false);
                    // Go back to overview
                    $state.go("list_picking_type")
                });
        }

        /**
        * Broadcast event on print opertion click
        * Call print opertion to create pdf
        **/
        $scope.$on('handleBroadcastPrintOperation', function(event, data) {  
            if($rootScope.currentState == 'list_move'){
                // Show loader
                $rootScope.$broadcast('handleBroadcastSpinner', true);

                var picking = $scope.data.picking;
                ScanMoveModel.generate_picking_pdf(picking.id).then(function (res) {
                    // PDF print is handled at odoo end.
                    // Show loader
                    $rootScope.$broadcast('handleBroadcastSpinner', false);
                },
                function(data) {
                    // Handle error here
                    alert(data);
                    // Show loader
                    $rootScope.$broadcast('handleBroadcastSpinner', false);
                });
            }
        });
        
        $scope.click_display_all = function () {
            if ($scope.data.display_all === true) {
              $scope.data.filter = 'display';
            } else {
              $scope.data.filter = 'display_allways';
            }
        };
    
        $scope.reset_qty = function (move) {
            MoveModel.set_quantity(move, 0).then(function () {
              move.qty_done = 0;
            });
        };
    
        $scope.see_move = function (move) {
            $state.go('main_scan', {
              picking_type_id: $rootScope.params.picking_type_id,
              picking_id: $rootScope.params.picking_id,
              move_id: move.id,
            });
        };

        /*
        * Set validate button class
        */ 
        $scope.checkValidateBtnClass = function (data) {
            if(!data){
                $scope.validate_class = "btn-grey";
            } else {
                $scope.validate_class = "btn-green";
            }
        }

        $scope.checkLastScan = function (data) {
            
            var className = '';

            if($scope.data.highlightPicking == true && data.state == 'done'){
                className = "bg-green";
            }
            
            if($rootScope.lastScan && $rootScope.lastScan.pickingTypeId != ''){
                if(($scope.data.highlightPicking == true || ($scope.data.showLocationInfo && ($scope.data.operationCode != 'incoming' || data.force_internal_process))) && data.id == $rootScope.lastScan.move['id']){
                    if(localStorage.getItem('lastScan')){
                        var lastScan = JSON.parse(localStorage.getItem('lastScan'));
                        var lastMove = lastScan ? lastScan['move'] : '';
                        var qtyDone = lastScan ? lastScan['qtyDone'] : 0;
                        var cwQtyDone = lastScan ? lastScan['cwQtyDone'] : 0;

                        $scope.data.moves.forEach(element => {
                            if(element.id == data.id && lastMove.id == data.id){
                                element.qty_done = qtyDone;
                                if($rootScope.lastScan.move['catch_weight_ok']) {
                                    element.cw_qty_done = cwQtyDone;
                                }
                                $scope.data.is_lastScanned = true;
                                className = "bg-yellow";
                                $location.hash('move-' + element.id);
                                $anchorScroll();
                            }
                        });
                    }
                } 
            }

            if($scope.data.operationCode == 'incoming' && !data.force_internal_process) {
                if(data.qty_done == data.qty_expected) {
                    className = 'bg-grey'
                } else if (data.lot_id && data.qty_done == 0 && (data.lot_mhd || data.pack_mhd)) {
                    className = 'bg-blue'
                }
            }

            return className;
        }
    }]
);
