{
    'name': 'Metro Rungis Invoice Robot',
    'version': '12.0.1.6.2',
    'license': 'AGPL-3',
    'summary': 'Customization For RUNGIS/Metro to generate invoice and Check errors in invoices and transfert invoice to partner, RUN-1134, RUN-1145, RUN-1170, RUN-1171, RUN-1182, RUN-1194',
    'description':
        """
        RUN-1134:https://jira.metrosystems.net/browse/RUN-1134
        RUN-1145:https://jira.metrosystems.net/browse/RUN-1145
        RUN-1170:https://jira.metrosystems.net/browse/RUN-1170
        RUN-1171:https://jira.metrosystems.net/browse/RUN-1171
        RUN-1182:https://jira.metrosystems.net/browse/RUN-1182
        RUN-1194:https://jira.metrosystems.net/browse/RUN-1194
        Adding the missing code for RUN-1170:https://jira.metrosystems.net/browse/RUN-1170
        RUN-1191:https://jira.metrosystems.net/browse/RUN-1191
        RUN-1195:https://jira.metrosystems.net/browse/RUN-1195
        RUN-1201:https://jira.metrosystems.net/browse/RUN-1201
        RUN-1206:https://jira.metrosystems.net/browse/RUN-1206
        """,
    'author': 'Hucke Media GmbH & Co KG',
    'depends': [
        'account',
        'account_invoice_merge',
        'account_invoice_ubl',
        "metro_account_invoice_ubl_extention",
        "queue_job",
    ],
    'data': [
        "security/security.xml",
        "data/actions.xml",
        'data/data.xml',
        'data/mail_template_data.xml',
        "data/parameter.xml",

        'views/res_partner.xml',
        'views/account_invoice.xml',
        "views/res_company.xml",
        "views/account_portal_templates.xml",
        "views/account_tax.xml",

        "wizard/invoice_merge.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'set_xml_format_in_pdf_invoice_to_ubl',
    'uninstall_hook': 'remove_ubl_xml_format_in_pdf_invoice',
}
