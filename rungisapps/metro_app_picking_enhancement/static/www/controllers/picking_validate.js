/* global angular */

angular.module('mobile_app_picking').controller(
  'PickingValidateCtrl', [
    '$scope', '$rootScope', '$state', '$stateParams', 'PickingModel', 'tools', '$window',
    function ($scope, $rootScope, $state, $stateParams, PickingModel, tools, $window) {
      $scope.data = {
        'picking': null,
        'validation_state': null,
        'errorMessage': ''
      };

      $scope.$on(
        '$stateChangeSuccess',
        function (event, toState, toParams, fromState, fromParams) {
          if ($state.current.name === 'picking_validate') {
            $scope.data.validation_state = null;
            tools.focus();

            // Show loader
            $rootScope.$broadcast('handleBroadcastSpinner', true);

            PickingModel.get_by_id(
              $stateParams.picking_type_id,
              $stateParams.picking_id
            ).then(function (picking) {
              $scope.data.picking = picking;
            });
            PickingModel.try_validate_picking(
              $stateParams.picking_id
            ).then(function (state) {
              // Show loader
              $rootScope.$broadcast('handleBroadcastSpinner', false);
              
              if (state === 'picking_validated') {
                $state.go('list_picking', {
                  picking_type_id: $stateParams.picking_type_id,
                });
              } else if (state === "picking_validated_no_left") {
                $state.go("list_picking_type");
              }
              $scope.data.validation_state = state;
            })
            .catch(function (data) {
              $scope.iframeHeight = ($window.innerHeight - 88);
              if(data.fullTrace.data.message != ''){
                $scope.data.errorMessage = data.fullTrace.data.message;
              } else {
                $scope.data.errorMessage = "Something went wrong, please try again.";
              }
              // Show loader
              $rootScope.$broadcast('handleBroadcastSpinner', false);
                // Handle error here
            });
          }
        });

        $scope.confirm_picking = function (action) {
            tools.display_loading_begin();
            // Show loader
            $rootScope.$broadcast('handleBroadcastSpinner', true);
            PickingModel.confirm_picking(
              $stateParams.picking_id, action
            ).then(function (state) {
              tools.display_loading_end();
              // Hide loader
              $rootScope.$broadcast('handleBroadcastSpinner', false);
    
              if (state === "picking_validated_no_left") {
                $state.go("list_picking_type");
              } else {
                $state.go('list_picking', {
                    picking_type_id: $stateParams.picking_type_id,
                  });
              }          
            }).catch(function (r) {
              $scope.data.errorMessage = r["fullTrace"]["data"]["message"];
              console.log(r);
              tools.display_loading_end();
              // Hide loader
              $rootScope.$broadcast('handleBroadcastSpinner', false);
            });
        };
    }]);
