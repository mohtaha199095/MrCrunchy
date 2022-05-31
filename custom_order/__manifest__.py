# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'First Task',
    'version' : '1.1',
    'summary': 'Projects rehabilitation',
    'sequence': 15,
    'description': """
Projects rehabilitation
====================
The Housing and Development Fund works on rehabilitating companies or factories.
    """,
    'category': 'Projects/rehailitation',
    'depends' : ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/first_task.xml',
    ],
   

    'installable': True,
    'application': True,
    'auto_install': False,
}