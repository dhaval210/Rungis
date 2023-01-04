function geoFindMe() {
  var output = document.getElementById("geo-message");
  var save_button = document.getElementsByClassName("localize_from_browser");

  if (!navigator.geolocation){
    output.innerHTML = "<p>Geolocation is not supported by your browser</p>";
    return;
  }

  function success(position) {
    var latitude  = position.coords.latitude;
    var longitude = position.coords.longitude;

    output.innerHTML = '<p>Latitude is ' + latitude + '° <br>Longitude is ' + longitude + '°</p>';
    var temp_lat = document.createElement('temp_lat');
    temp_lat.innerHTML = latitude;
    temp_lat.setAttribute('hidden','');
    var temp_long = document.createElement('temp_long');
    temp_long.innerHTML = longitude;
    temp_long.setAttribute('hidden','');

    save_button[0].classList.remove("o_form_invisible");

    var img = new Image();
    img.src = "https://maps.googleapis.com/maps/api/staticmap?center=" + latitude + "," + longitude + "&zoom=13&size=300x300&sensor=false";

    output.appendChild(img);
    output.appendChild(temp_lat);
    output.appendChild(temp_long);
  }

  function error() {
    output.innerHTML = "Unable to retrieve your location";
  }

  output.innerHTML = "<p>Locating…</p>";
  navigator.geolocation.getCurrentPosition(success, error);
  $('.localize_from_browser').css('visibility', 'visible');

}
odoo.define('metro_geolocalize.form_view', function (require) {
"use strict";

var data = require('web.data');
var FormView = require('web.FormView');
var form_widget = require('web.FormRenderer');
     form_widget.include({
        _addOnClickAction: function ($el, node) {
            var self = this;
            $el.click(function () {
                 if ($el.hasClass('localize_from_browser')) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                            var coords = _.pick(position.coords, ['latitude', 'longitude']);
                            var lat = coords.latitude
                            var long = coords.longitude
                            var context = _.extend({ 'long': long,'lat':lat });
                            return self._rpc({
                                    model: 'res.partner',
                                    method: 'geolocalize_actual',
                                    args: [lat, long, window.location.href],
                            })
                            .then(function(data){
                                window.location.reload();
                            });
                    });
                };
                if(node.attrs.id === "darkroom-save")

                        darkroomBut.darkroom.plugins.crop.cropCurrentZone(true);

                  //just code old may use super

                self.trigger_up('button_clicked', {

                    attrs: node.attrs,

                    record: self.state,

                });

            });
        },
    });
});



