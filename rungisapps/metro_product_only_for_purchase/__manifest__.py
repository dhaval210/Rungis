{
    'name': "Metro Product Only For Purchase",

    'summary': """EMO-392: Display products from selected vendor only in PO registration""",

    'description': """
        - have Vendor's Product Only field checked by default in PO and RFQ
        - if this field is selected, order lines will only shows products from this vendor
        - if unchecked all purchaseable products will be available in order lines
        - demo video for reference https://drive.google.com/file/d/1_CSiKCyHBcqmnU9cQVLkm3qo1T5v_OWa/view

    """,

    'author': "Nisu Technology",

    'website': "https://nisu.technology",

    'category': 'Purchase',

    'version': '12.0.0.2',

    'depends': ['purchase'],


    'data': [
         'views/vendor_product_only_views.xml',
    ],

    'installable': True,

    'application': True,

}
