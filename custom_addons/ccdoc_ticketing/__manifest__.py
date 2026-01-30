{
    'name': 'CCDOC Ticketing',
    'version': '17.0.1.0.0',
    'category': 'Services',
    'summary': 'Système de ticketing personnalisé pour CCDOC',
    'description': """
        Module de gestion des tickets de support pour CCDOC.
        
        Fonctionnalités:
        - Création et gestion des tickets
        - Assignation aux utilisateurs
        - Suivi des états (Nouveau, En cours, Résolu, Fermé)
        - Lien avec les projets et clients
        - Vue Kanban avec drag & drop
        - Priorités et catégories
        - SLA basique avec alertes automatiques
        - Historique et chatter
        - Notifications par email automatiques
        - Création de tickets par email
    """,
    'author': 'CCDOC',
    'depends': ['base', 'mail', 'project', 'contacts'],
    'data': [
        'security/ccdoc_ticketing_security.xml',
        'security/ir.model.access.csv',
        'data/ccdoc_ticket_sequence.xml',
        'data/ccdoc_ticket_stages.xml',
        'data/mail_templates.xml',
        'data/ccdoc_ticket_cron.xml',
        'data/assign_admin_group.xml',
        'views/ccdoc_ticket_views.xml',
        'views/ccdoc_ticket_category_views.xml',
        'views/ccdoc_ticket_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ccdoc_ticketing/static/src/css/ticket_kanban.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'icon': '/ccdoc_ticketing/static/description/icon.png',
}
