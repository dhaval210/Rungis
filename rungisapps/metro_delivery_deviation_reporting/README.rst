==================================
metro_delivery_deviation_reporting
==================================

This module allows to get email when the product missed,
product quantity changed and delivery delay while packing the sale order.

Installation
============

This module requires *'sale_management',
'metro_shipment_tour'* module


Usage
=====

Getting mail:
You need to configure mail address for corresponding sale person

Go to inventory> configuration >setting > check all the boxes  in Warehouse

Go to Inventory >Configuration >warehouse > select warehouse > Choose the outgoing Shipment

Go to sale module > configuration > setting > set Maximum Allowed Delivery Time inside Quotations & Orders.This time will calculate the delivery delay

You also need to Configure Time Zone also.otherwise did not get time in Delivery info Report

Now, Go to sale > create order > then delivery methods
If the delivery method is 3 step module affected inside pack operation
If the delivery method is 2 step module affected inside pick operation



Getting mail Report view:
Go to sale module > Report > Delivery info Here, you can get the report based on pack.










