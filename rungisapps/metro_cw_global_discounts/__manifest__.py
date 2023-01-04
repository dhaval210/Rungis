{
    'name': 'Metro CW with global discounts for Invoices',
    'version': '12.0.1.0.7',
    'license': 'AGPL-3',
    'summary': 'Customizations for Rungis/METRO, combining the tax calculation with catch weight and global discounts, RUN-1063, RUN-1085, RUN-1112, RUN-1193',
    'author': 'Niklas Hucke, Hucke Media GmbH & Co KG, Ankita',
    'description': '''RUN-1085 : https://jira.metrosystems.net/browse/RUN-1085
    RUN-1063: https://jira.metrosystems.net/browse/RUN-1063
    RUN-1112: https://jira.metrosystems.net/browse/RUN-1112
    RUN-1193: https://jira.metrosystems.net/browse/RUN-1193''',
    'depends': [
        'tis_catch_weight',
        "account_global_discount",
        'account_invoice_refund_line_selection',
    ],
    'data': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
