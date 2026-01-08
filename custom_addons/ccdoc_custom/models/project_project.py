from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    x_ref_offre = fields.Char(string='REF Offre', size=50)
    x_bu_ids = fields.Many2many('ccdoc.bu', string='BU')
    x_statut = fields.Char(string='Statut')
    x_responsable = fields.Many2one('res.users', string='Responsable')
    x_deadline = fields.Date(string='Deadline')
    x_priorite = fields.Selection([
        ('elevee', 'Élevée'),
        ('moyenne', 'Moyenne'),
        ('faible', 'Faible')
    ], string='Priorité')
    x_avancement = fields.Integer(string='Avancement (%)')
    x_date_demande = fields.Date(string='Date de demande')
    x_forecast = fields.Char(string='Forecast')
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


    def write(self, vals):
        # Si on archive (active passe à False), le motif de perte doit être renseigné
        if 'active' in vals and vals['active'] is False:
            for project in self:
                motif = vals.get('x_motif_perte') or project.x_motif_perte
                if not motif:
                    raise ValidationError("Vous devez renseigner le motif de perte avant d'archiver le projet.")
        return super().write(vals)