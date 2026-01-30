
# -*- coding: utf-8 -*-
import logging
from markupsafe import Markup
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # =====================================================================
    # CHAMPS PERSONNALISÉS
    # =====================================================================
    
    # Justification de gain
    x_justification_win = fields.Text(string="Justification gain")
    x_signed_po_attachment_id = fields.Many2one(
        'ir.attachment', 
        string="Bon de commande signé", 
        readonly=True
    )
    
    # Notification d'envoi
    x_contacts_a_notifier = fields.Many2many(
        'res.partner', 
        'crm_lead_notif_partner_rel',
        'lead_id',
        'partner_id',
        string="Contacts à notifier lors de l'envoi"
    )
    x_envoi_notifie = fields.Boolean(
        string="Envoi notifié", 
        default=False,
        help="Cochez cette case pour notifier les contacts sélectionnés."
    )
    
    # Références et classification
    x_ref_offre = fields.Char(string='REF Offre', size=50, tracking=True)
    x_bu_ids = fields.Many2many('ccdoc.bu', string='BU', tracking=True)
    
    # Suivi
    x_blocage = fields.Text(string='Blocage', tracking=True)
    x_etape_suivante = fields.Text(string='Étape suivante', tracking=True)
    
    # Dates
    x_date_depot = fields.Date(string='Date Dépôt', tracking=True)
    x_date_validation_dc = fields.Date(string='Date Validation DC', tracking=True)
    x_deadline_validation_dc = fields.Date(string='Échéance Validation DC', tracking=True)
    x_date_validation_dt = fields.Date(string='Date Validation DT', tracking=True)
    x_deadline_validation_dt = fields.Date(string='Échéance Validation DT', tracking=True)
    x_date_commande = fields.Date(string='Date Commande', tracking=True)
    x_date_demande = fields.Date(string='Date de demande', tracking=True)
    x_deadline = fields.Date(string='Deadline', tracking=True)
    
    # Statut et responsabilité
    x_statut = fields.Char(string='Statut', tracking=True)
    x_responsable = fields.Many2many(
        'res.users',
        'crm_lead_responsable_rel',
        'lead_id',
        'user_id',
        string='Responsables',
        tracking=True
    )
    x_priorite = fields.Selection([
        ('faible', 'Faible'),
        ('moyenne', 'Moyenne'),
        ('elevee', 'Élevée')
    ], string='Priorité', tracking=True)
    
    # Prévisions
    x_forecast = fields.Float(string='Forecast (%)', tracking=True)
    x_avancement = fields.Integer(string='Avancement (%)', tracking=True)
    
    # Projet lié
    project_id = fields.Many2one('project.project', string='Projet lié', tracking=True)

    # =====================================================================
    # MÉTHODES ONCHANGE
    # =====================================================================
    
    @api.onchange('x_envoi_notifie')
    def _onchange_envoi_notifie(self):
        """Avertissement si on coche sans avoir sélectionné de contacts."""
        if self.x_envoi_notifie and not self.x_contacts_a_notifier:
            return {
                'warning': {
                    'title': '⚠️ Aucun contact sélectionné',
                    'message': "Veuillez sélectionner des contacts à notifier.",
                }
            }

    @api.onchange('x_bu_ids')
    def _onchange_bu_ids(self):
        """Génère automatiquement la REF Offre quand on change les BU."""
        self._generate_ref_offre()

    @api.onchange('stage_id')
    def _onchange_stage_id_check_won(self):
        """Avertissement lors du changement d'étape vers Gagné."""
        if self.stage_id and self.stage_id.is_won:
            if not self.x_justification_win or not self.x_signed_po_attachment_id:
                if self._origin and self._origin.stage_id:
                    self.stage_id = self._origin.stage_id
                return {
                    'warning': {
                        'title': '⚠️ Justification requise',
                        'message': "Utilisez le bouton 'Justificatif de gain' avant de passer en 'Gagné'.",
                    }
                }

    # =====================================================================
    # MÉTHODE CREATE (CORRIGÉE POUR ODOO 17)
    # =====================================================================
    
    @api.model_create_multi
    @api.model_create_multi
    def create(self, vals_list):
        """Génération automatique de la REF Offre pour chaque opportunité créée."""
        for vals in vals_list:
            # Extraire les IDs des BU
            bu_ids = vals.get('x_bu_ids', [])
            bu_list = []
            
            if bu_ids:
                if isinstance(bu_ids, list) and len(bu_ids) > 0:
                    # Format [(6, 0, [ids])]
                    if isinstance(bu_ids[0], (list, tuple)) and len(bu_ids[0]) >= 3 and bu_ids[0][0] == 6:
                        bu_list = bu_ids[0][2]
                    # Format [(4, id), (4, id2), ...]
                    elif isinstance(bu_ids[0], (list, tuple)) and bu_ids[0][0] == 4:
                        bu_list = [item[1] for item in bu_ids if item[0] == 4]
                    # Format [id1, id2, ...]
                    elif isinstance(bu_ids[0], int):
                        bu_list = bu_ids
            
            # Générer la REF Offre si des BU sont sélectionnées
            if bu_list:
                bu_objs = self.env['ccdoc.bu'].browse(bu_list)
                date_str = fields.Date.context_today(self).strftime('%d%m%Y')
                
                # Trouver le dernier numéro utilisé (chercher dans TOUTES les refs)
                last_num = 0
                all_leads = self.env['crm.lead'].search([('x_ref_offre', '!=', False)])
                for lead in all_leads:
                    if lead.x_ref_offre:
                        # Parcourir toutes les refs (peut y en avoir plusieurs séparées par virgule)
                        for ref in lead.x_ref_offre.split(','):
                            ref = ref.strip()
                            try:
                                # Extraire le numéro à la fin (après le dernier tiret)
                                num = int(ref.split('-')[-1])
                                if num > last_num:
                                    last_num = num
                            except (ValueError, IndexError):
                                continue
                
                # Incrémenter pour la nouvelle opportunité
                new_num = last_num + 1
                
                # Construire les références
                ref_offres = []
                for bu in bu_objs:
                    bu_prefix = bu.name[:3].upper() if bu.name else 'XXX'
                    ref_offres.append(f"{bu_prefix}-{date_str}-{new_num}")
                
                vals['x_ref_offre'] = ', '.join(ref_offres) if ref_offres else ''
        
        return super().create(vals_list)

    # =====================================================================
    # MÉTHODE WRITE (UNIFIÉE)
    # =====================================================================
    
    def write(self, vals):
        """Gère les notifications d'envoi et les changements d'étape."""
        today = fields.Date.context_today(self)
        
        # --- Notification d'envoi ---
        if vals.get('x_envoi_notifie'):
            for lead in self:
                if not lead.x_envoi_notifie and lead.x_contacts_a_notifier:
                    self._send_envoi_notification(lead, today)
        
        # --- Changement d'étape ---
        if 'stage_id' in vals:
            stage = self.env['crm.stage'].browse(vals['stage_id'])
            stage_name = (stage.name or '').lower()
            
            # Dates automatiques selon l'étape
            if 'validation dc' in stage_name:
                vals['x_date_validation_dc'] = today
            if 'validation dt' in stage_name:
                vals['x_date_validation_dt'] = today
            
            # Passage en Gagné
            if stage and stage.is_won:
                vals['x_date_commande'] = today
                for lead in self:
                    self._check_won_requirements(lead)
                    lead.action_create_project_and_sale()
        
        return super().write(vals)

    def _send_envoi_notification(self, lead, today):
        """Envoie une notification aux contacts sélectionnés."""
        contacts = lead.x_contacts_a_notifier
        if not contacts:
            return
        
        partner_ids = contacts.ids
        contact_names = ', '.join(contacts.mapped('name'))
        
        body = Markup('''
        <div style="background: linear-gradient(135deg, #667eea 0%%, #764ba2 100%%); 
                    padding: 15px; border-radius: 10px; color: white; margin-bottom: 15px;">
            <h3 style="margin: 0; color: white;">📤 Dossier envoyé au client</h3>
        </div>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; 
                    border-left: 4px solid #667eea;">
            <p><strong>📋 Référence:</strong> %s</p>
            <p><strong>🏢 Client:</strong> %s</p>
            <p><strong>📅 Date d'envoi:</strong> %s</p>
            <p><strong>👥 Notifiés:</strong> %s</p>
        </div>
        ''') % (
            lead.x_ref_offre or lead.name,
            lead.partner_id.name if lead.partner_id else 'Non défini',
            today.strftime('%d/%m/%Y'),
            contact_names
        )
        
        lead.message_post(
            body=body,
            subject="📤 Dossier envoyé au client",
            partner_ids=partner_ids,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

    def _check_won_requirements(self, lead):
        """Vérifie les prérequis pour passer en Gagné."""
        if not lead.x_justification_win and not lead.x_signed_po_attachment_id:
            raise UserError(
                "⚠️ Justification requise !\n\n"
                "Avant de marquer cette opportunité comme gagnée :\n"
                "1. Cliquez sur 'Justificatif de gain'\n"
                "2. Renseignez la justification\n"
                "3. Uploadez le bon de commande signé"
            )
        elif not lead.x_justification_win:
            raise UserError("⚠️ Justification manquante !")
        elif not lead.x_signed_po_attachment_id:
            raise UserError("⚠️ Bon de commande signé manquant !")

    # =====================================================================
    # CONTRAINTES
    # =====================================================================
    
    @api.constrains('stage_id')
    def _check_won_justification(self):
        """Contrainte : empêche le passage en Gagné sans justification."""
        for lead in self:
            if lead.stage_id and lead.stage_id.is_won:
                if not lead.x_justification_win or not lead.x_signed_po_attachment_id:
                    raise ValidationError(
                        "⚠️ Justification et document requis pour passer en Gagné !"
                    )

    @api.constrains('x_date_depot', 'x_date_validation_dc', 'x_date_validation_dt', 'x_date_commande')
    def _check_dates_after_create_date(self):
        """Vérifie que les dates sont postérieures à la date de création."""
        for lead in self:
            if not lead.create_date:
                continue
            create_date = lead.create_date.date()
            
            dates_to_check = [
                ('x_date_depot', 'Date de dépôt'),
                ('x_date_validation_dc', 'Date validation DC'),
                ('x_date_validation_dt', 'Date validation DT'),
                ('x_date_commande', 'Date commande'),
            ]
            
            for field_name, field_label in dates_to_check:
                date_val = getattr(lead, field_name)
                if date_val and date_val < create_date:
                    raise ValidationError(
                        f"⚠️ {field_label} doit être postérieure à la date de création."
                    )

    # =====================================================================
    # ACTIONS
    # =====================================================================
    
    def action_set_won(self):
        """Surcharge de l'action Gagné standard."""
        for lead in self:
            self._check_won_requirements(lead)
        return super().action_set_won()

    def action_open_purchase(self):
        """Ouvre le formulaire de création de bon de commande fournisseur."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bon de commande fournisseur',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_origin': self.x_ref_offre,
            },
        }

    def action_open_sale(self):
        """Ouvre le formulaire de création de devis client."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Devis client',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_opportunity_id': self.id,
                'default_origin': self.x_ref_offre,
            },
        }

    def action_justify_win(self):
        """Ouvre le wizard de justification de gain."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.justify.win.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_attachment_id': False, 
                'active_id': self.id
            },
        }

    def action_create_project_and_sale(self):
        """Crée le projet et la commande de vente lors du passage en Gagné."""
        bu_list = self.x_bu_ids
        if not bu_list:
            bu_list = self.env['ccdoc.bu'].search([], limit=1)
        
        if not bu_list:
            _logger.warning("Aucune BU trouvée pour créer le projet")
            return
        
        ref_offres = [ref.strip() for ref in (self.x_ref_offre or '').split(',') if ref.strip()]
        
        for idx, bu in enumerate(bu_list):
            # Déterminer la référence pour cette BU
            if idx < len(ref_offres):
                ref_offre_bu = ref_offres[idx]
            else:
                ref_offre_bu = f"{self.x_ref_offre or self.name}-{bu.name}"
            
            # Créer le projet s'il n'existe pas
            existing_project = self.env['project.project'].search([
                ('x_ref_offre', '=', ref_offre_bu)
            ], limit=1)
            
            if not existing_project:
                project = self.env['project.project'].create({
                    'name': f"{self.name} [{bu.name}]",
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'x_ref_offre': ref_offre_bu,
                    'x_bu_ids': [(6, 0, [bu.id])],
                    'x_etat': 'attente_validation',
                    'x_responsable': [(6, 0, self.x_responsable.ids)] if self.x_responsable else False,
                    'x_deadline': self.x_deadline,
                    'x_priorite': self.x_priorite,
                    'x_avancement': self.x_avancement or 0,
                    'x_date_demande': self.x_date_demande,
                    'x_date_depot': self.x_date_depot,
                    'x_date_validation_dc': self.x_date_validation_dc,
                    'x_date_validation_dt': self.x_date_validation_dt,
                    'x_date_commande': self.x_date_commande,
                    'x_forecast': self.x_forecast or 0.0,
                    'x_blocage': self.x_blocage,
                    'x_etape_suivante': self.x_etape_suivante,
                })
                self._ccdoc_create_wbs(project)
                self.project_id = project.id
            
            # Créer la commande de vente
            self._ccdoc_create_sale_order_bu(bu, ref_offre_bu)

    # =====================================================================
    # MÉTHODES UTILITAIRES
    # =====================================================================
    
    def _generate_ref_offre(self):
        """Génère la référence offre basée sur les BU sélectionnées."""
        if not self.x_bu_ids:
            return
        
        date_str = fields.Date.context_today(self).strftime('%d%m%Y')
        
        # Trouver le dernier numéro utilisé
        last_num = 0
        all_leads = self.env['crm.lead'].search([('x_ref_offre', '!=', False), ('id', '!=', self.id if self.id else 0)])
        for lead in all_leads:
            if lead.x_ref_offre:
                for ref in lead.x_ref_offre.split(','):
                    ref = ref.strip()
                    try:
                        num = int(ref.split('-')[-1])
                        if num > last_num:
                            last_num = num
                    except (ValueError, IndexError):
                        continue
        
        new_num = last_num + 1
        
        ref_offres = []
        for bu in self.x_bu_ids:
            bu_prefix = bu.name[:3].upper() if bu.name else 'XXX'
            ref_offres.append(f"{bu_prefix}-{date_str}-{new_num}")
        
        self.x_ref_offre = ', '.join(ref_offres)

    def _ccdoc_create_wbs(self, project):
        """Crée la structure WBS (Work Breakdown Structure) du projet."""
        task_names = ['Analyse', 'Réalisation', 'Recette', 'Livraison']
        for task_name in task_names:
            self.env['project.task'].create({
                'name': task_name,
                'project_id': project.id,
            })

    def _ccdoc_create_sale_order(self):
        """Crée une commande de vente liée à l'opportunité."""
        product = self.env['product.product'].search([], limit=1)
        
        for lead in self:
            if not lead.partner_id:
                continue
            
            existing = self.env['sale.order'].search([
                ('opportunity_id', '=', lead.id)
            ], limit=1)
            
            if not existing:
                so = self.env['sale.order'].create({
                    'partner_id': lead.partner_id.id,
                    'opportunity_id': lead.id,
                    'origin': lead.x_ref_offre or lead.name,
                    'client_order_ref': lead.x_ref_offre,
                })
                self.env['sale.order.line'].create({
                    'order_id': so.id,
                    'product_id': product.id if product else False,
                    'name': lead.name,
                    'product_uom_qty': 1,
                    'price_unit': lead.x_forecast or 0.0,
                })

    def _ccdoc_create_sale_order_bu(self, bu, ref_offre_bu):
        """Crée une commande de vente liée à l'opportunité et à une BU."""
        product = self.env['product.product'].search([], limit=1)

        for lead in self:
            if not lead.partner_id:
                continue

            existing = self.env['sale.order'].search([
                ('opportunity_id', '=', lead.id),
                ('client_order_ref', '=', ref_offre_bu)
            ], limit=1)

            if not existing:
                so = self.env['sale.order'].create({
                    'partner_id': lead.partner_id.id,
                    'opportunity_id': lead.id,
                    'origin': ref_offre_bu,
                    'client_order_ref': ref_offre_bu,
                    'name': f"{lead.name} [{bu.name}]"
                })
                self.env['sale.order.line'].create({
                    'order_id': so.id,
                    'product_id': product.id if product else False,
                    'name': f"{lead.name} [{bu.name}]",
                    'price_unit': lead.x_forecast or 0.0,
                })

    # =====================================================================
    # NOTIFICATIONS D'ÉCHÉANCE
    # =====================================================================

    @api.model
    def _cron_check_validation_deadlines(self):
        """Vérifie les échéances de validation et envoie des notifications."""
        today = fields.Date.context_today(self)

        # Chercher les opportunités avec échéances DC arrivant aujourd'hui ou dépassées
        leads_dc = self.search([
            ('x_deadline_validation_dc', '<=', today),
            ('x_date_validation_dc', '=', False),  # Pas encore validé
            ('active', '=', True),
        ])

        for lead in leads_dc:
            lead._send_validation_reminder('DC', lead.x_deadline_validation_dc)

        # Chercher les opportunités avec échéances DT arrivant aujourd'hui ou dépassées
        leads_dt = self.search([
            ('x_deadline_validation_dt', '<=', today),
            ('x_date_validation_dt', '=', False),  # Pas encore validé
            ('active', '=', True),
        ])

        for lead in leads_dt:
            lead._send_validation_reminder('DT', lead.x_deadline_validation_dt)

    def _send_validation_reminder(self, validation_type, deadline):
        """Envoie un rappel de validation aux responsables."""
        self.ensure_one()
        today = fields.Date.context_today(self)

        # Calculer si c'est en retard
        days_overdue = (today - deadline).days if deadline < today else 0
        is_overdue = days_overdue > 0

        # Préparer le message
        if is_overdue:
            status_msg = f"⚠️ EN RETARD de {days_overdue} jour(s)"
            status_color = "#dc3545"
        else:
            status_msg = "📅 ÉCHÉANCE AUJOURD'HUI"
            status_color = "#ffc107"

        body = Markup('''
        <div style="background: linear-gradient(135deg, {color} 0%%, #764ba2 100%%);
                    padding: 15px; border-radius: 10px; color: white; margin-bottom: 15px;">
            <h3 style="margin: 0; color: white;">⏰ Rappel de Validation {type}</h3>
        </div>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px;
                    border-left: 4px solid {color};">
            <p><strong>Statut:</strong> <span style="color: {color}; font-weight: bold;">{status}</span></p>
            <p><strong>📋 Opportunité:</strong> {name}</p>
            <p><strong>🏢 Client:</strong> {partner}</p>
            <p><strong>📅 Échéance:</strong> {deadline}</p>
            <p><strong>📝 Référence:</strong> {ref}</p>
            <p style="margin-top: 15px; padding: 10px; background-color: #fff3cd; border-radius: 5px;">
                💡 <strong>Action requise:</strong> Veuillez valider cette opportunité au plus vite.
            </p>
        </div>
        ''').format(
            type=validation_type,
            color=status_color,
            status=status_msg,
            name=self.name,
            partner=self.partner_id.name if self.partner_id else 'Non défini',
            deadline=deadline.strftime('%d/%m/%Y'),
            ref=self.x_ref_offre or 'Non définie'
        )

        # Déterminer les destinataires (responsables + user_id par défaut)
        partner_ids = []
        if self.x_responsable:
            partner_ids.extend(self.x_responsable.mapped('partner_id').ids)
        if self.user_id and self.user_id.partner_id:
            partner_ids.append(self.user_id.partner_id.id)

        # Supprimer les doublons
        partner_ids = list(set(partner_ids))

        if partner_ids:
            self.message_post(
                body=body,
                subject=f"⏰ Rappel Validation {validation_type} - {self.name}",
                partner_ids=partner_ids,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
            )