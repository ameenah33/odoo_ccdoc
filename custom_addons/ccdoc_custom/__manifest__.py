{
    'name': 'CCDOC Customizations',
    'version': '1.2',
    'category': 'Customizations',
    'summary': 'Champs personnalisés CCDOC pour CRM et Projets',
    'description': """
        Module de personnalisation CCDOC
        - Ajoute des champs personnalisés au CRM
        - Ajoute des champs personnalisés aux Projets
    """,
    'author': 'CCDOC',
    'depends': ['crm', 'project', 'sale', 'mail', 'purchase', 'account'],
    'post_init_hook': 'post_init_hook',
    'data': [
    'security/ir.model.access.csv',
    'views/ccdoc_bu_menu.xml',
    'wizard/crm_lead_justify_win_wizard_view.xml',
    'wizard/sale_order_import_wizard_view.xml',
    'views/crm_lead_views.xml',
    'views/project_project_views.xml',
    'views/sale_order_views.xml',
    'views/planner_views.xml',
    'data/project_task_stages.xml',
    'data/planner_plan_stages.xml',
    'data/planner_task_stages.xml',
    'data/ccdoc_config.xml',
    'data/ccdoc_config_force.xml',
    'data/mail_templates.xml',
    'data/crm_cron.xml',
],
    'assets': {
        'web.assets_backend': [
            'ccdoc_custom/static/src/css/hide_quick_buttons.css',
            'ccdoc_custom/static/src/js/hide_odoo_account.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
