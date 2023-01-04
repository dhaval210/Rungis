# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api
import pytz
from pytz import timezone
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    deviated = fields.Boolean(
        string="Delivery is deviated",
        default=False,
        store=True
    )

    @api.model
    def _deviations_cron_action(self):
        # Getting the maximum allowed delivery time
        threshold = self.env['ir.config_parameter'].sudo().get_param(
            'metro_delivery_deviation_reporting.delivery_hour')

        # Check if a timezone was set in the settings. If not, cancel the cron
        tz = self.env["ir.config_parameter"].sudo().get_param(
            "metro_delivery_deviation_reporting.timezone"
        )

        if not tz:
            _logger.warn(
                "No timezone is set in the settings.\nPlease go to Sales -> Configuration -> Settings -> Quotations & Orders -> Timezone and set a timezone")
            return

        # Getting all the Sale IDs of the picking with a customer_delivery_date
        # of today
        query = "SELECT sale_id FROM stock_picking WHERE customer_delivery_date >= %s" + \
                "AND customer_delivery_date < %s GROUP BY sale_id;"
        today = datetime.now().replace(hour=0, minute=0, second=0,
                                       microsecond=0) + timedelta(
            hours=float(threshold))
        tomorrow = today + timedelta(days=1)

        # Getting the Sale Order objects expected today
        self.env.cr.execute(query, [str(today), str(tomorrow)])
        result = self.env.cr.fetchall()
        order_ids = [id[0] for id in result]
        orders = self.env["sale.order"].search([
            ("id", "in", order_ids),
            ("deviated", "=", False),
            ("state", "not in", ("draft", "cancel")),
        ])
        for order in orders:
            wh = order.warehouse_id
            if not wh:
                # If the warehouse is null the record will be skipped for now
                continue

            if wh.delivery_steps == "pick_pack_ship":
                pickings = []

                for pick in order.picking_ids:
                    # Check if the current picking is a PACK operation
                    # and if the picking is not already identified as deviated
                    prefix = pick.picking_type_id.sequence_id.prefix
                    flag = False
                    if prefix:
                        if "PICK" in prefix:
                            flag = True
                    if flag:
                        # Check for a deviation
                        pickings.append(pick)

                self.check_deviations(order, pickings, threshold)

    def check_deviations(self, order, pickings, threshold):
        order_lines = {}
        done_pickings = {}
        time_delay = False

        deviation_details = {
            "time": [],
            "missing": {},
            "cw_qty": {},
            "changed_qty": {},
            "operations": ""
        }

        # Extract the important information out of the order
        for line in order.order_line:
            product_info = {
                "qty": 0,
                "uom_id": 0
            }
            if line.product_id.id in order_lines:
                product_info = order_lines[line.product_id.id]
            product_info["qty"] += line.product_uom_qty
            product_info["uom_id"] = line.product_uom.id
            order_lines[line.product_id.id] = product_info

        for pick in pickings:
            if pick.state == "done":
                # Extract important informations of the done pickings
                # for later comparison with the order
                for line in pick.move_ids_without_package:
                    move_info = {
                        "qty_done": 0,
                        "qty_initial": 0,
                        "uom_id": 0,
                        "cw_qty_done": 0
                    }
                    if line.product_id.id in done_pickings:
                        move_info = done_pickings[line.product_id.id]

                    move_info["qty_done"] += line.quantity_done
                    move_info["qty_initial"] += line.product_uom_qty
                    move_info["uom_id"] = line.product_uom.id
                    move_info["cw_qty_done"] = line.cw_qty_done

                    done_pickings[line.product_id.id] = move_info
                    ###
            # Check every picking for a delay in time
            # Make sure that a picking without a delay doesn't
            # override the value of time_delay if one of the pickings before had a delay
            delay, latest_pack_date = self.check_delivery_date(pick, threshold)

            if delay:
                if pick.state == "done" and pick.date_done:
                    date = pick.date_done
                elif pick.state == "cancel":
                    date = "Picking cancelled"
                else:
                    date = "Not packed yet"
                deviation_details["time"].append(
                    {"name": pick.name, "date": date,
                     "latest_pack_date": latest_pack_date})
                deviation_details["operations"] += pick.name + ", "
                time_delay = True

        if time_delay:
            # Check done pickings
            order_lines, missing_product_ids = self.check_missing_products(
                order_lines, done_pickings)
            changed_qty_ids = self.check_quantities(order_lines, done_pickings)
            cw_done_qty_ids = self.check_cw_quantities(done_pickings)
            deviation_details["cw_qty"] = cw_done_qty_ids

            for key in missing_product_ids:
                deviation_details["missing"][key] = missing_product_ids[key]

            for item in changed_qty_ids:
                info = {
                    "qty_done": done_pickings[item]["qty_done"],
                    "qty_ordered": order_lines[item]["qty"],
                    "uom_id": order_lines[item]["uom_id"]
                }
                deviation_details["changed_qty"][item] = info
        # Remove the last komma from the string
        deviation_details["operations"] = deviation_details["operations"][:-2]
        # Generate and send the E-Mail to the salesperson
        # Also creates the record for packing.details
        self.send_mail(order, time_delay, deviation_details)

    # Check the delivery date
    # Returns true if package is deviated
    def check_delivery_date(self, pick, threshold):
        latest_pack_date = pick.customer_delivery_date - timedelta(
            float(threshold) / 24)

        if pick.date_done == False and datetime.now() > latest_pack_date:
            return True, latest_pack_date
        elif pick.date_done:
            if pick.date_done > latest_pack_date:
                return True, latest_pack_date

        return False, latest_pack_date

    def check_cw_quantities(self, done_pickings):
        cw_qty_ids = {}
        for p_id in done_pickings.keys():
            cw_qty_ids[p_id] = done_pickings[p_id]["cw_qty_done"]
        return cw_qty_ids

    # Check if products are missing
    # Compares the ordered products with the products moved
    # Returns true if products are missing
    def check_missing_products(self, order_lines, done_pickings):
        # products_missing = False
        missing_product_ids = {}
        filtered_order_lines = order_lines.copy()
        for key in order_lines.keys():
            if not key in done_pickings:
                # products_missing = True
                info = {
                    "qty_ordered": order_lines[key]["qty"],
                    "uom_id": order_lines[key]["uom_id"]
                }
                missing_product_ids[key] = info
                del filtered_order_lines[key]
        return filtered_order_lines, missing_product_ids

    # Check if quantities have changed
    # Compares ordered quantities with quantities moved
    # Returns true if quantities changed
    def check_quantities(self, order_lines, done_pickings):
        changed_qty_ids = []
        for key in order_lines.keys():
            # Check if the quantities are same
            if not order_lines[key]["qty"] == done_pickings[key]["qty_done"] \
                    or not order_lines[key]["uom_id"] == done_pickings[key][
                "uom_id"]:
                changed_qty_ids.append(key)
        return changed_qty_ids

    def send_mail(self, order, time_delay, deviation_details):
        responsible = order.user_id.name or "Unkown"
        msg = """Dear """ + str(responsible) + """,
        <br />
        The order """ + str(
            order.name) + """ has some delivery deviations.<br />"""
        product_details = []

        time_zone = pytz.timezone(
            self.env["ir.config_parameter"].sudo().get_param(
                "metro_delivery_deviation_reporting.timezone"
            )
        )

        current_time = pytz.utc.localize(
            datetime.now(),
            is_dst=None).astimezone(time_zone)
        formatted_current_time = current_time.strftime(
            "%Y-%m-%d "
            "%H:%M:%S")

        # A time deviation occured
        if time_delay:
            cdd = pytz.utc.localize(
                (order.commitment_date or order.expected_date),
                is_dst=None).astimezone(time_zone)
            latest_pack_date = pytz.utc.localize(
                deviation_details["time"][0]["latest_pack_date"],
                is_dst=None).astimezone(time_zone)
            msg += """<b>Difference in Delivery Time:</b>
            <br />
            Customer Delivery Date: """ + cdd.strftime("%Y-%m-%d %H:%M:%S") + \
                   """ (""" + time_zone.zone + """)""" + """<br/>Latest moment in time of packing: """ + latest_pack_date.strftime(
                "%Y-%m-%d %H:%M:%S") + \
                   """ (""" + time_zone.zone + """)""" + """<br /><ul>"""
            for item in deviation_details["time"]:
                if type(item["date"]) != type("string"):
                    date = pytz.utc.localize(
                        item["date"], is_dst=None).astimezone(time_zone)
                    msg += "<li>" + item["name"] + ": " + date.strftime(
                        "%Y-%m-%d %H:%M:%S") + " (" + time_zone.zone + ")" + "</li>"
                else:
                    msg += "<li>" + item["name"] + ": " + item[
                        "date"] + "</li>"

            msg += "</ul>"
            # Cw quantity deviated
            cw_text_flag = False
            products = self.env["product.product"].browse(
                list(deviation_details["cw_qty"].keys()))
            for item in products:
                default_code = item.product_tmpl_id.default_code or "EMPTY"
                if item.product_tmpl_id.average_cw_quantity != 0:
                    deviation = item.product_tmpl_id.average_cw_quantity * (
                            item.product_tmpl_id.max_deviation / 100) if item.product_tmpl_id.average_cw_quantity else 0
                    deviation_max_value = item.product_tmpl_id.average_cw_quantity + deviation
                    deviation_min_value = abs(
                        item.product_tmpl_id.average_cw_quantity - deviation)
                    if deviation_details["cw_qty"][
                        item.id] < deviation_min_value or (
                            deviation_details["cw_qty"][item.id]) > \
                            deviation_max_value:
                        if not cw_text_flag:
                            msg += "<b>Cw Qty Changed Products:</b><br/><ul>"
                            cw_text_flag = True
                        msg += "<li> [" + default_code + "] " + \
                               item.product_tmpl_id.name + " Ordered: " + \
                               "Min." + \
                               str(round(deviation_min_value,1)) \
                               + "->" + "Max." + str(round(deviation_max_value,1)) + ":" \
                               + str(deviation_details["cw_qty"][item.id]) + "</li>"
            msg += "</ul>"

        # Products are missing
        if len(deviation_details["missing"]) >= 1:
            msg += "<b>Missing Products:</b><br/><ul>"
            products = self.env["product.product"].browse(
                list(deviation_details["missing"].keys()))
            for item in products:
                default_code = item.product_tmpl_id.default_code or "EMPTY"

                msg += "<li> [" + default_code + "] " + item.product_tmpl_id.name + "</li>"
                detail = {}
                detail["product_id"] = item.id
                detail["qty_done"] = 0
                detail["qty_ordered"] = deviation_details["missing"][item.id][
                    "qty_ordered"]
                detail["uom_id"] = deviation_details["missing"][item.id][
                    "uom_id"]
                product_details.append(detail)
            msg += "</ul>"

        # Quantities have changed
        if len(deviation_details["changed_qty"]) >= 1:
            msg += "<b>Changed Quantities:</b><br/><ul>"
            products = self.env["product.product"].browse(
                list(deviation_details["changed_qty"].keys()))
            for item in products:
                default_code = item.product_tmpl_id.default_code or "EMPTY"

                msg += "<li> [" + default_code + "] " + item.product_tmpl_id.name + " Ordered: " + \
                       str(deviation_details["changed_qty"][item.id][
                               "qty_ordered"]) + " -> " + \
                       str(deviation_details["changed_qty"][item.id][
                               "qty_done"]) + "</li>"
                detail = {}
                detail["product_id"] = item.id
                detail["qty_done"] = deviation_details["changed_qty"][item.id][
                    "qty_done"]
                detail["qty_ordered"] = \
                deviation_details["changed_qty"][item.id]["qty_ordered"]
                detail["uom_id"] = deviation_details["changed_qty"][item.id][
                    "uom_id"]
                product_details.append(detail)

        # Create the records
        if time_delay or len(deviation_details["changed_qty"]) >= 1 \
                or len(deviation_details["missing"]) >= 1:
            # Create record in packing.details
            # Menu: Sales -> Reporting -> Delivery Deviations
            packing_detail_id = self.env["packing.details"].create({
                "order_id": order.id,
                "message_info": msg,
                "pack_operation": deviation_details["operations"],
                "time_stamp": formatted_current_time
            })
            order.deviated = True
            for detail in product_details:
                self.env["packing.details.line"].create({
                    "packing_id": packing_detail_id.id,
                    "product_id": detail["product_id"],
                    "qty_ordered": detail["qty_ordered"],
                    "qty_done": detail["qty_done"],
                    "uom_id": detail["uom_id"]
                })
            # Generate mail
            subject = "Delivery Deviation for " + deviation_details[
                "operations"]
            subject += " Related to " + order.name
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
