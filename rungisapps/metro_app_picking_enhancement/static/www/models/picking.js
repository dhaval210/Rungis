/* global angular */

angular.module('mobile_app_picking').factory(
  'ScanPickingModel', [
    '$q', 'jsonRpc', 'PickingModel',
    function ($q, jsonRpc, PickingModel) {
      function reset () {
        data.pickings = [];
        data.promise = null;
      }
      var data = {};
      reset();

      return {

        /**
        * On scan of picking barcode
        * Jump to picking move list
        **/
        get_picking_by_barcode: function (pickingTypeId, pickingName) {
          return PickingModel.get_list({'id': pickingTypeId})
            .then(function (pickings) {
              var foundPicking = false;
              
              pickings.forEach(function (picking) {

                var name = picking.name.replace(/\//g, '');
                if (pickingName === name) {
                  foundPicking = picking;
                }

                if (!foundPicking) {                  
                  if (pickingName === picking.origin) {
                    foundPicking = picking;
                  }
                }
              });
              return foundPicking;
            });
        },

      };
    }]);
