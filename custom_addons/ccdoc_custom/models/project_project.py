from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_ref_offre = fields.Char(string='REF Offre', size=50)
    x_bu_ids = fields.Many2many('ccdoc.bu', string='BU')

    # ── Étape dynamique (remplace l'ancien champ Selection x_etat) ──
    x_stage_id = fields.Many2one(
        'ccdoc.project.stage',
        string='Étape du projet',
        tracking=True,
        group_expand='_read_group_stage_ids',
        default=lambda self: self._default_stage_id(),
        copy=True,
        index=True,
        ondelete='restrict',
    )

    x_statut = fields.Char(string='Statut')  # Gardé pour compatibilité
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
    x_forecast = fields.Float(string='Forecast (%)')
    x_blocage = fields.Text(string='Blocage')
    x_etape_suivante = fields.Text(string='Étape suivante')
    x_ccdoc = fields.Char(string='CCDOC', size=50)
    x_equipe = fields.Many2many('res.users', string='Équipe projet')
    x_date_debut = fields.Date(string='Date de début')
    x_date_fin = fields.Date(string='Date de fin')
    x_charge_prevue = fields.Float(string='Charge prévue (Jours)')
    x_budget_prevu = fields.Float(string='Budget prévisionnel')
    x_budget_realise = fields.Float(string='Budget réalisé')
    x_motif_perte = fields.Text(string='Motif de perte')
    x_motif_blocage = fields.Text(string='Motif de blocage')

    # Couleur pour le Kanban — héritée de l'étape
    x_color = fields.Integer(string='Couleur', compute='_compute_color', store=True)

    # ── Helpers ──────────────────────────────────────────────────────

    @api.model
    def _default_stage_id(self):
        """Retourne la première étape par défaut (séquence la plus basse)."""
        return self.env['ccdoc.project.stage'].search([], order='sequence, id', limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Affiche toutes les étapes actives dans la vue Kanban, même vides."""
        return self.env['ccdoc.project.stage'].search([], order=order or 'sequence, id')

    # ── Compute / Onchange / Contraintes ─────────────────────────────

    @api.depends('x_stage_id', 'x_stage_id.color')
    def _compute_color(self):
        """Couleur du projet = couleur de son étape."""
        for project in self:
            project.x_color = project.x_stage_id.color if project.x_stage_id else 0

    @api.onchange('x_stage_id')
    def _onchange_stage_id(self):
        """Avertit si l'étape est bloquante et qu'aucun motif n'est renseigné."""
        if self.x_stage_id and self.x_stage_id.is_blocking and not self.x_motif_blocage:
            return {
                'warning': {
                    'title': '⚠️ Motif de blocage requis',
                    'message': "Veuillez renseigner le motif de blocage.",
                }
            }

    @api.constrains('x_stage_id', 'x_motif_blocage')
    def _check_blocage_motif(self):
        """Vérifie que le motif est renseigné si l'étape est bloquante."""
        for project in self:
            if project.x_stage_id and project.x_stage_id.is_blocking and not project.x_motif_blocage:
                raise ValidationError(
                    "⚠️ Le motif de blocage est obligatoire pour les projets dans l'étape « %s »."
                    % project.x_stage_id.name
                )

    def write(self, vals):
        # Si on archive (active passe à False), le motif de perte doit être renseigné
        if 'active' in vals and vals['active'] is False:
            for project in self:
                motif = vals.get('x_motif_perte') or project.x_motif_perte
                if not motif:
                    raise ValidationError(
                        "Vous devez renseigner le motif de perte avant d'archiver le projet."
                    )
        return super().write(vals)