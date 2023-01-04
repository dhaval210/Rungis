# Description
Gate Management

- EMO: #2.1/2.2
- Depends on `stock` module.

- Added Configuration Option for default Operation Type (default=Receipts) in `Settings > General Settings > Inventory > Gate Management`.
- Added Configuration Option for Gates in `Inventory > Configuration > Gates`.
- Added Kanban View in `Inventory > Operations > Gates`.
- Added Model `stock.gate` which contains all gates.
- Added Fields to `stock.picking`.
- Modified `_openRecord` from `Kanban_Record.js` because the `click event` was overwritten from `Stock Barcode`.

# Fields
**stock.gate**

- `name` Name (e.g.: Gate 1) (Char) (Unique)
- `active` Is Gate active? (Boolean)

**stock.picking**

- `gate_id` ID (Integer)
- `gate_assigned` Date when gate was assigned (Datetime)
- `status_complete` Date when status was changed to complete (Datetime)


# File Structure
    ├── README.md
    ├── __init__.py
    ├── __manifest__.py
    ├── data
    │   └── res_config_settings_data.xml
    ├── models
    │   ├── __init__.py
    │   ├── __pycache__
    │   ├── res_config_settings.py
    │   ├── stock_gate.py
    │   └── stock_picking.py
    ├── security
    │   └── ir.model.access.csv
    ├── static
    │   └── src
    │       └── js
    │           └── stock_picking.js
    └── views
        ├── res_config_settings_view.xml
        ├── resources.xml
        ├── stock_gate_views.xml
        └── stock_picking_views.xml
