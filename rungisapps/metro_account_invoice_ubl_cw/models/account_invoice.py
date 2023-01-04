from lxml import etree
from odoo import models
from odoo.tools import float_is_zero, float_round


class Invoice(models.Model):
    _inherit = 'account.invoice'

    def _ubl_add_invoice_line_tax_total(
            self, iline, parent_node, ns, version='2.1'):
        '''
            override of account_invoice_ubl -> _ubl_add_invoice_line_tax_total
        '''
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        tax_total_node = etree.SubElement(parent_node, ns['cac'] + 'TaxTotal')
        price = iline.price_unit * (1 - (iline.discount or 0.0) / 100.0)
        if iline.catch_weight_ok:
            quantity = iline.product_cw_uom_qty
        else:
            quantity = iline.quantity
        res_taxes = iline.invoice_line_tax_ids.compute_all(
            price, quantity=quantity, product=iline.product_id,
            partner=self.partner_id)
        tax_total = float_round(
            res_taxes['total_included'] - res_taxes['total_excluded'],
            precision_digits=prec)
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        tax_amount_node.text = '%0.*f' % (prec, tax_total)
        if not float_is_zero(tax_total, precision_digits=prec):
            for res_tax in res_taxes['taxes']:
                tax = self.env['account.tax'].browse(res_tax['id'])
                # we don't have the base amount in res_tax :-(
                self._ubl_add_tax_subtotal(
                    False, res_tax['amount'], tax, cur_name, tax_total_node,
                    ns, version=version)
