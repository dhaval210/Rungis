/* global angular */

angular.module('mobile_app_picking').controller(
  'LoginCtrl', [
    '$scope', '$rootScope', 'jsonRpc', '$state', '$translate', 'tools', '$http',
    function ($scope, $rootScope, jsonRpc, $state, $translate, tools, $http) {
      $scope.data = {
        'database': '',
        'databases': [],
        'login': '',
        'password': '',
      };

      $scope.$on('$ionicView.beforeEnter', function () {
        if ($state.current.name === 'logout') {
          jsonRpc.logout();
        }
      });

      $scope.init = function () {
        // jsonRpc.login(
        //   $scope.data.database,
        //   $scope.data.login,
        //   $scope.data.password
        // )
        tools.focus();

        // Load available databases
        jsonRpc.getDbList().then(function (databases) {
          $scope.data.databases = databases;
          if (databases.length >= 1) {
            $scope.data.database = databases[0];
          }
        }, function (reason) {
          $scope.errorMessage = $translate.instant('Unreachable Service');
        });
      };

      $scope.$on(
        '$stateChangeSuccess',
        function (event, toState, toParams, fromState, fromParams) {
          if ($state.current.name === 'login') {
            tools.focus();
          }
        });

      $scope.submit = function () {
        // Show loader
        $rootScope.$broadcast('handleBroadcastSpinner', true);
        $http({
          method : "GET",
          url : "/metro_app_picking_enhancement/init",
          params: {
            db: $scope.data.database,
            user: $scope.data.login,
            password: $scope.data.password
          },
          headers: {'Content-Type': 'application/json; charset=utf-8'},
        }).then(function mySuccess(response) {
            // Hide loader
            $rootScope.$broadcast('handleBroadcastSpinner', false);

            $state.go('list_picking_type', {});
          }, function myError(response) {
            // Hide loader
            $rootScope.$broadcast('handleBroadcastSpinner', false);

            $scope.errorMessage = $translate.instant('Bad Login / Password');
        });

      };
    }]);
