from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_ref_offre = fields.Char(string='REF Offre', size=50)
    x_bu_ids = fields.Many2many('ccdoc.bu', string='BU')
    
    # États du projet CCDOC
    x_etat = fields.Selection([
        ('attente_validation', 'Attente de validation'),
        ('attente_paiement', 'Attente de paiement'),
        ('en_cours', 'En cours'),
        ('bloque', 'Bloqué'),
        ('en_recette', 'En recette'),
        ('en_production', 'En production'),
        ('termine', 'Terminé'),
    ], string='État du projet', default='attente_validation', tracking=True, group_expand='_group_expand_states')
    
    x_statut = fields.Char(string='Statut')  # Gardé pour compatibilité
    x_responsable = fields.Many2one('res.users', string='Responsable')
    x_deadline = fields.Date(string='Deadline')
    x_priorite = fields.Selection([
        ('elevee', 'Élevée'),
        ('moyenne', 'Moyenne'),
        ('faible', 'Faible')
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
    
    # Couleur pour le Kanban
    x_color = fields.Integer(string='Couleur', compute='_compute_color', store=True)

    @api.depends('x_etat')
    def _compute_color(self):
        """Calcule la couleur en fonction de l'état."""
        color_map = {
            'attente_validation': 3,   # Jaune
            'attente_paiement': 2,     # Orange
            'en_cours': 10,            # Vert
            'bloque': 1,               # Rouge
            'en_recette': 4,           # Bleu clair
            'en_production': 9,        # Violet
            'termine': 7,              # Vert foncé
        }
        for project in self:
            project.x_color = color_map.get(project.x_etat, 0)

    @api.model
    def _group_expand_states(self, states, domain, order):
        """Affiche tous les états dans la vue Kanban même s'ils sont vides."""
        return [key for key, val in self._fields['x_etat'].selection]

    @api.onchange('x_etat')
    def _onchange_etat(self):
        """Actions lors du changement d'état."""
        if self.x_etat == 'bloque' and not self.x_motif_blocage:
            return {
                'warning': {
                    'title': '⚠️ Motif de blocage requis',
                    'message': "Veuillez renseigner le motif de blocage.",
                }
            }

    @api.constrains('x_etat', 'x_motif_blocage')
    def _check_blocage_motif(self):
        """Vérifie que le motif est renseigné si le projet est bloqué."""
        for project in self:
            if project.x_etat == 'bloque' and not project.x_motif_blocage:
                raise ValidationError(
                    "⚠️ Le motif de blocage est obligatoire pour passer un projet en état 'Bloqué'."
                )


    def write(self, vals):
        # Si on archive (active passe à False), le motif de perte doit être renseigné
        if 'active' in vals and vals['active'] is False:
            for project in self:
                motif = vals.get('x_motif_perte') or project.x_motif_perte
                if not motif:
                    raise ValidationError("Vous devez renseigner le motif de perte avant d'archiver le projet.")
        return super().write(vals)