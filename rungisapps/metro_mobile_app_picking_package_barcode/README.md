# Description
This module allows you to add a barcode to your package.

# New Method
**stock.picking**
- check_barcode   
returns barcode wizard if pack is created

**stock.quant.package**
- check_name   
returns true/false if a barcode is already in use and newer than 365 days

# Extended Method
**stock.picking**
- put_in_pack   
added Wizard to put_in_pack method

# Barcode Wizard
**js validation**   
- clears the package name   
- validation of barcode input   
- action save on successfull scan   

# Depends  
- stock
