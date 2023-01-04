from odoo import models, api
from odoo.exceptions import AccessError


class OrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def write(self, vals):
        for rec in self:
            if (
                len(rec.db2_bind_ids) > 0 and
                not self.env.user.has_group('metro_rungis_views.group_master_user_sale_order') and
                rec.order_id.softm_trennen is False
            ):
                raise AccessError('You are not allowed to change Softm orders. Only master user can do this!')
        return super().write(vals)
