import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class TransferProductsWizard(models.TransientModel):
    _name = "stock.location.transfer.wizard"

    # contains quant_ids which contain the product_id & quantity
    location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        required=True,
        domain=[("usage", "in", ["internal", "transit"]), ("location_id", "!=", False)]
    )
    quant_ids = fields.Many2many(
        "stock.quant",
        domain="[('location_id', '=', location_id)]"
    )
    product_id = fields.Many2one(
        "product.product",
    )
    quant_id = fields.Many2one(
        "stock.quant",
        required=False,
        domain="[('location_id', '=', location_id)]"
    )
    catch_weight_ok = fields.Boolean(
        related="product_id.catch_weight_ok"
    )
    product_uom = fields.Many2one(
        "uom.uom",
        related="product_id.uom_id"
    )
    product_cw_uom = fields.Many2one(
        "uom.uom",
        related="product_id.cw_uom_id"
    )
    product_qty = fields.Float(
        string="Quantities"
    )
    product_bbd = fields.Datetime(
        string="Best Before Date",
        related="lot_id.use_date"
    )
    lot_id = fields.Many2one(
        "stock.production.lot"
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        required=True,
        domain=[("usage", "in", ["internal", "transit"]), ("location_id", "!=", False)]
    )
    error_free_location = fields.Boolean(
        default=False
    )
    error_free_source_location = fields.Boolean(
        default=False
    )
    # If the warning in the form for destination location should be shown
    warning_dest_location = fields.Boolean(
        default=False
    )
    error_free_dest_location = fields.Boolean(
        default=False
    )
    transfer_complete = fields.Boolean(
        default=False
    )
    edit_boolean = fields.Boolean(default=False)
    save_boolean = fields.Boolean(default=False)
    new_lot_id = fields.Char("Lot")
    new_product_bbd = fields.Datetime(
        string="Best Before Date")

    @api.onchange("location_id")
    def get_quant_on_location(self):
        # NOTE: Value is not overwritten, when location_id is changed to error-prone location, error is raised and location_id contains old value
        self.error_free_source_location = False
        if not self.location_id:
            return
        errors = []
        # pids = set()
        pids = {}
        lots = set()
        if len(self.location_id.quant_ids) == 0:
            raise UserError(_("There are no products on this location."))

        qty = 0
        self.quant_ids = [(5, 0, 0)]
        """Build sets in for loop, required for calculating quantities, more efficient to use 1 loop instead of 3"""
        for q in self.location_id.quant_ids:
            qty += q.cw_stock_quantity if q.catch_weight_ok else q.quantity
            rqty = q.cw_stock_reserved_quantity if q.catch_weight_ok else q.reserved_quantity
            if rqty:
                errors.append(
                    "There are reserved quantities for the product " + q.product_id.name + " with lot " + q.lot_id.name + ".")

            self.quant_ids = [(4, q.id)]
            if q.product_id.id in pids:
                pids[q.product_id.id] = pids[q.product_id.id] + qty
            else:
                pids[q.product_id.id] = qty

            lots.add(q.lot_id.id)
        if len(errors) >= 1:
            msg = "There were some errors regarding the location " + self.location_id.name + ".\n"
            for e in errors:
                msg += " * " + e + "\n"
            raise ValidationError(_(msg))
        # No error until here, so quants are okay
        self.error_free_source_location = True
        # Auto set the quant_id if only one product is present at the location
        if len(self.quant_ids) == 1:
            pid = list(pids.keys())[0]
            self.quant_id = self.quant_ids[0]
            self.product_id = pid
            self.product_qty = pids[pid]
            self.lot_id = list(lots)[0]

    @api.onchange("quant_id")
    def _onchange_quant_id(self):
        self.product_id = self.quant_id.product_id.id
        self.lot_id = self.quant_id.lot_id
        self.product_qty = self.quant_id.cw_stock_quantity if self.quant_id.catch_weight_ok else self.quant_id.quantity
        # Seems not to be triggered when adding quant_id to api.onchange of _onchange_location_dest_id()
        self._onchange_location_dest_id()

    @api.onchange("location_dest_id")
    def _onchange_location_dest_id(self):
        # Make sure destination location does not contain products
        self.warning_dest_location = False
        self.error_free_dest_location = False
        if not self.location_dest_id:
            return {}
        pids = {q.product_id.id for q in self.location_dest_id.quant_ids}
        if len(pids) > 1:
            raise ValidationError(_("There are already products on this location."))
        # Make sure the parent location has the same softm location number as the product
        formatted_nr = "{:0>2}".format(self.product_id.softm_location_number)
        same_softm_nr = False
        ploc = self.location_dest_id
        while ploc.location_id.id != False:
            if ploc.name.strip().startswith(formatted_nr):
                same_softm_nr = True
                break
            ploc = ploc.location_id
        if not same_softm_nr:
            raise ValidationError(
                _("The destination location must have the same Softm Location number as the product."))

        if len(pids) == 1 and list(pids)[0] != self.product_id.id:
            # Not the same product
            raise ValidationError(_("There is already another product on this location."))
        elif len(pids) == 1:
            # Same product, check if lots are same, if not show warning to user
            source_lots = {q.lot_id.name for q in self.location_id.quant_ids}
            dest_lots = {q.lot_id.name for q in self.location_dest_id.quant_ids}
            if source_lots != dest_lots:
                # Display the alert in the form instead of raising an error and discarding the value the user chose, display confirm button
                self.warning_dest_location = True
        self.error_free_dest_location = True

    @api.onchange("location_id", "location_dest_id", "error_free_source_location", "error_free_dest_location")
    def _check_error_free(self):
        self.error_free_location = self.error_free_source_location and self.error_free_dest_location

    def transfer_products(self):
        # for q in self.location_id.quant_ids:
        warehouse = self.env["stock.warehouse"].search([
            ("company_id", "=", self.location_id.company_id.id),
            ("lot_stock_id", "parent_of", self.location_id.id)
        ], limit=1)
        if not warehouse:
            # Case should not occur anymore, since domain of locations contains location_id != False (=> parent location must be set)
            raise UserError(_("No warehouse found for location " + self.location_id.name + "."))
        picking_type = self.env["stock.picking.type"].search([
            ("code", "=", "internal"),
            ("barcode", "like", "%INTERNAL"),
            ("warehouse_id", "=", warehouse.id),
            ("active", "=", True)
        ], limit=1).id
        values = {
            "product_id": self.quant_id.product_id.id,
            "location_id": self.location_id.id,
            "location_dest_id": self.location_dest_id.id,
            "picking_type_id": picking_type,
            "company_id": warehouse.company_id.id,
            "partner_id": self.env.user.partner_id.id,
        }
        # Got UserError, please configure senders e-mail address when trying w/ taxi w/o sudo
        picking = self.env["stock.picking"].create(values)
        move = self.env["stock.move"].create({
            "product_id": self.quant_id.product_id.id,
            "product_uom_qty": self.quant_id.quantity,
            "product_uom": self.quant_id.product_uom_id.id,
            "product_cw_uom_qty": self.quant_id.cw_stock_quantity,
            "product_cw_uom": self.quant_id.product_cw_uom.id,
            "location_id": self.location_id.id,
            "location_dest_id": self.location_dest_id.id,
            "warehouse_id": warehouse.id,
            "picking_id": picking.id,
            "name": str(warehouse.code) + " product transfer",
        })
        self.env.cr.commit()
        # "Mark as Todo"
        picking.action_confirm()
        self.env.cr.commit()
        # "Check availability"
        picking.action_assign()
        self.env.cr.commit()
        # "Validate"
        move.write({
            "quantity_done": self.quant_id.quantity,
            "cw_qty_done": self.quant_id.cw_stock_quantity,
        })
        picking.action_done()
        self.transfer_complete = True
        return {
            "name": _("Transfer products between locations"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.location.transfer.wizard",
            "type": "ir.actions.act_window",
        }

    @api.model
    def get_location_by_barcode(self, barcode):
        return self.env["stock.location"].search([
            ("company_id", "=", self.env.user.company_id.id),
            ("barcode", "=", barcode),
            ("usage", "in", ["internal", "transit"])
        ], limit=1).id

    def edit_lot_bbd(self):
        self.edit_boolean = not self.edit_boolean
        self.new_lot_id = self.lot_id.name
        self.new_product_bbd = self.product_bbd
        self.save_boolean = not self.save_boolean

    def save_button(self):
        self.save_boolean = not self.save_boolean
        self.edit_boolean = not self.edit_boolean
        product = self.lot_id.product_id
        ref_date = self.new_product_bbd - datetime.timedelta(days=product.use_time)
        self.lot_id.removal_date = ref_date + datetime.timedelta(days=product.removal_time)
        self.lot_id.life_date = ref_date + datetime.timedelta(days=product.life_time)
        self.lot_id.alert_date = ref_date + datetime.timedelta(days=product.alert_time)
        self.lot_id.write({
            'name': self.new_lot_id,
            'use_date': self.new_product_bbd,
        })
