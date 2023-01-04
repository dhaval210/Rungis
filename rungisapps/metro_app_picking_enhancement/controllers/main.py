from odoo import http
from odoo.http import request
from odoo.addons.metro_mobile_app_picking.controllers.main import Home
from odoo.addons.web.controllers.main \
    import db_monodb, ensure_db, set_cookie_and_redirect, login_and_redirect

class HomeExtended(Home):
    @http.route('/mobile_app_picking', type='http', auth='none')
    def index(self, s_action=None, db=None):
        return http.local_redirect(
            '/metro_app_picking_enhancement/static/www/index.html',
            query=request.params)
    
    @http.route('/metro_app_picking_enhancement/init', auth='none')
    def init(self, db, user, password):
        # this only works with dbfilter set to a specific db
        resp = login_and_redirect(
            db,
            user,
            password,
            redirect_url='/metro_app_picking_enhancement/static/www/index.html'
        )
        return resp
