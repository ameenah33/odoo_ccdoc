from odoo import models, fields, api
from odoo.exceptions import ValidationError

DEFAULT_TASK_STAGE_XMLIDS = [
    'ccdoc_custom.task_stage_attente_validation_client',
    'ccdoc_custom.task_stage_a_faire',
    'ccdoc_custom.task_stage_en_cours',
    'ccdoc_custom.task_stage_bloque',
    'ccdoc_custom.task_stage_termine',
]


class ProjectProject(models.Model):
    _inherit = 'project.project'

    partner_id = fields.Many2one('res.partner', string='Client', required=True)

    x_ref_offre = fields.Char(string='REF Offre', size=50)
    x_bu_ids = fields.Many2many('ccdoc.bu', string='BU')

    x_responsable = fields.Many2many(
        'res.users',
        'project_project_responsable_rel',
        'project_id',
        'user_id',
        string='Responsables',
    )
    x_deadline = fields.Date(string='Deadline')
    x_priorite = fields.Selection([
        ('elevee', 'Élevée'),
        ('moyenne', 'Moyenne'),
        ('faible', 'Faible'),
    ], string='Priorité')
    x_avancement = fields.Integer(string='Avancement (%)')
    x_date_demande = fields.Date(string='Date de commande')
    x_date_depot = fields.Date(string='Date de dépôt')
    x_date_validation_dc = fields.Date(string='Date validation DC')
    x_date_validation_dt = fields.Date(string='Date validation DT')
    x_date_commande = fields.Date(string='Date de commande')
    x_blocage = fields.Text(string='Blocage')
    x_etape_suivante = fields.Text(string='Étape suivante')
    x_ccdoc = fields.Char(string='CCDOC', size=50)
    x_equipe = fields.Many2many('res.users', string='Équipe projet')
    x_date_debut = fields.Date(string='Date de début')
    x_date_fin = fields.Date(string='Date de fin')
    x_charge_prevue = fields.Float(string='Charge prévue (Jours)')
    x_budget_prevu = fields.Float(string='Budget prévisionnel')
    x_budget_realise = fields.Float(string='Budget réalisé')
    x_motif_blocage = fields.Text(string='Motif de blocage')

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        self._assign_default_task_stages(projects)
        return projects

    def _assign_default_task_stages(self, projects):
        stages = self.env['project.task.type']
        for xmlid in DEFAULT_TASK_STAGE_XMLIDS:
            stage = self.env.ref(xmlid, raise_if_not_found=False)
            if stage:
                stages |= stage
        if stages:
            for project in projects:
                project.type_ids = [(4, s.id) for s in stages]