# Description
This addon adds new fields for the connector of softm

# IDs

- RUN-70
- RUN-71
- RUN-72
- RUN-73

# Depends
- odoo_transport_management
- sale
- stock

# Fields
## sale.order
- tour_id: ID aus Tourenstamm
- run_up_point: Anlaufpunkt

## sale.order.line
- special_wishes: Sonderwünsche (Erste Stelle muss ein # sein)
- process_number: Vorgangsnummer (Mehrplatzlager)
- process_position: Vorgangsposition (Mehrplatzlager)

## stock.move
- movement_key: Bewegungsschlüssel
- send_to_softm: Status, ob Buchung an SoftM übertragen wurde
- special_wishes: Sonderwünsche (Erste Stelle muss ein # sein)
- process_number: Vorgangsnummer (Mehrplatzlager)
- process_position: Vorgangsposition (Mehrplatzlager)
- tour_id: ID aus Tourenstamm

## stock.picking
- send_to_softm: Status, ob an SoftM übertragen

## transporter.route
- tour_name Tourenbezeichnung
- tour_group Tourengruppe
- tour_depot Depot
- company_id

## product.category
- company_id

## product.product
- categ_main_id categ_main_id

# Methods
## sale.order.line
- _prepare_procurement_values

## stock.move
- _get_new_picking_values

## stock.rule
- _get_custom_move_fields
