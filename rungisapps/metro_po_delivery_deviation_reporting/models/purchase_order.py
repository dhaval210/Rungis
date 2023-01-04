# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import pytz
from pytz import timezone
import logging


_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # If deviated is true, the order was checked and classified as deviated
    deviated = fields.Boolean()
    
    # Cron action for detecting deviations, gets PO which should be checked for deviations
    @api.model
    def _deviations_cron_action(self):
        # Query for getting the picking ids
        query = """SELECT p.id FROM purchase_order AS p WHERE p.state IN ('purchase', 'done') AND p.date_planned>=%s
            AND p.date_planned<=%s AND (p.deviated=false OR p.deviated IS NULL)
            ORDER BY p.id DESC;"""
        # Tolerance for the scheduled date
        tolerance = self.env["ir.config_parameter"].sudo().get_param(
            'metro_po_delivery_deviation_reporting.tolerance'
        )
        if not tolerance:
            tolerance = 0
        # Check if timezone setting is set
        time_zone = self.env["ir.config_parameter"].sudo().get_param(
            "metro_po_delivery_deviation_reporting.timezone"
        )
        if not time_zone:
            _logger.warn("No timezone is set in the settings.\nPlease go to Purchase -> Configuration -> Settings -> Products -> Timezone and set a timezone")
            return
        
        # Calculate timeframe for getting the pickings
        last_day = datetime.now() - timedelta(hours=float(tolerance))
        first_day = last_day - timedelta(days=1)

        # Get picking ids from the database
        # every item which gets returned by this query should already be delivered
        # if not, it automatically has a deviation in time. If it is delivered the date_done must be checked
        self.env.cr.execute(query, [str(first_day), str(last_day)])
        res = self.env.cr.fetchall()
        ids = [id[0] for id in res]
        
        # Get picking objects
        orders = self.env["purchase.order"].browse(ids)
        self._check_deviations(orders, tolerance)

    # Checks for a deviation in time, missing products or changed quantities for each PO
    # Gets called from _deviations_cron_action(), reports a deviation if there is one
    @api.model
    def _check_deviations(self, orders, tolerance):
        for order in orders:
            # Check if there is a deviation in time
            time_deviation = self._check_time_deviation(order, tolerance)

            # Check if less products were delivered than ordered
            missing_ids = self._check_missing_products(order)

            # Check if less quantities were delivered than ordered
            changed_qty = self._check_quantities(order)

            # Report a deviation if quantities have changed, products are missing or
            # the items were delivered to late
            if time_deviation or len(missing_ids) > 0 or len(changed_qty) > 0:
                self._report_deviation(order, time_deviation, missing_ids, changed_qty)

    # Checks for a deviation in time.
    # If the date_done of the picking is after the scheduled date + the tolerance, it's deviated
    # If the picking is not packed yet, it's deviated
    # Returns the time the picking was done or "Nothing received yet" if package is deviated
    # Returns None if there is no deviation in time
    def _check_time_deviation(self, order, tolerance):
        # Get pickings
        query = "SELECT s.id FROM stock_picking AS s WHERE s.origin=%s AND s.picking_type_id=%s AND s.state != 'cancel';"
        self.env.cr.execute(query, [order.name, order.picking_type_id.id])
        res = self.env.cr.fetchall()
        ids = [id[0] for id in res]

        pickings = self.env["stock.picking"].browse(ids)

        deviated_pickings = {}

        # If at least on picking has a time deviation, return true
        for picking in pickings:
            # Get the timeframe the picking is not deviated
            earliest = order.date_planned - timedelta(hours=float(tolerance))
            latest = order.date_planned + timedelta(hours=float(tolerance))
            # If picking is done, check if it was done before or after the scheduled date
            if picking.date_done:
                if latest < picking.date_done or earliest > picking.date_done:
                    tz = pytz.timezone(
                        self.env["ir.config_parameter"].sudo().get_param(
                            "metro_po_delivery_deviation_reporting.timezone"
                        )
                    )
                    t = pytz.utc.localize(
                        picking.date_done, is_dst=None
                    ).astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
                    # return str(t)
                    deviated_pickings[picking.name] = str(t)
            # If not done, the picking is automatically deviated (should already be packed)
            else:
                deviated_pickings[picking.name] = "Nothing received yet."
                # return "Nothing received yet."
        return deviated_pickings

    # Checks if all products were delivered
    # It returns a dictionary of the products information, if
    # at least one product is missing. It returns an empty dictionary if all products are present.
    def _check_missing_products(self, order):
        missing_ids = {}
        ids_with_qty = []
        # Add products to missing_ids if the received_qty is equal or less than 0
        for line in order.order_line:
            if line.qty_received <= 0:
                if line.product_id.id in missing_ids:
                    missing_ids[line.product_id.id] += line.product_qty
                else:
                    missing_ids[line.product_id.id] = line.product_qty
            else:
                ids_with_qty.append(line.product_id.id)

        # Remove products from missing which had a quantity
        for id in ids_with_qty:
            if id in missing_ids:
                del missing_ids[id]
        return missing_ids

    # Checks if all products were shipped with the same quantity as ordered.
    # If at least one quantity has changed, the returned dictionary will have a length
    # If no quantity has changed, the returned dictionary will be empty
    def _check_quantities(self, order):
        raw_quantities = {}
        for line in order.order_line:
            p_info = {"expected": 0, "received": 0}
            if line.product_id.id in raw_quantities:
                p_info = raw_quantities[line.product_id.id]
            
            p_info["expected"] += line.product_qty
            p_info["received"] += line.qty_received

            raw_quantities[line.product_id.id] = p_info
        # Remove items w/ same quantity or 0 quantity
        changed_qty = {}
        for k,v in raw_quantities.items():
            p = self.env["product.product"].browse([k])
            if v["expected"] != v["received"] and v["received"] != 0:
                changed_qty[k] = v

        return changed_qty

    # Generate the deviation message and create purchase.order.deviation records
    # When this function gets called it means the order was already identified as deviated
    def _report_deviation(self, order, time_deviation, missing_ids, changed_qty):
        responsible = order.user_id.name or "Unkown"
        msg = "Dear "+responsible+",<br/>"
        msg += "The order "+ order.name +" has some delivery deviations.<br/>"

        time_zone = pytz.timezone(
            self.env["ir.config_parameter"].sudo().get_param(
                "metro_po_delivery_deviation_reporting.timezone"
            )
        )

        # if time_deviation:
        if len(time_deviation) > 0:
            expected = pytz.utc.localize(
                order.date_planned, is_dst=None
            ).astimezone(time_zone).strftime("%Y-%m-%d %H:%M:%S")

            msg += "<b>Difference in delivery time ("+ time_zone.zone +"):</b><br/>"
            msg += "Expected date: "+ str(expected)
            msg += "<ul>"
            for name,date in time_deviation.items():
                msg += "<li>"+ name + ": "+ date +"</li>"
            msg += "</ul>"
        
        if len(missing_ids) > 0:
            msg += "<b>Products are missing: </b><br/><ul>"
            for id in missing_ids.keys():
                p = self.env["product.product"].browse([id])
                code = p.product_tmpl_id.default_code or "EMPTY"
                msg += "<li>["+code+"] "+ p.name  +"</li>"
            msg += "</ul>"
        
        if len(changed_qty) > 0:
            msg += "<b>Quantities have changed:</b><br/><ul>"
            for id,qtys in changed_qty.items():
                p = self.env["product.product"].browse([id])
                code = p.product_tmpl_id.default_code or "EMPTY"
                msg += "<li>["+code+"] "+p.name+": " + str(qtys["expected"]) + " -> " + str(qtys["received"]) + "</li>"
            msg += "</ul>"
        
        pod_id = self.env["purchase.order.deviation"].create({
            "order_id": order.id,
            "message": msg,
            "time_stamp": datetime.now()
        })
        order.deviated = True
        for pid,qty in missing_ids.items():
            p = self.env["product.product"].browse([pid])
            self.env["purchase.order.deviation.line"].create({
                "deviation_id": pod_id.id,
                "product_id": p.id,
                "qty_ordered": qty,
                "qty_done": 0,
                "uom_id": p.uom_id.id
            })
        for pid,qtys in changed_qty.items():
            p = self.env["product.product"].browse([pid])
            self.env["purchase.order.deviation.line"].create({
                "deviation_id": pod_id.id,
                "product_id": p.id,
                "qty_ordered": qtys["expected"],
                "qty_done": qtys["received"],
                "uom_id": p.uom_id.id
            })
        
        self._send_deviation_mail(order, msg)

    # Generate the E-Mail headers and create and send the mail record
    def _send_deviation_mail(self, order, msg):
        # Generate mail
        subject = "Delivery Deviation for " + order.name
        mail = ""
        if order.user_id:
            mail = order.user_id.email or ""
        mail_content = {
            "subject": subject,
            "body_html": msg,
            "email_to": mail,
            "auto_delete": True
        }

        self.env["mail.mail"].create(mail_content).send()
        order.message_post(body=msg)

