# Description
Auto validation of specific Pickings/Operation Types
Will check if auto validation is set in configuration and if the new picking
is inside the filter (configuration) parameter.

- RUN #123
- Depends on `stock` module.

- Added Configuration Option for to allow auto validation `Inventory > Settings`
- Added Configuration Option for Auto Validation for Filter `Inventory > Settings`.
- Added Data with default Filter for `assigned` pickings
- Modified `_check_entire_pack` from `stock.picking` model.

# Fields


# File Structure
    ├── README.md
    ├── __init__.py
    ├── __manifest__.py
    ├── data
    │   └── res_config_settings_data.xml
    ├── models
    │   ├── __init__.py
    │   ├── res_config_settings.py
    │   └── stock_picking.py
    └── views
        ├── res_config_settings_view.xml
        ├── resources.xml
        ├── stock_gate_views.xml
        └── stock_picking_views.xml
