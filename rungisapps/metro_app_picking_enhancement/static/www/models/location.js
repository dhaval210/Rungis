/* global angular */

angular.module('mobile_app_picking').factory(
  'ScanLocationModel', [
    'jsonRpc',
    function (jsonRpc) {
      function reset () {
        data.locations = [];
        data.promise = null;
      }
      var data = {};
      reset();

      return {

        get_available_locations: function () {

          if (data.locations && data.promise) {
            // Return cached data if available
            return data.promise;
          }
          reset();

          data.promise = data.promise || jsonRpc.call(
            'mobile.app.picking', 'get_available_locations', []
          ).then(function (res) {
            data.locations = res;
            return data.locations;
          });
          return data.promise;
        },

        get_all_locations: function (location_dest_id, product_id, op_default_loc_id) {
          data.promise = jsonRpc.call(
            'mobile.app.picking', 'get_all_locations', [location_dest_id, product_id, op_default_loc_id]
          ).then(function (res) {
            data.locations = res;
            return data.locations;
          });
          return data.promise;
        },

      };
    }]);
