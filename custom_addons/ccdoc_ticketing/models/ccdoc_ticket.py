from odoo import models, fields, api
from datetime import datetime, timedelta


class CcdocTicket(models.Model):
    _name = 'ccdoc.ticket'
    _description = 'Ticket CCDOC'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'mail.alias.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'
    def _alias_get_creation_values(self):
        """Valeurs pour la création automatique de tickets depuis un email."""
        values = super()._alias_get_creation_values()
        values['alias_model_id'] = self.env['ir.model']._get('ccdoc.ticket').id
        values['alias_force_thread_id'] = 0
        return values

    name = fields.Char(string='Référence', readonly=True, copy=False, default='Nouveau')
    display_name = fields.Char(string='Nom', compute='_compute_display_name', store=True)
    subject = fields.Char(string='Sujet', required=True, tracking=True)
    description = fields.Html(string='Description')

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
    
    color = fields.Integer(string='Couleur')
    tag_ids = fields.Many2many('ccdoc.ticket.tag', string='Tags')
    origin = fields.Selection([
        ('email', 'E-mail'),
        ('phone', 'Téléphone'),
        ('web', 'Site Web'),
        ('internal', 'Interne'),
    ], string='Origine', default='internal')
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
            if not vals.get('partner_id'):
                user = self.env.user
                # Vérifier si l'utilisateur a le rôle Demandeur
                if user.has_group('ccdoc_ticketing.group_ccdoc_ticketing_requester'):
                    # Trouver le partneraire lié au user
                    if user.partner_id:
                        vals['partner_id'] = user.partner_id.id

        tickets = super().create(vals_list)
        for ticket in tickets:
            ticket._send_notification_creation()

        return tickets

    def _send_notification_creation(self):
        """Envoie une notification par email lors de la création du ticket."""
        template = self.env.ref('ccdoc_ticketing.mail_template_ticket_creation', raise_if_not_found=False)
        if template and self.partner_id:
            template.send_mail(self.id, force_send=True, email_values={
                'email_to': self.partner_id.email,
            })
    
    def write(self, vals):
        old_stages = {ticket.id: ticket.stage_id for ticket in self}

        if 'user_id' in vals and vals['user_id']:
            vals['date_assigned'] = datetime.now()
        if 'stage_id' in vals:
            stage = self.env['ccdoc.ticket.stage'].browse(vals['stage_id'])
            if stage.is_closed:
                vals['date_closed'] = datetime.now()
            else:
                vals['date_closed'] = False

        result = super().write(vals)
        if 'stage_id' in vals:
            for ticket in self:
                old_stage = old_stages.get(ticket.id)
                if old_stage and old_stage.id != ticket.stage_id.id:
                    ticket._send_notification_stage_change(old_stage, ticket.stage_id)

        return result

    def _send_notification_stage_change(self, old_stage, new_stage):
        """Envoie une notification par email lors du changement d'étape."""
        # Notification de clôture
        if new_stage.is_closed:
            template = self.env.ref('ccdoc_ticketing.mail_template_ticket_closed', raise_if_not_found=False)
        else:
            # Notification de changement de statut général
            template = self.env.ref('ccdoc_ticketing.mail_template_ticket_stage_change', raise_if_not_found=False)

        if template and self.partner_id:
            template.with_context(
                old_stage_name=old_stage.name,
                new_stage_name=new_stage.name
            ).send_mail(self.id, force_send=True, email_values={
                'email_to': self.partner_id.email,
            })
    
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

    def action_open_partner(self):
        """Ouvrir la fiche du client."""
        self.ensure_one()
        if not self.partner_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Client',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _cron_check_sla_alerts(self):
        """Vérifie les tickets avec SLA dépassé ou à risque et envoie des alertes.
        Cette méthode est appelée par le cron job toutes les heures.
        """
        # Rechercher les tickets ouverts avec SLA à risque ou dépassé
        tickets = self.search([
            ('is_closed', '=', False),
            ('sla_status', 'in', ['overdue', 'at_risk']),
            ('user_id', '!=', False),  # Uniquement les tickets assignés
        ])

        template = self.env.ref('ccdoc_ticketing.mail_template_ticket_sla_alert', raise_if_not_found=False)

        if not template:
            return

        # Envoyer une alerte pour chaque ticket
        for ticket in tickets:
            # Vérifier si une alerte n'a pas déjà été envoyée récemment (dans les dernières 24h)
            last_message = self.env['mail.message'].search([
                ('model', '=', 'ccdoc.ticket'),
                ('res_id', '=', ticket.id),
                ('subject', 'like', 'Alerte SLA'),
            ], order='create_date desc', limit=1)

            # Si aucun message ou dernier message il y a plus de 24h
            if not last_message or (datetime.now() - last_message.create_date).total_seconds() > 86400:
                try:
                    template.send_mail(ticket.id, force_send=True, email_values={
                        'email_to': ticket.user_id.email,
                    })
                except Exception as e:
                    # Log l'erreur mais continue avec les autres tickets
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.error(f"Erreur lors de l'envoi de l'alerte SLA pour le ticket {ticket.name}: {str(e)}")


class CcdocTicketTag(models.Model):
    _name = 'ccdoc.ticket.tag'
    _description = 'Tag de ticket'

    name = fields.Char(string='Nom', required=True)
    color = fields.Integer(string='Couleur')
