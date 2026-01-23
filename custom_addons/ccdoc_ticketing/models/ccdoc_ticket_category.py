from odoo import models, fields


class CcdocTicketCategory(models.Model):
    _name = 'ccdoc.ticket.category'
    _description = 'Catégorie de ticket'
    _order = 'sequence, name'

    name = fields.Char(string='Nom', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Couleur')
    default_user_id = fields.Many2one('res.users', string='Assigné par défaut')
    default_sla_hours = fields.Float(string='SLA par défaut (heures)', default=24.0)
    active = fields.Boolean(string='Actif', default=True)
    
    ticket_count = fields.Integer(string='Nombre de tickets', compute='_compute_ticket_count')
    
    def _compute_ticket_count(self):
        for category in self:
            category.ticket_count = self.env['ccdoc.ticket'].search_count([
                ('category_id', '=', category.id)
            ])
