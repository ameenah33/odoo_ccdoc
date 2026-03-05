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
    x_ref_projet = fields.Char(string='REF Projet', size=50)
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

    @api.onchange('x_bu_ids')
    def _onchange_bu_ids(self):
        """Génère automatiquement la REF Projet quand on sélectionne des BU."""
        if self.x_bu_ids and not self.x_ref_projet:
            self._generate_ref_projet()

    def _generate_ref_projet(self):
        """Génère la référence projet basée sur les BU sélectionnées."""
        if not self.x_bu_ids:
            return
        date_str = fields.Date.context_today(self).strftime('%d%m%Y')
        last_num = self._get_last_projet_num(exclude_id=self._origin.id or None)
        new_num = last_num + 1
        ref_projets = []
        for bu in self.x_bu_ids:
            bu_prefix = bu.name[:3].upper() if bu.name else 'XXX'
            ref_projets.append(f"{bu_prefix}-{date_str}-{new_num}")
        self.x_ref_projet = ', '.join(ref_projets)

    def _get_last_projet_num(self, exclude_id=None):
        """Retourne le dernier numéro de séquence utilisé dans les REF Projet."""
        domain = [('x_ref_projet', '!=', False)]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))
        last_num = 0
        for project in self.env['project.project'].search(domain):
            for ref in project.x_ref_projet.split(','):
                try:
                    num = int(ref.strip().split('-')[-1])
                    if num > last_num:
                        last_num = num
                except (ValueError, IndexError):
                    continue
        return last_num

    @api.model
    def _compute_new_ref_projet(self, bu_ids):
        """Calcule une nouvelle REF Projet pour une liste de BU IDs (utilisé à la création)."""
        date_str = fields.Date.context_today(self).strftime('%d%m%Y')
        last_num = self._get_last_projet_num()
        new_num = last_num + 1
        bu_objs = self.env['ccdoc.bu'].browse(bu_ids)
        ref_projets = []
        for bu in bu_objs:
            bu_prefix = bu.name[:3].upper() if bu.name else 'XXX'
            ref_projets.append(f"{bu_prefix}-{date_str}-{new_num}")
        return ', '.join(ref_projets)

    @staticmethod
    def _extract_bu_ids_from_vals(bu_vals):
        """Extrait les IDs de BU depuis les différents formats ORM."""
        if not bu_vals or not isinstance(bu_vals, list):
            return []
        first = bu_vals[0]
        if isinstance(first, (list, tuple)):
            if first[0] == 6:
                return first[2]
            elif first[0] == 4:
                return [item[1] for item in bu_vals if item[0] == 4]
        elif isinstance(first, int):
            return bu_vals
        return []

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('x_ref_projet') and vals.get('x_bu_ids'):
                bu_ids = self._extract_bu_ids_from_vals(vals['x_bu_ids'])
                if bu_ids:
                    vals['x_ref_projet'] = self._compute_new_ref_projet(bu_ids)
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