/* global angular */

angular.module('mobile_app_picking').controller(
  'MainScanCtrl', [
  '$scope', '$rootScope','$filter', '$state', '$translate', '$stateParams', 'MoveModel', 'PickingTypeModel', 'ScanMoveModel', 'tools', '$mdDialog', 'ScanLocationModel', 'jsonRpc',
  function ($scope, $rootScope, $filter, $state, $translate, $stateParams, MoveModel, PickingTypeModel, ScanMoveModel, tools, $mdDialog, ScanLocationModel, jsonRpc) {
    var myDate = new Date();
    var minDate = new Date(
      myDate.getFullYear(),
      myDate.getMonth(),
      myDate.getDate()
      );
      
      $scope.reset = function(){
        $scope.data = {
          'inputData': null,
          'currentMove': null,
          'errorMessage': null,
          'lotName': null,
          'packNumber': null,
          'catchWeight': null,
          'minDate': minDate,

          'bestBefore' : myDate,
          'locationDestId' : null,
          'newLocationDestId' : null,
          'locationList' : null,
          'showLocationInfo' : false,
          'showGreenSaveBtn': false,
        };
      }
      
      $scope.$on('$stateChangeSuccess',function (event, toState, toParams, fromState, fromParams) {
        if ($state.current.name === 'main_scan') {
          tools.focus();
          $scope.reset();
          
          $scope.data.operationCode = null;
          // Show loader
          $rootScope.$broadcast('handleBroadcastSpinner', true);
          PickingTypeModel.get_list().then(function (pickingTypes) {
            // Picking type details
            if (pickingTypes.length > 0) {
              
              pickingTypes.forEach(pickingTypeItem => {
                var pickingTypeItemId = pickingTypeItem.id;
                
                if($stateParams.picking_type_id == pickingTypeItemId) {  
                  $scope.data.operationCode = pickingTypeItem.code;
                  console.log("2611- pickingTypeItem : ",pickingTypeItem);
                  $scope.data.op_def_loc_id = pickingTypeItem.op_def_loc_id;

                  $scope.data.showLocationInfo = pickingTypeItem.show_location_info;
                }
              });
            }
            // Hide loader
            $rootScope.$broadcast('handleBroadcastSpinner', false);
          });
          
          if ($stateParams.move_id !== 0) {
            ScanMoveModel.get_by_id(
              $stateParams.picking_id, $stateParams.move_id
              ).then(function (move) {
                console.log("2611- move : ",move);
              if (move) {
                $scope.data.currentMove = move;
                $scope.data.packNumber = (move.package_id ? move.package_id : (move.pack_number ? move.pack_number : (move.result_package_id ? move.result_package_id : '')));

                // Just use qty_done as input, if statement says if the move was edited (pack is set) use the expected quantity
                // The people in the warehouse want to see the value they have entered before, so qty_expected would only be interesting if it's equal to qty_done
                $scope.data.inputData = move.qty_done;
                $scope.data.lotName = (move.lot_id ? move.lot_id : "");
                $scope.data.catchWeight = (move.catch_weight_ok ? move.cw_qty_done : null);
                $scope.data.bestBefore = (move.lot_mhd ? move.lot_mhd : (move.pack_mhd ? move.pack_mhd : false));
                $scope.data.locationDestId = move.location_dest_id;
                $scope.data.no_expiry = (move.product.no_expiry || false);

                if ("generic_attributes" in $scope.data.currentMove) {
                  for (let i in  $scope.data.currentMove.generic_attributes) {
                    const att = $scope.data.currentMove.generic_attributes[i]
                    for (let val in att.valid_values) {
                      const valid_value = att.valid_values[val]
                      // Make sure structure which will be used exists
                      if (!("generic" in $scope.data.currentMove)) {
                        $scope.data.currentMove.generic = {line_: {}}
                      }
                      // Preselect values
                      if (valid_value.selected) {
                        $scope.data.currentMove.generic.line_[att.attribute_line_id] = valid_value.id
                      }
                    }
                  }
                }
              }
            });
          }
        }
      });

      $scope.save = function() {
        // Show loader
        // $rootScope.$broadcast('handleBroadcastSpinner', true);
        var packQuantity = $scope.data.inputData;
        var lotName = $scope.data.lotName;
        var packNumber = $scope.data.packNumber;
        var catchWeight = $scope.data.catchWeight;
        var noExpiry = $scope.data.no_expiry;

        var bestBefore = $filter('date')($scope.data.bestBefore, "MM/dd/yyyy");
        if(catchWeight) {
            var move = $scope.data.currentMove;
            jsonRpc.call(
                'product.product', 'check_deviation_warning_js',
                [move.product.id, catchWeight, packQuantity, move.uom.id, move.product_cw_uom.id]
            ).then(function(msg) {
                if(msg.message){
                    $rootScope.$broadcast('handleBroadcastSpinner', false);
                    $scope.data.errorMessage = msg.message;
                    return false;
                }
            })
        }

        if ($scope.data.currentMove.generic_attributes) {
            $scope.data.currentMove.generic_attributes.forEach(attribute => {
                if (attribute.mandatory == true && ($scope.data.currentMove.generic == undefined || $scope.data.currentMove.generic.line_[attribute.attribute_line_id]  == undefined)) {
                    $scope.data.errorMessage = attribute.attribute_label + ' requires value';
                    return false;
                }
            })
        }

        if(packQuantity && lotName && packNumber && ((bestBefore == false && noExpiry) || (bestBefore && noExpiry == false))){ // && $scope.data.newLocationDestId

          if(packQuantity > 0){

            $scope.data.currentMove['lot_mhd'] = bestBefore;
            $scope.data.currentMove['pack_number'] = packNumber;
            $scope.data.currentMove['lot_name'] = lotName;
            // $scope.data.currentMove['cw_qty_done'] = catchWeight;


              var showAlert = true;

              if($scope.data.currentMove.catch_weight_ok == false){
                if(packQuantity <= $scope.data.currentMove.qty_expected){
                  showAlert = false;
                } else {
                  showAlert = true;
                }
              } else {
                if(packQuantity <= $scope.data.currentMove.qty_expected){

                  if(catchWeight <= ($scope.data.currentMove.product_cw_uom_qty - $scope.data.currentMove.cw_qty_done)){
                    showAlert = false;
                  } else {
                    showAlert = true;
                  }

                } else {
                  showAlert = true;
                }
              }

              if(showAlert){
                if ( window.confirm("Please confirm that entered values are correct.") ) {
                  // Save
                  $scope.call_save_line(packQuantity);
                }
              } else {
                // Save
                $scope.call_save_line(packQuantity);
              }
          } else {
            // Hide loader
            $rootScope.$broadcast('handleBroadcastSpinner', false);
            $scope.data.errorMessage = "Invalid quantity or weight";
          }

        } else {
          // Hide loader
          $rootScope.$broadcast('handleBroadcastSpinner', false);
          $scope.data.errorMessage = "Package format should be e.g.,RX123456 or R123456";
        }
      };

      $scope.call_save_line = function(packQuantity) {
        // Show loader
        $rootScope.$broadcast('handleBroadcastSpinner', true);

        $scope.data.currentMove['cw_qty_done'] = $scope.data.catchWeight;

        ScanMoveModel.save_line($scope.data.currentMove, packQuantity).then(function () {

          $state.go('list_move', {
            picking_type_id: $stateParams.picking_type_id,
            picking_id: $stateParams.picking_id
          });
        },
        function(data) {
          // Handle error here
          if(data.fullTrace.data.message != '' && $scope.data.errorMessage.length == 0){
            $scope.data.errorMessage = data.fullTrace.data.message;
          } else if ($scope.data.errorMessage.length == 0) {
            $scope.data.errorMessage = "Something went wrong, please try again.";
          }

        });
        // Hide loader
        $rootScope.$broadcast('handleBroadcastSpinner', false);
      };

      $scope.submit = function () {
        $scope.display_loading_begin();
        var inputValue = $scope.data.inputData;

        // It's a barcode of a product
        if (tools.is_barcode(inputValue)) {
          MoveModel.get_by_barcode_product($stateParams.picking_id,inputValue)
          .then(function (moves) {
            if (moves.length === 0) {
              $scope.display_loading_end($translate.instant(
                'Barcode not found in the picking'));
            } else if (moves.length > 1) {
              $scope.display_loading_end($translate.instant(
                'Many operations found'));
            } else {
              // The exact move has been found
              move = moves[0];
              var newQty = move.qty_done + 1;
              MoveModel.set_quantity(move, newQty).then(function () {
                $scope.data.currentMove = move;
                $scope.display_loading_end();
              });
            }
          });

              // It's a quantity
        } else if (tools.is_quantity_correct(inputValue)) {
          if ($scope.data.currentMove) {
            var move = $scope.data.currentMove;
            MoveModel.set_quantity(move, inputValue).then(function () {
              $scope.display_loading_end();
            });
          } else {
            $scope.display_loading_end($translate.instant(
              'Please first scan a product'));
            }

            // It's an error
        } else {
          $scope.display_loading_end($translate.instant('Incorrect quantity'));
        }
      };

      $scope.display_loading_begin = function () {
        $scope.data.errorMessage = null;
        tools.display_loading_begin();
      };

      $scope.display_loading_end = function (errorMessage) {
        $scope.data.errorMessage = errorMessage;
        tools.display_loading_end();
        $scope.data.inputData = null;
      };

      $scope.clearValidation = function () {
        $scope.data.errorMessage = "";
        $scope.getSaveBtnStatus();
      };


      $scope.getSaveBtnStatus = function() {
        $scope.data.showGreenSaveBtn = false;
        // Product has no generic attributes, so button can be made green
        if (!("generic_attributes" in $scope.data.currentMove)) {
          $scope.data.showGreenSaveBtn = true;
          return;
        }
        // Loop through given generic_attributes
        for (const att in $scope.data.currentMove.generic_attributes) {
          const element = $scope.data.currentMove.generic_attributes[att];
          if (element.mandatory) {
            // If one of the mandatory generic attributes is invalid, don't turn the save button green
            // So when showGreenSaveBtn is set to false, function can return
            if ("generic" in $scope.data.currentMove) {
              if (element.attribute_line_id in $scope.data.currentMove.generic.line_) {
                $scope.data.showGreenSaveBtn = true;
              } else {
                $scope.data.showGreenSaveBtn = false;
                return;
              }
            } else {
              $scope.data.showGreenSaveBtn = false;
              return;
            }
          } else {
            $scope.data.showGreenSaveBtn = true;
        }
        }
      };
    }
  ]
);
                
