{
    'name': "Metro Product Minimum Order Quantity",

    'summary': """EMO-423: Setting up warning if Minimum Order Quantity in PO does not meet Vendor's MOQ requirement""",

    'description': """
        - If MOQ in PO is less than MOQ set by vendor in vendor form, system will show error message 'Ordered quantity is below MOQ!' in purchase order.
        - If MOQ is greater than or equal to Quantity set by vendor in product form, system will continue with the Purchase Order.
        - live demo: https://drive.google.com/file/d/1IMRG4g7xfI3MtidTzVccEmZRL5v3psUI/view
    """,

    'author': "Nisu Technology",

    'website': "https://nisu.technology",

    'category': 'Purchase',

    'version': '12.0.0.1',

    'depends': ['purchase'],

    'data': [],

    'application': False,

    'installable': True,
}
