from odoo import models, fields


class CcdocTicketStage(models.Model):
    _name = 'ccdoc.ticket.stage'
    _description = 'Étape de ticket'
    _order = 'sequence, id'

    name = fields.Char(string='Nom de letape', required=True, translate=True)
    sequence = fields.Integer(string='Séquence', default=10)
    description = fields.Text(string='Description')
    fold = fields.Boolean(string='Replié dans Kanban', default=False)
    is_default = fields.Boolean(string='Étape par défaut', default=False)
    is_closed = fields.Boolean(string='Étape de clôture', default=False)
    color = fields.Integer(string='Couleur')

    mail_template_id = fields.Many2one('mail.template', string='Modèle d\'email')
    
    ticket_count = fields.Integer(string='Nombre de tickets', compute='_compute_ticket_count')
    
    def _compute_ticket_count(self):
        for stage in self:
            stage.ticket_count = self.env['ccdoc.ticket'].search_count([
                ('stage_id', '=', stage.id)
            ])
