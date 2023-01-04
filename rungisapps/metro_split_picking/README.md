# Description
split the pickings into the size of configured transport units

# IDs
- EMO-5.2
- EMO-5.8
- EMO-5.11

# Depends
- delivery
- stock

# Setup
- configure transport unit in "inventory->configuration->transport unit"
- configure "multi step routes" in "inventory->configuration->settings"
- set transport_unit in warehouse "inventory->configuration->warehouse"
- set "split by capacity" in operation type "inventory->configuration->operation type"
- set "show detailed operations" in operation type "inventory->configuration->operation type"

# New Fields
## product.category
- transport_id (ID auf Transport Unit)

## product.template
- transport_id (ID auf Transport Unit)
- base_qty 

## stock.location
- transport_id (ID auf Transport Unit)

## stock.picking.type
- split_by_capacity

## stock.picking
- transport_id (ID auf Transport Unit)
- picking_treated

## stock.warehouse
- transport_id (ID auf Transport Unit)

## transport.unit
- name
- max_weight_capacity
- max_volume_capacity

# Extended Methods
## stock.move
- _assign_picking

# New Methods
## stock.picking
- do_split
- split_by_capacity
