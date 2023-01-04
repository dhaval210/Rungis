from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    group_check = fields.Boolean("Group Check", compute="check_group")
    write_date = fields.Datetime(string='Last Updated on', readonly=True, track_visibility='onchange')

    def check_group(self):
        user = self.env.user
        if user.has_group('metro_rungis_views.group_contact'):
            self.group_check = True
        else:
            self.group_check = False
