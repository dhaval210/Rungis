==========================
metro_product_expiry_alert
==========================

Horizontal extension to the  module product_expiry_alert Send alert mail to responsible person consolidating all lots for a product, Added purchasing team to
Lot/serial number


Installation
============

This module requires *'base','stock','metro_purchasing_team','account'* module


Usage
=====
Get Alert:

#.Go to Inventory module > Setting > check the box 'Lots & serial Numbers'

#.Go to Product > Select Product > Inventory > Traceability > check By Lots

#.Go to Purchase > Purchase Order > Create > Add Product > Confirm Order >
    Receipt there you can find a icon for adding lot click on it >
    add the serial number to product.

#.Again go to Inventory Module > Master Data >Lots/Serial Number >
  select the Lot number > add the 'Alert date'.

#.Select one purchase team and add email to the team,while running the
    sheduler you will get the alert email of the product



