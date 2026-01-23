from odoo import models, fields, api
from datetime import datetime, timedelta


class CcdocTicket(models.Model):
    _name = 'ccdoc.ticket'
    _description = 'Ticket CCDOC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'

    # Champs principaux
    name = fields.Char(string='Référence', readonly=True, copy=False, default='Nouveau')
    display_name = fields.Char(string='Nom', compute='_compute_display_name', store=True)
    subject = fields.Char(string='Sujet', required=True, tracking=True)
    description = fields.Html(string='Description')
    
    # Relations
    partner_id = fields.Many2one('res.partner', string='Client', tracking=True)
    project_id = fields.Many2one('project.project', string='Projet lié', tracking=True)
    user_id = fields.Many2one('res.users', string='Assigné à', tracking=True, 
                               default=lambda self: self.env.user)
    team_user_ids = fields.Many2many('res.users', string='Équipe')
    category_id = fields.Many2one('ccdoc.ticket.category', string='Catégorie', tracking=True)
    stage_id = fields.Many2one('ccdoc.ticket.stage', string='Étape', tracking=True,
                                group_expand='_group_expand_stages',
                                default=lambda self: self._get_default_stage())
    
    # Priorité et urgence
    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Urgente'),
    ], string='Priorité', default='1', tracking=True)
    
    # Dates
    create_date = fields.Datetime(string='Date de création', readonly=True)
    date_deadline = fields.Datetime(string='Échéance', tracking=True)
    date_assigned = fields.Datetime(string='Date d\'assignation', readonly=True)
    date_closed = fields.Datetime(string='Date de clôture', readonly=True)
    
    # SLA
    sla_hours = fields.Float(string='SLA (heures)', default=24.0)
    sla_deadline = fields.Datetime(string='Deadline SLA', compute='_compute_sla_deadline', store=True)
    sla_status = fields.Selection([
        ('on_track', 'Dans les temps'),
        ('at_risk', 'À risque'),
        ('overdue', 'En retard'),
    ], string='Statut SLA', compute='_compute_sla_status', store=True)
    
    # États calculés
    is_closed = fields.Boolean(string='Fermé', compute='_compute_is_closed', store=True)
    kanban_state = fields.Selection([
        ('normal', 'Gris'),
        ('done', 'Vert'),
        ('blocked', 'Rouge'),
    ], string='État Kanban', default='normal', tracking=True)
    
    # Couleur pour Kanban
    color = fields.Integer(string='Couleur')
    
    # Tags
    tag_ids = fields.Many2many('ccdoc.ticket.tag', string='Tags')
    
    # Canal d'origine
    origin = fields.Selection([
        ('email', 'E-mail'),
        ('phone', 'Téléphone'),
        ('web', 'Site Web'),
        ('internal', 'Interne'),
    ], string='Origine', default='internal')
    
    # Résolution
    resolution = fields.Html(string='Résolution')
    
    @api.depends('name', 'subject')
    def _compute_display_name(self):
        for ticket in self:
            if ticket.name and ticket.name != 'Nouveau':
                ticket.display_name = f"{ticket.name} - {ticket.subject or ''}"
            else:
                ticket.display_name = ticket.subject or 'Nouveau ticket'
    
    def _get_default_stage(self):
        return self.env['ccdoc.ticket.stage'].search([('is_default', '=', True)], limit=1)
    
    @api.model
    def _group_expand_stages(self, stages, domain, order):
        """Affiche toutes les étapes dans le Kanban même si vides."""
        return self.env['ccdoc.ticket.stage'].search([], order=order)
    
    @api.depends('create_date', 'sla_hours')
    def _compute_sla_deadline(self):
        for ticket in self:
            if ticket.create_date and ticket.sla_hours:
                ticket.sla_deadline = ticket.create_date + timedelta(hours=ticket.sla_hours)
            else:
                ticket.sla_deadline = False
    
    @api.depends('sla_deadline', 'is_closed', 'date_closed')
    def _compute_sla_status(self):
        now = datetime.now()
        for ticket in self:
            if not ticket.sla_deadline:
                ticket.sla_status = 'on_track'
            elif ticket.is_closed:
                if ticket.date_closed and ticket.date_closed <= ticket.sla_deadline:
                    ticket.sla_status = 'on_track'
                else:
                    ticket.sla_status = 'overdue'
            elif now > ticket.sla_deadline:
                ticket.sla_status = 'overdue'
            elif now > ticket.sla_deadline - timedelta(hours=2):
                ticket.sla_status = 'at_risk'
            else:
                ticket.sla_status = 'on_track'
    
    @api.depends('stage_id', 'stage_id.is_closed')
    def _compute_is_closed(self):
        for ticket in self:
            ticket.is_closed = ticket.stage_id.is_closed if ticket.stage_id else False
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('ccdoc.ticket') or 'Nouveau'
        return super().create(vals_list)
    
    def write(self, vals):
        # Enregistrer la date d'assignation
        if 'user_id' in vals and vals['user_id']:
            vals['date_assigned'] = datetime.now()
        
        # Enregistrer la date de clôture
        if 'stage_id' in vals:
            stage = self.env['ccdoc.ticket.stage'].browse(vals['stage_id'])
            if stage.is_closed:
                vals['date_closed'] = datetime.now()
            else:
                vals['date_closed'] = False
        
        return super().write(vals)
    
    def action_assign_to_me(self):
        """Assigner le ticket à l'utilisateur courant."""
        self.write({
            'user_id': self.env.user.id,
            'date_assigned': datetime.now(),
        })
    
    def action_close(self):
        """Fermer le ticket."""
        closed_stage = self.env['ccdoc.ticket.stage'].search([('is_closed', '=', True)], limit=1)
        if closed_stage:
            self.write({
                'stage_id': closed_stage.id,
                'date_closed': datetime.now(),
            })
    
    def action_reopen(self):
        """Réouvrir le ticket."""
        default_stage = self._get_default_stage()
        self.write({
            'stage_id': default_stage.id if default_stage else False,
            'date_closed': False,
        })


class CcdocTicketTag(models.Model):
    _name = 'ccdoc.ticket.tag'
    _description = 'Tag de ticket'

    name = fields.Char(string='Nom', required=True)
    color = fields.Integer(string='Couleur')
