# Description
EMO #2.4   
This module creates an activity to collect data for new products. A new product is recognized as one,  
when the first stock.move for this product is created.

# New Fields  
**product.template**  
collect_data: flag that marks if data needs to be collected for new products

# Extended Views
**product.template**  
id: product_template_form_view  
added collect_data after purchase_ok

# Extended Methods
**stock.move**  
create:  
added functionallity that checks if it's the first stock.move for this product.  
if true create activity  
parent method will be called in any case


# Depends  
- mail
- stock
