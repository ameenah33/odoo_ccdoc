{
    'name': 'CCDOC Customizations',
    'version': '1.0',
    'category': 'Customizations',
    'summary': 'Champs personnalisés CCDOC pour CRM et Projets',
    'description': """
        Module de personnalisation CCDOC
        - Ajoute des champs personnalisés au CRM
        - Ajoute des champs personnalisés aux Projets
    """,
    'author': 'CCDOC',
    'depends': ['crm', 'project', 'sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/crm_lead_justify_win_wizard_view.xml',
        'views/crm_lead_views.xml',
        'views/project_views.xml',
        'views/project_project_views.xml',
        'views/ccdoc_bu_menu.xml',
        'data/ccdoc_config.xml',
        'data/ccdoc_config_force.xml',
        'data/mail_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ccdoc_custom/static/src/css/hide_quick_buttons.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
