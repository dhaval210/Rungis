/* global angular */

// Angular.module is a global place for creating, registering and retrieving
// Angular modules
// 'mobile_app_picking' is the name of this angular module example
// (also set in a <body> attribute in index.html)
// the 2nd parameter is an array of 'requires'
angular.module(
  'mobile_app_picking', [
    'ionic', 'ui.router', 'odoo', 'pascalprecht.translate', 'ngMaterial', 'ngMessages'])

  .run(['jsonRpc', '$state', '$rootScope', function (
    jsonRpc, $state, $rootScope) {
    jsonRpc.errorInterceptors.push(function (a) {
      if (a.title === 'session_expired') {
        $state.go('login');
      }
    });
  }])

  .config([
    '$ionicConfigProvider', '$stateProvider', '$urlRouterProvider',
    '$translateProvider',
    function ($ionicConfigProvider, $stateProvider, $urlRouterProvider,
      $translateProvider) {
      $stateProvider
        .state(
          'login', {
            url: '/login',
            templateUrl: '/metro_mobile_app_picking/static/www/views/login.html',
            controller: 'LoginCtrl',
          })
        .state(
          'logout', {
            url: '/logout',
            templateUrl: '/metro_mobile_app_picking/static/www/views/login.html',
            controller: 'LoginCtrl',
          })
        .state(
          'credit', {
            url: '/credit',
            templateUrl: '/metro_mobile_app_picking/static/www/views/credit.html',
            controller: 'CreditCtrl',
          })
        .state(
          'list_picking_type', {
            url: '/list_picking_type',
            templateUrl: '/metro_mobile_app_picking/static/www/views/list_picking_type.html',
            controller: 'ListPickingTypeCtrl',
          })
        .state(
          'list_picking', {
            url: '/picking_type/{picking_type_id:int}/list_picking',
            templateUrl: '/metro_mobile_app_picking/static/www/views/list_picking.html?v=1.2.16',
            controller: 'ListPickingCtrl',
          })
        .state(
          'list_move', {
            url: '/picking_type/{picking_type_id:int}/picking/' +
            '{picking_id:int}/list_move',
            templateUrl: 'views/list_move.html?v=12.0.1.3.18',
            controller: 'ListMoveCtrl',
          })
        .state(
          'main_scan', {
            url: '/picking_type/{picking_type_id:int}/picking/' +
            '{picking_id:int}/main_scan/{move_id:int}',
            templateUrl: 'views/main_scan.html?v=1.3.19',
            controller: 'MainScanCtrl',
          })
        .state(
          'picking_validate', {
            url: '/picking_type/{picking_type_id:int}/picking/' +
            '{picking_id:int}/picking_validate/',
            templateUrl: 'views/picking_validate.html',
            controller: 'PickingValidateCtrl',
          });

      $ionicConfigProvider.views.transition('none');

      $urlRouterProvider.otherwise('/login');

      $translateProvider.useStaticFilesLoader({
        prefix: 'i18n/',
        suffix: '.json',
      }).registerAvailableLanguageKeys(['en', 'fr'], {
        'en': 'en',
        'en_GB': 'en',
        'en_US': 'en',
        'fr': 'fr',
      })
        .preferredLanguage('en')
        .fallbackLanguage('en')
        .determinePreferredLanguage()
        .useSanitizeValueStrategy('escapeParameters');
    }
  ])

  .controller('AppCtrl', [
    '$scope', '$state', '$stateParams', '$rootScope', '$translate', 'MoveModel',
    'tools', 'PickingModel', 'PickingTypeModel', 'ScanPickingModel', 'ScanMoveModel', 'ScanLocationModel',
    function ($scope, $state, $stateParams, $rootScope, $translate, MoveModel,
      tools, PickingModel, PickingTypeModel, ScanPickingModel, ScanMoveModel, ScanLocationModel) {
      $rootScope.$on('$stateChangeError', console.log.bind(console));
      $scope.$on('$stateChangeSuccess',
        function (evt, toState, toParams, fromState, fromParams) {
          // For side menu
          $rootScope.currentState = toState.name;
          $rootScope.params = toParams;
          $scope.showAlert = '';
          $scope.showSpinner = false;
          $scope.isLotPackFound = false;
          $rootScope.lastScanMoved = [];          
        }
      );


      /**
      * Show spinner
      **/
      $scope.$on('handleBroadcastSpinner', function(event, data) {        
        $scope.showSpinnerFunc(data);
      });
      $scope.showSpinnerFunc = function(value) {  
        // $scope.$apply(function () {
          $scope.showSpinner = value;
        // });
      };

      /**
      * On scan error display message
      **/
      $scope.showAlertFunc = function(value) {          
        // $scope.showAlert = value;
        setTimeout(function () {
          $scope.$apply(function () {
            $scope.showAlert = value;
          });
        }, 500);
      };

      /**
      * Clear last scan product
      **/
      $scope.clearLastScan = function() {
        $rootScope.lastScan = {
          'pickingTypeId' : '',
          'pickingId' : '',
          'move' : '',
          'qtyDone' : 0,
        };
        localStorage.removeItem('lastScan');
      };

      /**
      * On scan of discard barcode
      * Jump to picking type list
      **/
      $scope.redirectToPickingType = function() {
        $scope.clearLastScan();
        $state.go('list_picking_type', {});
      }

      /**
      * Trigger print function in list move
      **/
      $scope.click_print_operation = function() {
        $scope.clearLastScan();
        if($rootScope.currentState == 'list_move'){ 
          $scope.showAlertFunc('');
          $rootScope.$broadcast('handleBroadcastPrintOperation');
        } else {
          $scope.showAlertFunc('Only possible inside a picking.');
        }
      }
      
      /**
      * Global scan event handle
      **/
      $scope.customScanCall = function(value) {
        // List Move Quantity Update
        if($rootScope.currentState == 'list_move'){
          $scope.showAlertFunc('');
          $scope.picking_update_product_qty(value);
          $scope.showSpinnerFunc(false);
        }  else if ($rootScope.currentState == 'main_scan') {
            ScanMoveModel.set_move_vals(value);
            $scope.showSpinnerFunc(false);
            $scope.showAlertFunc('');
        } else if($rootScope.currentState != 'main_scan') {
          $scope.barcode_scaning_api(value, $stateParams.picking_type_id, $stateParams.picking_id);
        }

      };

      /**
      * On scan of picking barcode
      * Jump to picking list
      **/
      $scope.jump_to_picking_list = function (inputValue,picking_type_id) {
        // if (tools.is_barcode(inputValue)) {
          ScanPickingModel.get_picking_by_barcode(
            picking_type_id,
            inputValue).then(function (receipt) {       
              
            if(receipt) {
              $scope.clearLastScan();
              $state.go('list_move', {
                picking_type_id: picking_type_id,
                picking_id: receipt.id,
              });
              $rootScope.$broadcast('handleBroadcastMoveLoad');
            }
          });  
        // }
      };
      
      /**
      * On scan of product barcode
      * Update product quantity
      **/
      $scope.picking_update_product_qty = function (inputValue) {
        // if (tools.is_barcode(inputValue)) {
          MoveModel.get_by_barcode_product(
            $stateParams.picking_id,
            inputValue).then(function (moves) {

            if (moves.length === 0) {
              $scope.barcode_scaning_api(inputValue, $stateParams.picking_type_id, $stateParams.picking_id);
            } else if (moves.length > 1) {
              PickingTypeModel.get_list().then(function (pickingTypes) {
                if (pickingTypes.length > 0) {
    
                  pickingTypes.forEach(pickingTypeItem => {
                      var pickingTypeItemId = pickingTypeItem.id;
                      
                      if($stateParams.picking_type_id == pickingTypeItemId) {
                        
                        if(!pickingTypeItem.disable_product_scan){
                          $state.go('main_scan', {
                            picking_type_id: $rootScope.params.picking_type_id,
                            picking_id: $rootScope.params.picking_id,
                            move_id: moves[0].id,
                          });
                        }                        
                      }
                  });
                }
              });

            } else {
              // The exact move has been found
              $scope.clearLastScan();

              PickingTypeModel.get_list().then(function (pickingTypes) {
                // Picking type details
                
                if (pickingTypes.length > 0) {
                  pickingTypes.forEach(pickingTypeItem => {
                      var pickingTypeItemId = pickingTypeItem.id;
                      
                      if($stateParams.picking_type_id == pickingTypeItemId) {  
                        if(!pickingTypeItem.disable_product_scan){
                          $state.go('main_scan', {
                            picking_type_id: $rootScope.params.picking_type_id,
                            picking_id: $rootScope.params.picking_id,
                            move_id: moves[0].id,
                          });
                        }
                      }
                  });
                }
              });
            }
          });  
        // }
      };

      /**
      * On scan of lot's and packs barcode
      * Jump to move list
      **/ 
      $scope.move_list_scanning_by_lots_packs = function (inputValue, pickingTypeItemId, pickingItemId, pickingTypeItemNew) {

        ScanMoveModel.get_list({id: pickingItemId})
        .then(function (moves) {
          if(moves.length > 0){
    
            $scope.isLocationFound = true;

            moves.forEach(moveItem => {
              
              var lotId = moveItem.lot_id ? moveItem.lot_id : '';
              var packId = moveItem.package_id ? moveItem.package_id : ''; 

              // Match scanned barcode to move lots and packs
              if((packId.toLowerCase() == inputValue.toLowerCase() && pickingTypeItemNew.disable_package_scan == false) || (lotId.toLowerCase() == inputValue.toLowerCase() && pickingTypeItemNew.disable_lot_scan == false)){
                
                // if(!pickingTypeItemNew.disable_product_scan){

                  $scope.isLotPackFound = true;
                  // if(moveItem.qty_done != moveItem.qty_expected) {

                    if($rootScope.currentState == 'list_move'){ 

                      if( $stateParams.picking_id == pickingItemId){

                        if($rootScope.lastScan && $rootScope.lastScan.pickingTypeId != ''){
                          // Picking is already scanned and highlighted as yellow
                          var lastMove = $rootScope.lastScan.move;

                          // Added check whether the scanned product is the same which was scanned last time
                          if(lastMove['id'] != moveItem.id || $rootScope.lastScan.pickingTypeId != pickingTypeItemId || $rootScope.lastScan.pickingId != pickingItemId){
                            
                              $scope.clearLastScan();
                              $rootScope.$broadcast('handleBroadcastMoveLoad');
                              // Check highlight picking status
                              if($scope.highlightPicking == false){
                                var newQty = 0;
                                if(packId.toLowerCase() == inputValue.toLowerCase()){
                                  newQty = moveItem.qty_expected;
                                } else if(lotId.toLowerCase() == inputValue.toLowerCase()){
                                  newQty = (moveItem.qty_done + 1);
                                }
                                newQty = (newQty > moveItem.qty_expected) ? moveItem.qty_expected : newQty;

                                MoveModel.set_quantity(moveItem, newQty).then(function () {
                                  // Quantity Updated  
                                  $rootScope.$broadcast('handleBroadcastMoveLoad');
                                });

                              } else {
                                // Last Scanned Quantity Updated
                                if ($scope.showLocationInfo) {
                                  $scope.update_last_scan(inputValue, moveItem, pickingTypeItemId, pickingItemId, lotId, packId);
                                }
                              }

                            // });
                          } else {
                            // When same product is scanned again for package transfer
                            // Currently no action is taken
                          }

                        } else {
                          // Scanned picking is to be highlighted as yellow as per status
                          // Check highlight picking status
                          if($scope.highlightPicking == false){
                            $scope.clearLastScan();
                            $rootScope.$broadcast('handleBroadcastMoveLoad');


                            var newQty = 0;
                            if(packId.toLowerCase() == inputValue.toLowerCase()){
                              newQty = moveItem.qty_expected;
                            } else if(lotId.toLowerCase() == inputValue.toLowerCase()){
                              newQty = (moveItem.qty_done + 1);
                            }
                            newQty = (newQty > moveItem.qty_expected) ? moveItem.qty_expected : newQty;

                            MoveModel.set_quantity(moveItem, newQty).then(function () {
                              // Quantity Updated  
                              $rootScope.$broadcast('handleBroadcastMoveLoad');
                            });

                          } else {
                            // highlight picking as yellow and update quantity locally
                            $scope.update_last_scan(inputValue, moveItem, pickingTypeItemId, pickingItemId, lotId, packId);
                          }
                        }

                      } else {

                        $state.go('list_move', {
                          picking_type_id: pickingTypeItemId,
                          picking_id: pickingItemId,
                        });
                        $rootScope.$broadcast('handleBroadcastMoveLoad');
                      }

                    } else {
                      $state.go('list_move', {
                        picking_type_id: pickingTypeItemId,
                        picking_id: pickingItemId,
                      });
                      $rootScope.$broadcast('handleBroadcastMoveLoad');
                    }

                  // } else if(moveItem.qty_done == moveItem.qty_expected) {
                  //   $scope.showAlertFunc($translate.instant('Not found'));
                  // }

                // }

              } else {
                // Check scanned barcode is a validate location

                var lastMove = $rootScope.lastScan ? $rootScope.lastScan['move'] : '';
                var qtyDone = $rootScope.lastScan ? $rootScope.lastScan['qtyDone'] : 0;

                if( lastMove && $scope.isLocationFound){
                  
                  $scope.isLocationFound = false;

                  ScanLocationModel.get_available_locations().then(function (locations) {

                    angular.forEach(locations, function(value, key) {
                      // Check scaned location

                      var isLocationFound = true;
                      
                      if(key.toLowerCase() == inputValue.toLowerCase() && isLocationFound == true){

                        isLocationFound = false;

                        // Check highlight picking status
                        if($scope.highlightPicking == true){
                          let parentPath = value.parent_path.split('/').map(x=>+x);
                          
                          if(parentPath.includes(lastMove.location_dest_id)){
                            
                            lastMove.qty_done = qtyDone;
    
                            // MoveModel.set_quantity(lastMove, newQty).then(function () {
                              $scope.move_to_location(value, lastMove);
                            // });
                            
                          } else {
                            $scope.showAlertFunc($translate.instant('Invalid location for selected package'));
                          }

                        }
                      }
                    });
                  },
                  function(data) {
                    // Handle error here
                    console.log("error : ",data);                    
                  });
                }
                
              }

            });
          }
        })          

      }

      $scope.handleInternalWithLocations = function (inputValue, pickingTypeItemId, pickingItemId, pickingTypeItemNew) {
        ScanMoveModel.get_list({id: pickingItemId})
        .then(function (moves) {
          if(moves.length > 0){
    
            $scope.validScannedLocation = null;
            $scope.isPackOrLot = false;
            
            moves.forEach(moveItem => {
              
              var lotId = moveItem.lot_id ? moveItem.lot_id : '';
              var packId = moveItem.package_id ? moveItem.package_id : '';

              if((packId.toLowerCase() == inputValue.toLowerCase() && pickingTypeItemNew.disable_package_scan == false) || (lotId.toLowerCase() == inputValue.toLowerCase() && pickingTypeItemNew.disable_lot_scan == false)) {
                if (moveItem.qty_done != moveItem.qty_expected) {
                  $scope.update_last_scan(inputValue, moveItem, pickingTypeItemId, pickingItemId, lotId, packId);
                  $scope.isPackOrLot = true;
                  return;
                }
              }
            });

            
            if (!$scope.isPackOrLot) {
              // get locations for last scan and check if scanned is valid
              if (!$scope.validScannedLocation && $rootScope.lastScan) {
                if ($rootScope.lastScan.move.lot_id.toLowerCase() != inputValue.toLowerCase() || $rootScope.lastScan.move.package_id.toLowerCase() != inputValue.toLowerCase()) {

                  ScanLocationModel.get_all_locations($rootScope.lastScan.move.location_dest_id, $rootScope.lastScan.move.product.id, $scope.op_def_loc_id).then(function (locations) {
                    angular.forEach(locations, function(location, barcode) {
                      if (inputValue.toLowerCase() == barcode.toLowerCase() && $scope.validScannedLocation === null) {
                        $scope.validScannedLocation = location;
                        return;
                      }
                    });

                    if($scope.validScannedLocation !== null) {
                      // send this to new place!
                      var move = $rootScope.lastScan.move;
                      move['qty_done'] = $rootScope.lastScan.qtyDone;
                      if(move.catch_weight_ok) {
                        move['cw_qty_done'] = $rootScope.lastScan.cwQtyDone;
                      }

                      if(pickingItemId == move['picking_id']) {
                        $scope.move_to_location($scope.validScannedLocation, move);
                      }
                    }
                  });
                }
              }
            }
          }
        });
      }

      $scope.update_last_scan = function (inputValue, moveItem, pickingTypeItemId, pickingItemId, lotId = '', packId = '') {
        var newQty = 0;
        if(packId.toLowerCase() == inputValue.toLowerCase() || (lotId.toLowerCase() == inputValue.toLowerCase())){
          newQty = moveItem.qty_expected;
        } else if(lotId.toLowerCase() == inputValue.toLowerCase()){
          if($rootScope.lastScan && $rootScope.lastScan.move.id == moveItem.id) {
            newQty = ($rootScope.lastScan.qtyDone + 1);
          } else {
            newQty = (moveItem.qty_done + 1);
          }
        }
        newQty = (newQty > moveItem.qty_expected) ? moveItem.qty_expected : newQty;

        // Catchweight
        if (moveItem.catch_weight_ok) {
          var newCwQty = 0;
          if(packId.toLowerCase() == inputValue.toLowerCase()) {
            newCwQty = moveItem.product_cw_uom_qty;
          } else if(lotId.toLowerCase() == inputValue.toLowerCase()) {
            newCwQty = (newQty / moveItem.qty_expected) * moveItem.product_cw_uom_qty;
          }
        }

        $rootScope.lastScan = {
          'pickingTypeId' : pickingTypeItemId,
          'pickingId' : pickingItemId,
          'move' : moveItem,
          'qtyDone' : newQty,
          'cwQtyDone': newCwQty
        }; 

        localStorage.setItem('lastScan',JSON.stringify($rootScope.lastScan));
        $rootScope.$broadcast('handleBroadcastMoveLoad');
      }

      $scope.move_to_location = function (location, move) {
        if (move.qty_done !== move.qty_expected) {
          if(move.catch_weight_ok) {
            move['cw_qty_done'] = $rootScope.lastScan['cwQtyDone'];
          }
          
          move['qty_done'] = $rootScope.lastScan['qtyDone'];
          move['location_dest_id'] = location.id;

          ScanMoveModel.new_location_line(move).then(function (res) {
            if(res) {
              if($rootScope.lastScan.pickingId) {
                $rootScope.lastScanMoved.push($rootScope.lastScan['move']);
              }
              
              $scope.clearLastScan();                    
              $rootScope.$broadcast('handleBroadcastMoveLoad');  
              $scope.showAlertFunc('');
            }
          });
        } else {
          move['location_dest_id'] = location.id;
          ScanMoveModel.save_line(move, move.qty_done, true).then(function (res) {

            if(res){
              if($rootScope.lastScan.pickingId){
                $rootScope.lastScanMoved.push($rootScope.lastScan['move']);
              }
              $scope.clearLastScan();                    
              $rootScope.$broadcast('handleBroadcastMoveLoad');  
              $scope.showAlertFunc('');
            }
            
          },
          function(data) {
            // Handle error here
            if(data.fullTrace.data.message != ''){
              $scope.data.errorMessage = data.fullTrace.data.message;
            } else {
              $scope.data.errorMessage = "Something went wrong, please try again.";
            }
            
          });
        }
      }

      /**
      * On scan of barcode
      * Jump to picking list using endpoint response
      **/ 
      $scope.barcode_scaning_api = function (inputValue, operation_type, picking_id) {
        
        ScanMoveModel.picking_by_scan(inputValue, operation_type, picking_id).then(function (res) {
          if(res == false) {
            if ($state.current.name === 'list_move') {
              if ($scope.showLocationInfo) {
                $scope.scan_operations(inputValue);
              } else {
                // handle highlighted mode - maybe merge them together?
                ScanLocationModel.get_available_locations().then(function (locations) {
                  var isLocationFound = false;
                  angular.forEach(locations, function(value, key) {                  
                    if(key.toLowerCase() == inputValue.toLowerCase())
                    {
                      isLocationFound = true;
                      $scope.scan_operations(inputValue);
                    }
                  });
  
                  if(!isLocationFound) {
                    $scope.showAlertFunc($translate.instant('Not found'));
                    $scope.showSpinnerFunc(false);
                  }
                },
                function(data) {
                  // Handle error here
                  console.log("error : ",data);                    
                });
              }
            } else {
              $scope.showAlertFunc($translate.instant('Not found'));
              $scope.showSpinnerFunc(false);
            }
          } else {
            // Call to check scan disabled or not
            ScanMoveModel.picking_by_scan(inputValue, operation_type, picking_id).then(function (resNew) {
              $scope.showAlertFunc('');
              if(resNew != false) {
                if(($stateParams.picking_type_id != resNew.picking_type_id) || ($stateParams.picking_id != resNew.picking)) {
                  $state.go('list_move', {
                    picking_type_id: resNew.picking_type_id,
                    picking_id: resNew.picking,
                  });
                } else {
                  $scope.scan_operations(inputValue);
                }
              }
            },
            function(data) {
                // Handle error here
                $scope.showAlertFunc(data.fullTrace.data.message);
                $scope.showSpinnerFunc(false);
            });
          }
        },
        function(data) {
            // Handle error here
            $scope.showAlertFunc(data.fullTrace.data.message);
            $scope.showSpinnerFunc(false);
        });
      }

      /**
      * On scan of barcode
      * scan operations
      **/ 
      $scope.scan_operations = function (inputValue) {
        $scope.showAlertFunc('');
        if($stateParams.picking_type_id){

          PickingTypeModel.get_list().then(function (pickingTypes) {
            // Picking type details
            if (pickingTypes.length > 0) {

              pickingTypes.forEach(pickingTypeItem => {
                let operationCode = pickingTypeItem.code;
                let pickingTypeItemId = pickingTypeItem.id;
                let highlightPicking = pickingTypeItem.highlight_picking;
                
                if($stateParams.picking_type_id == pickingTypeItemId) {

                  // if(!pickingTypeItem.disable_product_scan){

                    $scope.highlightPicking = highlightPicking;
                    $scope.showLocationInfo = pickingTypeItem.show_location_info;
                    $scope.op_def_loc_id = pickingTypeItem.op_def_loc_id;

                    PickingModel.get_list({id: pickingTypeItemId})
                    .then(function (pickings) {
                      
                      if(pickings.length > 0){
                        // if $stateParams contains a picking_id filter the pickings for already existing picking_id
                        if ($stateParams.picking_id) {
                          pickings = pickings.filter((p) => p.id === $stateParams.picking_id)
                        }
                        pickings.forEach(pickingItem => {
                          // If operationCode is incoming, but force_internal_process checkbox is checked, go into the internal process
                          if(operationCode == 'incoming' && !pickingTypeItem.force_internal_process){
                            $scope.clearLastScan();
                          } else if(operationCode == 'internal' || (operationCode == "incoming" && pickingTypeItem.force_internal_process)) {
                            if ($scope.showLocationInfo) {
                              $scope.handleInternalWithLocations(inputValue, pickingTypeItemId, pickingItem.id, pickingTypeItem);
                            } else {
                              $scope.move_list_scanning_by_lots_packs(inputValue, pickingTypeItemId, pickingItem.id, pickingTypeItem);
                            }
                          }
                          
                        });
                      }
                    });
                  // }
                }
              });
            }
          });
        }   
      }
    },
  ]);
