# Description
Automaticly set the transporter in pickings, based on the transporter in the partner.
Priority: Transporter in Partner > Transporter in Sale Order

# IDs

- RUN-167

# Depends
- stock
- odoo_transport_management

# Fields
## res.partner
- transporter_id: Transporter


# Methods
## stock.picking
- _onchange_partner_id
