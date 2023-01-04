# Description
EMO #2.6  
This module adds an automated rule to send an email on cancelled backorders to inform the purchaser of incomplete deliveries.

# Mail Template
**id: stock_backorder_mail**  
Mail template for backorder notification. Text provided by Lars Schwebel  


# Rules
**id: stock_backorder_notification**  
filter for cancelled stock.picking with backorder_id and send mail  

# Depends  
- base_automation
- stock
