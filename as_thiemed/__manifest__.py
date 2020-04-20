# -*- coding: utf-8 -*-
{
    'name': "Ahorasoft Thiemed Project",
    'category': 'Thiemed',
    'version': '1.0.4',
    'author': "Ahorasoft",
    'website': 'http://www.ahorasoft.com',
    "support": "soporte@ahorasoft.com",
    'summary': """
        Ahorasoft Thiemed Project""",
    'description': """
        Ahorasoft Thiemed Project
    """,
    "images": [],
    "depends": [
        "base","stock","product","report_xlsx","account"
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/as_kardex_productos_wiz.xml',
        'wizard/as_cambiador_factura.xml'
    ],
    'qweb': [
    ],
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'installable': True,
    'auto_install': False,
    
}