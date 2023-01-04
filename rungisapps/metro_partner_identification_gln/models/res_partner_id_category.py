from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

try:
    from stdnum import ean
    from stdnum.exceptions import InvalidChecksum
except ImportError:
    _logger.debug('Cannot `import external dependency python stdnum package`.')

class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    @api.multi
    def validate_res_partner_gln(self, id_number):
        self.ensure_one()
        if not id_number:
            return False

        try:
            ean.validate(id_number.name)
        except InvalidChecksum:
            return True

        # cat = self.env.ref('partner_identification_gln.'
        #                    'partner_identification_gln_number_category').id
        # duplicate_gln = self._search_duplicate(cat, id_number, True)
        # if duplicate_gln:
        #     return True

        return False
