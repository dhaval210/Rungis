from odoo import models, api


class InvoiceMerge(models.TransientModel):
    _inherit = "invoice.merge"


    @api.multi
    def merge_invoices(self):
        aw_obj = self.env['ir.actions.act_window']
        ids = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(ids)
        allinvoices = invoices.do_merges(keep_references=self.keep_references,
                                        date_invoice=self.date_invoice,
                                        manually_selected=True)
        # xid = {
        #     'out_invoice': 'action_invoice_tree1',
        #     'out_refund': 'action_invoice_tree1',
        #     'in_invoice': 'action_invoice_tree2',
        #     'in_refund': 'action_invoice_tree2',
        # }[invoices[0].type]
        # action = aw_obj.for_xml_id('account', xid)
        # action.update({
        #     'domain': [('id', 'in', ids + list(allinvoices.keys()))],
        # })
