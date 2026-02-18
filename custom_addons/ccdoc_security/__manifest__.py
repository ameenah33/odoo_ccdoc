{
    'name': 'CCDOC Security',
    'version': '17.0.1.0.0',
    'category': 'Security',
    'summary': 'Sécurisation de la plateforme Odoo CCDOC (correctifs pentest)',
    'description': """
        Module de sécurité suite aux recommandations du rapport de pentest.
        - Restriction des accès aux modèles sensibles via ACL et Record Rules
        - Limitation de la visibilité des projets et partenaires par utilisateur
        - Protection des données personnelles (emails, téléphones)
        - Journalisation des accès suspects
        - Politique de mots de passe renforcée
    """,
    'author': 'CCDOC',
    'depends': ['base', 'mail', 'project', 'crm', 'sale', 'account', 'purchase',
                'ccdoc_custom', 'ccdoc_ticketing'],
    'data': [
        'security/ir.model.access.csv',
        'security/ccdoc_security_rules.xml',
        'data/ccdoc_security_cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
