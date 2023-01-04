"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from collections import defaultdict
from datetime import datetime

from odoo import models, fields, api


class PurchasingTeam(models.Model):
    """inherit purchasing team to add fields """
    _inherit = 'purchasing.team'

    alert_email = fields.Text('Alert Email', )


class StockLotSerial(models.Model):
    """inherit stock.production.lot to add fields """
    _inherit = 'stock.production.lot'

    purchasing_team_id = fields.Many2one('purchasing.team',
                                         string='Purchasing Team',
                                         related='product_id.product_tmpl_id.purchasing_team_id',
                                         readonly=False, store=True)


class ProductProduct(models.Model):
    """inherit product.product  to adding email """
    _inherit = 'product.product'

    @api.multi
    def _get_alert_data(self):
        alert_data = []
        current_date = datetime.now().date()
        print(current_date)
        product = self.env['stock.production.lot'].search([])
        for lot in product:
            if lot.alert_date:
                lot_date = datetime.strptime(str(lot.alert_date),
                                             '%Y-%m-%d %H:%M:%S')
                if lot_date.date() == current_date:
                    alert_data.append(lot)
        product_lot_dict = defaultdict(list)
        if alert_data:
            for expiry_data_id in alert_data:
                product_lot_dict[expiry_data_id.product_id].append(
                    expiry_data_id)
        return product_lot_dict

    @api.multi
    def _alert_product_expiry(self):

        product_lot_dict = self._get_alert_data()
        for product, lot_data in product_lot_dict.items():
            lot_details = self._get_lot_data(lot_data)
            context = self._context.copy()

            context.update({'lot_data': lot_details})
            template_id = self.env.ref(
                'metro_product_expiry_alert. '
                'expiry_alert_email_template_product')
            template_id.with_context(context).sudo().send_mail(product.id,
                                                               force_send=True)

    @api.multi
    def _get_lot_data(self, lot_data):
        records = []
        if lot_data:
            for lot in lot_data:
                lots = {}
                lots["lot_number"] = lot.name
                lots["removal_date"] = lot.removal_date
                lots["use_date"] = lot.use_date
                lots["life_date"] = lot.life_date
                records.append(lots)
        return records
