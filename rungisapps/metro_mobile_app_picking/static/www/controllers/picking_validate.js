/* global angular */

angular.module('mobile_app_picking').controller(
  'PickingValidateCtrl', [
    '$scope', '$state', '$stateParams', 'PickingModel', 'tools',
    function ($scope, $state, $stateParams, PickingModel, tools) {
      $scope.data = {
        'picking': null,
        'validation_state': null,
      };

      $scope.$on(
        '$stateChangeSuccess',
        function (event, toState, toParams, fromState, fromParams) {
          if ($state.current.name === 'picking_validate') {
            $scope.data.validation_state = null;
            tools.focus();

            PickingModel.get_by_id(
              $stateParams.picking_type_id,
              $stateParams.picking_id
            ).then(function (picking) {
              $scope.data.picking = picking;
            });
            PickingModel.try_validate_picking(
              $stateParams.picking_id
            ).then(function (state) {
              if (state === 'picking_validated') {
                $state.go('list_picking', {
                  picking_type_id: $stateParams.picking_type_id,
                });
              } else if (state === "picking_validated_no_left") {
                $state.go("list_picking_type");
              }
              $scope.data.validation_state = state;
            });
          }
        });

      $scope.confirm_picking = function (action) {
        tools.display_loading_begin();
        PickingModel.confirm_picking(
          $stateParams.picking_id, action
        ).then(function () {
          tools.display_loading_end();
          $state.go('list_picking', {
            picking_type_id: $stateParams.picking_type_id,
          });
        }).catch(function (r) {
          $scope.data.errorMessage = r["fullTrace"]["data"]["message"];
          console.log(r);
          tools.display_loading_end();
          // Hide loader
          $rootScope.$broadcast('handleBroadcastSpinner', false);
        });
      };
    }]);
