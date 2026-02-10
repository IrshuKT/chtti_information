# -*- coding: utf-8 -*-
{
    'name': "Chitti Team Ten",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Irshad K T",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'finance',
    'version': '0.1',
    'application': True,
    'license':'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base','web','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/member_view.xml',
        'views/payment_views.xml',
        'views/transaction_views.xml',
        #'views/member_share.xml',
        'views/cash_bank_transfer.xml',
        'views/pending_receivers_view.xml',
        'views/upaid_members.xml',
        #'views/custom_layout.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
