# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

import urllib.parse as urlparse

from odoo import api, fields, models


class ResPartner(models.Model):
    """inherit partner for adding field"""
    _inherit = "res.partner"

    plus_code = fields.Char('Google Plus Code')

    @api.model
    def geolocalize_actual(self, lat=False, long=False, url=False):
        """get value pass from rpc query """
        parsed = urlparse.urlparse(url)
        fragment = parsed.fragment
        print("ll",type(fragment))
        fragment = fragment.split("&")
        print("shshs",fragment)

        for i in fragment:
            i = i.split("=")
            for key in i:
                if key == 'id':
                    res_id = i[1]

        obj = self.env['res.partner'].search([('id', '=', res_id)])
        if lat and long:
            obj.update({
                'date_localization': fields.Date.context_today(self),
                'partner_latitude': lat,
                'partner_longitude': long,
            })
        return True
