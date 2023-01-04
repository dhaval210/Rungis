===================
Account Invoice UBL
===================

With this module, you can generate customer invoices/refunds:

* in PDF format with an embedded UBL XML file
* as an XML file with an optional embedded PDF file

This module supports UBL version 2.1 (used by default) and 2.0.

**Table of contents**

.. contents::
   :local:

Configuration
=============

In the menu *Invoicing > Configuration > Settings > Invoicing*, under
*Electronic Invoices*, check the value of 2 options:

* *XML Format embedded in PDF invoice* : if you want to have an UBL XML file
   embedded inside the PDF invoice, set it to
   *Universal Business Language (UBL)*
* if you work directly with XML invoices and you want to have the PDF invoice
  in base64 inside the XML file, enable the *Embed PDF in UBL XML Invoice*.


This module needs the SSH public key from the host environment to connect via sftp

command to excute to generate the key :

ssh-keyscan hostname or ipaddress

 example key ssh: AAAAB3NzaC1yc2EAAAADAQABAAABAQClc7Yhq+J8yl89p3tiM7F .....


Bug Tracker
===========

Python Packages to install :
===========
pysftp
paramiko
cachetools


Credits
=======

Authors
~~~~~~~

* Hucke Media GmbH & Co KG

Maintainers
~~~~~~~~~~~

