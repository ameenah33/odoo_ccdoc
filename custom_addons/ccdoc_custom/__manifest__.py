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
    'depends': ['crm', 'project', 'sale'],
    'data': [
        'views/crm_lead_views.xml',
        'views/project_views.xml',
        'views/project_project_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
