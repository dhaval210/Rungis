
from odoo import models, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_approve(self, force=False):
        res = super().button_approve(force)

        for rec in self:
            company_partner = int(self.env["ir.config_parameter"].sudo()
                                .get_param("inter_company_purchase_partner_id"))
            sale_id = self.env['sale.order'].sudo().search([
                ('name', '=', rec.origin),
                ('company_id', '=', 4)
            ])
            if rec.partner_id.id == company_partner and sale_id.id is not False:
                for picking in rec.picking_ids:
                    if picking.picking_type_code == 'incoming':
                        for sml in picking.move_line_ids:
                            if not sml.inter_company_line:
                                sml.unlink()
        return res

    @api.multi
    def _inter_company_create_sale_order(self, dest_company):
        """ Create a Sale Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo,
            and the creation of the derived
            SO as intercompany_user, minimizing the access right required
            for the trigger user.
            :param dest_company : the company of the created PO
            :rtype dest_company : res.company record
        """
        self.ensure_one()
        # Check intercompany user
        intercompany_user = dest_company.intercompany_user_id
        if intercompany_user.company_id != dest_company:
            intercompany_user.company_id = dest_company
        # check intercompany product
        self._check_intercompany_product(dest_company)
        # Accessing to selling partner with selling user, so data like
        # property_account_position can be retrieved
        company_partner = self.company_id.partner_id
        # check pricelist currency should be same with PO/SO document
        if self.currency_id.id != (
                company_partner.property_product_pricelist.currency_id.id):
            raise UserError(_(
                'You cannot create SO from PO because '
                'sale price list currency is different than '
                'purchase price list currency.'))
        # create the SO and generate its lines from the PO lines
        sale_order_data = self._prepare_sale_order_data(
            self.name, company_partner, dest_company, self.dest_address_id)
        if self.origin:
            sale_id = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
            if sale_id:
                sale_order_data.update({
                    'name': self.origin,
                    'partner_shipping_id': sale_id.partner_shipping_id.id,
                    'tour_id': sale_id.tour_id.id,
                    'run_up_point': sale_id.run_up_point,
                    'commitment_date': sale_id.commitment_date,
                    'date_order': sale_id.date_order,
                })
        sale_order = self.env['sale.order'].sudo(
            intercompany_user.id).create(sale_order_data)
        for purchase_line in self.order_line:
            sale_line_data = self._prepare_sale_order_line_data(
                purchase_line, dest_company, sale_order)

            if self.origin and sale_id:
                sale_line_id = self.env['sale.order.line'].search(
                    [
                        ('order_id', '=', sale_id.id),
                        ('product_id', '=', purchase_line.product_id.id),
                    ],
                    limit=1
                )
                if sale_line_id.id is not False:
                    sale_line_data.update({
                        'special_wishes': sale_line_id.special_wishes,
                        'process_number': sale_line_id.process_number,
                        'process_position': sale_line_id.process_position,
                    })
            self.env['sale.order.line'].sudo(
                intercompany_user.id).create(sale_line_data)
        # write supplier reference field on PO
        if not self.partner_ref:
            self.partner_ref = sale_order.name
        # Validation of sale order
        if dest_company.sale_auto_validation:
            sale_order.sudo(intercompany_user.id).action_confirm()
