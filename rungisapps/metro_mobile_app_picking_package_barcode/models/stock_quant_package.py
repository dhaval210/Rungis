from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class QuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def check_name(self, name):
        if len(name):
            last_year = fields.Date.today() - relativedelta(days=365)
            if len(self.search([
                ("name", "=", name),
                ("write_date", ">", last_year), ("id", '!=', self.id)
            ])):
                return False
        return True
