import logging

from odoo import api, fields, models, _
from datetime import timedelta, datetime
from odoo.addons.queue_job.job import job


logger = logging.getLogger(__name__)


    
class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    invoice_created = fields.Boolean('invoice created', default=False)
    
    @job(default_channel='root.generate_check_invoice')
    def generate_check_invoice(self):
        # Create first_date variable and get the date from the ir.config_parameter
        first_date = datetime.now()
        try:
            first_date = datetime.strptime(
                    self.env["ir.config_parameter"].sudo().get_param("metro_rungis_invoice_robot.create_invoice_picking_start_date"), "%Y-%m-%d")
        except Exception as e:
            logger.error("Error getting metro_rungis_invoice_robot.create_invoice_picking_start_date from ir.config_parameter")
            return
        # Get companies which have the robot activated
        company_ids = self.env["res.company"].search([("run_invoice_robot", "=", True)])
        # Loop through companies
        for company in company_ids:
            # First: Check if cron was interrupted before (=> draft invoices were created) and process them first
            self._process_draft_invoices(company.id)
            # Get pickings which need to be processed
            picking_ids = self.env['stock.picking'].search([
                ('state','=','done'),
                ('picking_type_code','=','outgoing'),
                ('invoice_created','=',False),
                ("scheduled_date", ">=", str(first_date)),
                ("company_id", "=", company.id)
            ])
            # NOTE: Shift date_create_invoice after partner is processed
            # Extract the different partners for the loaded pickings and create invoices for each partner
            partner_ids = picking_ids.mapped("partner_id")
            for partner in partner_ids:
                # Get the partner's subcontact of type invoice, otherwise use partner of picking as fallback
                # Make sure "Process Controls" is configured properly
                inv_partner = partner.child_ids.filtered(lambda child: child.type == "invoice")
                if not inv_partner:
                    inv_partner = partner
                # Create invoices based on pickings after partner was checked for errors
                partner_pickings = picking_ids.filtered(lambda p: p.partner_id.id == partner.id)
                # Create an invoice for each outgoing picking
                for picking in partner_pickings:
                    if picking.group_id and not picking.invoice_created:
                        # Get invoice lines which need to be invoiced and create invoice with them, do a commit after invoice is created
                        not_invoiced_lines = picking._check_invoice_already_created()
                        invoice = picking.action_create_invoice(not_invoiced_lines)
                        picking.invoice_created = True
                        # Might return None if no lines need to be invoiced
                        if not invoice or invoice is None:
                            continue
                        self.env.cr.commit()
                        invoice._pre_process_invoice()

    @api.model
    def _process_draft_invoices(self, company_id=None):
        """This function identifies invoices which are still in status draft and were generated by the robot
        The reason for the invoices being in state draft is that the job didn't quite finish at the current invoice
        So to make sure the process will not break if something in the invoice is broken everything is wrapped in try/catch

        Args:
            company_id (int, optional): Current company id the robot is processing. Defaults to None.

        Returns:
            bool: True if all invoices could be processed, False if at least one has failed
        """
        if not company_id:
            return
        # Find invoices generated by the robot still in state draft
        robot_draft_inv = self.env["account.invoice"].search([
            ("picking_invoice", "=", True),
            ("state", "=", "draft"),
            ("company_id", "=", company_id)
        ])
        # Do every step which is done in the first step again
        try:
            for invoice in robot_draft_inv:
                invoice._pre_process_invoice()
        except Exception as e:
            logger.warning("%s" % e)
            # Post an error into the chatter
            msg = "ERROR: Failed to process draft invoice {} ({}):\n{}".format(invoice.number, invoice.id, e)
            invoice.message_post(body=msg)
            return False
        return True


    @api.multi
    def _check_invoice_already_created(self):
        # {line_id : float(delivered_qty - invoiced_qty),}; if value of line_id > 0, value is to invoice, CW PRODUCTS!
        not_invoiced = {}
        for picking in self:
            for line in picking.sale_id.order_line:
                if line.product_id._is_cw_product():
                    # If line is already invoiced don't include it in dict
                    if (line.cw_qty_delivered - line.cw_qty_invoiced) > 0:
                        not_invoiced[line.id] = line.cw_qty_delivered - line.cw_qty_invoiced
                # If line is already invoiced don't include it in dict
                elif  (line.qty_delivered - line.qty_invoiced) > 0:
                    not_invoiced[line.id] = line.qty_delivered - line.qty_invoiced
        return not_invoiced

    @api.multi
    def action_create_invoice(self, not_invoiced):
        """ 
            Action to create invoice from done picking/deliveries
        """
        # Workaround, for some reason the not_invoiced dictionary was wrapped in a list
        if type(not_invoiced) == type([]):
            not_invoiced = not_invoiced[0]
        
        # Everything is already invoiced
        if len(not_invoiced) == 0:
            return None
        invoice_vals = self._prepare_invoice()
        
        invoice_obj = self.env['account.invoice'].create(invoice_vals)
        account = self.with_context(force_company=self.company_id.id).product_id.property_account_income_id \
             or self.with_context(force_company=self.company_id.id).product_id.categ_id.property_account_income_categ_id

        if not account and self.product_id:
            logger.debug('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".',
                self.product_id.name, self.product_id.id, self.product_id.categ_id.name)
    
        # sale_id don't need to force_company, since a sale order is already assigned to a company
        fpos = self.sale_id.fiscal_position_id or \
            self.sale_id.partner_id.with_context(force_company=self.company_id.id).property_account_position_id
        
        if fpos and account:
            account = fpos.map_account(account)
        # Array for making sure sale lines are not invoices twice
        done_slines = set()
        for line in self.move_lines:
            sale_line = self.env['sale.order.line'].search([('order_id','=',self.origin),('product_id','=',line.product_id.id)])
            # Workaround edge case: 1 order in test db contained same product twice
            for sline in sale_line:
                if sline.id in not_invoiced and not_invoiced[sline.id] > 0 and sline.id not in done_slines:
                    self.env['account.invoice.line'].create({
                        'invoice_id':invoice_obj.id,
                        'name': sline.name,
                        # Changed origin from picking name to order name
                        'origin': sline.order_id.name,
                        'account_id': account.id,
                        'price_unit': sline.price_unit,
                        'currency_id':sline.currency_id.id,
                        # 'quantity': line.quantity_done,
                        # 'product_cw_uom_qty': line.cw_qty_done,
                        'quantity': not_invoiced[sline.id] if not sline.product_id._is_cw_product() else (sline.qty_delivered - sline.qty_invoiced),
                        'product_cw_uom_qty': not_invoiced[sline.id] if sline.product_id._is_cw_product() else 0,
                        'product_cw_uom': line.product_cw_uom.id,
                        'discount': sline.discount,
                        'uom_id': line.product_uom.id,
                        'product_id': line.product_id.id or False,
                        'invoice_line_tax_ids': [(6, 0, sline.tax_id.ids)],
                        'account_analytic_id': sline.order_id.analytic_account_id.id,
                        'analytic_tag_ids': [(6, 0, sline.analytic_tag_ids.ids)],
                        'display_type': sline.display_type,
                        'sale_line_ids': [(6, 0, [sline.id])]
                    })
                    done_slines.add(sline.id)
        logger.debug('invoices are created from Done deliveries')
        return invoice_obj
    
    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a Picking/deliveries.)
        """
        self.ensure_one()
        journal_id = self.env["account.journal"].search([
            ("company_id", "=", self.company_id.id),
            ("type", "=", "sale"),
            ("active", "=", True)
        ], limit=1)
        if not journal_id:
            logger.debug('Please define an accounting sales journal for this company.')
        global_discount_ids = self.sale_id.partner_id.customer_global_discount_ids.ids
        if self.sale_id.global_discount_ids.ids:
            global_discount_ids = self.sale_id.global_discount_ids.ids
        invoice_vals = {
            'name': self.sale_id.client_order_ref or '',
            'origin': self.sale_id.name,
            'type': 'out_invoice',
            'picking_invoice':True,
            'account_id': self.sale_id.partner_invoice_id.with_context(force_company=self.company_id.id).property_account_receivable_id.id,
            'partner_id': self.sale_id.partner_invoice_id.id,
            'partner_shipping_id': self.sale_id.partner_shipping_id.id,
            'global_discount_ids': [(6, 0, list(global_discount_ids))],
            'journal_id': journal_id.id,
            'currency_id': self.sale_id.pricelist_id.currency_id.id or self.env.user.company_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.sale_id.payment_term_id.id,
            'fiscal_position_id': self.sale_id.fiscal_position_id.id or self.sale_id.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.sale_id.user_id and self.sale_id.user_id.id,
            'team_id': self.sale_id.team_id.id,
            'transaction_ids': [(6, 0, self.sale_id.transaction_ids.ids)],
        }
        return invoice_vals
