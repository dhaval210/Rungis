# Copyright 2016-2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Metro SFTP File Transfert',
    'version': '12.0.1.4.0',
    'license': 'AGPL-3',
    'summary': 'Customization For RUNGIS/Metro to generate UBL invoice and partner master data and transefer it to SAP server, RUN-1205, RUN-1227, RUN-1285, RUN-1206',
    "description": """
    * RUN-1227: https://jira.metrosystems.net/browse/RUN-1227
    * RUN-1285: https://jira.metrosystems.net/browse/RUN-1285
    * RUN-1205: https://jira.metrosystems.net/browse/RUN-1205
    * RUN-1206: https://jira.metrosystems.net/browse/RUN-1206
    """,
    'author': 'Hucke Media GmbH & Co KG',
    'depends': [
        'account_e-invoice_generate',
        'account_payment_partner',
        'base_ubl_payment',
        'account_invoice_ubl',
        'account_tax_unece',
        'connector',
        'metro_partner_exporter',
        'metro_account_invoice_ubl_extention',
        "metro_rungis_invoice_robot",
    ],
    'external_dependencies': {
        "python": ["pysftp", "paramiko", "cachetools"]
    },
    'data': [
        'security/ir.model.access.csv',
        
        'data/data.xml',
        
        'views/sftp_config_view.xml',
        "views/res_partner.xml",
       # 'views/account_invoice.xml',

        ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'set_xml_format_in_pdf_invoice_to_ubl',
    'uninstall_hook': 'remove_ubl_xml_format_in_pdf_invoice',
}
