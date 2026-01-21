import logging
from markupsafe import Markup
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_justification_win = fields.Text(string="Justification gain")
    x_signed_po_attachment_id = fields.Many2one('ir.attachment', string="Bon de commande signé", readonly=True)
    
    # Champs pour la notification d'envoi
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
        help="Cochez cette case pour notifier les contacts sélectionnés que le dossier a été envoyé au client."
    )

    @api.onchange('x_envoi_notifie')
    def _onchange_envoi_notifie(self):
        """Avertissement si on coche sans avoir sélectionné de contacts."""
        if self.x_envoi_notifie and not self.x_contacts_a_notifier:
            return {
                'warning': {
                    'title': '⚠️ Aucun contact sélectionné',
                    'message': "Veuillez sélectionner des contacts à notifier avant de cocher cette case.",
                }
            }

    def write(self, vals):
        # Si on coche "Envoi notifié", envoyer la notification
        if vals.get('x_envoi_notifie') and not self.x_envoi_notifie:
            for lead in self:
                contacts = vals.get('x_contacts_a_notifier') and self.browse(vals.get('x_contacts_a_notifier')[0][2]) or lead.x_contacts_a_notifier
                if lead.x_contacts_a_notifier:
                    contacts = lead.x_contacts_a_notifier
                if contacts:
                    # Poster un message dans le chatter avec notification aux contacts
                    partner_ids = contacts.ids if hasattr(contacts, 'ids') else contacts
                    contact_names = ', '.join(contacts.mapped('name'))
                    body = Markup('''
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%%); padding: 15px; border-radius: 10px; color: white; margin-bottom: 15px;">
                        <h3 style="margin: 0; color: white;">📤 Dossier envoyé au client</h3>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea;">
                        <table style="width: 100%%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #666; width: 130px;"><strong>📋 Référence</strong></td>
                                <td style="padding: 8px 0; color: #333;">%s</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>🏢 Client</strong></td>
                                <td style="padding: 8px 0; color: #333;">%s</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>📅 Date d'envoi</strong></td>
                                <td style="padding: 8px 0; color: #333;">%s</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #666;"><strong>👥 Notifiés</strong></td>
                                <td style="padding: 8px 0; color: #333;">%s</td>
                            </tr>
                        </table>
                    </div>
                    ''') % (
                        lead.x_ref_offre or lead.name,
                        lead.partner_id.name if lead.partner_id else 'Non défini',
                        fields.Date.context_today(self).strftime('%d/%m/%Y'),
                        contact_names
                    )
                    lead.message_post(
                        body=body,
                        subject="📤 Dossier envoyé au client",
                        partner_ids=partner_ids,
                        message_type='notification',
                        subtype_xmlid='mail.mt_comment',
                    )
        
        result = super().write(vals)
        return result

    @api.constrains('stage_id')
    def _check_won_justification(self):
        """Contrainte : empêche le passage en Gagné sans justification et document."""
        for lead in self:
            if lead.stage_id and lead.stage_id.is_won:
                if not lead.x_justification_win and not lead.x_signed_po_attachment_id:
                    raise ValidationError(
                        "⚠️ Justification requise !\n\n"
                        "Avant de marquer cette opportunité comme gagnée, vous devez :\n"
                        "1. Cliquer sur le bouton 'Justificatif de gain'\n"
                        "2. Renseigner la justification du gain\n"
                        "3. Uploader le bon de commande signé\n\n"
                        "Cette étape est obligatoire pour valider le passage en 'Gagné'."
                    )
                elif not lead.x_justification_win:
                    raise ValidationError(
                        "⚠️ Justification manquante !\n\n"
                        "Veuillez renseigner la justification du gain via le bouton 'Justificatif de gain'."
                    )
                elif not lead.x_signed_po_attachment_id:
                    raise ValidationError(
                        "⚠️ Document manquant !\n\n"
                        "Veuillez uploader le bon de commande signé via le bouton 'Justificatif de gain'."
                    )

    @api.onchange('stage_id')
    def _onchange_stage_id_check_won(self):
        """Avertissement lors du changement d'étape vers Gagné sans justification."""
        if self.stage_id and self.stage_id.is_won:
            if not self.x_justification_win or not self.x_signed_po_attachment_id:
                # Revenir à l'étape précédente
                if self._origin and self._origin.stage_id:
                    self.stage_id = self._origin.stage_id
                return {
                    'warning': {
                        'title': '⚠️ Justification requise',
                        'message': "Vous devez d'abord cliquer sur le bouton 'Justificatif de gain' pour justifier et uploader le bon de commande signé avant de passer en 'Gagné'.",
                    }
                }

    def action_set_won(self):
        for lead in self:
            if not lead.x_justification_win and not lead.x_signed_po_attachment_id:
                raise UserError(
                    "⚠️ Justification requise !\n\n"
                    "Avant de marquer cette opportunité comme gagnée, vous devez :\n"
                    "1. Cliquer sur le bouton 'Justificatif de gain'\n"
                    "2. Renseigner la justification du gain\n"
                    "3. Uploader le bon de commande signé\n\n"
                    "Cette étape est obligatoire pour valider le passage en 'Gagné'."
                )
            elif not lead.x_justification_win:
                raise UserError(
                    "⚠️ Justification manquante !\n\n"
                    "Veuillez renseigner la justification du gain via le bouton 'Justificatif de gain'."
                )
            elif not lead.x_signed_po_attachment_id:
                raise UserError(
                    "⚠️ Document manquant !\n\n"
                    "Veuillez uploader le bon de commande signé via le bouton 'Justificatif de gain'."
                )
        return super(CrmLead, self).action_set_won()

    def action_open_purchase(self):
        # Redirige vers la vue de création d'un bon de commande fournisseur
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
        # Redirige vers la vue de création d'un devis client
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
        # Ouvre le wizard de justification
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.justify.win.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attachment_id': False, 'active_id': self.id},
        }

    def action_create_project_and_sale(self):
        # Appelée après justification, déclenche la création projet/vente
        # (reprend la logique existante du passage en gagné)
        bu_list = self.x_bu_ids or []
        if not bu_list:
            bu_list = [self.env['ccdoc.bu'].search([], limit=1)]
        ref_offres = [ref.strip() for ref in (self.x_ref_offre or '').split(',')]
        for idx, bu in enumerate(bu_list):
            ref_offre_bu = ref_offres[idx] if idx < len(ref_offres) else f"{self.x_ref_offre or ''}-{bu.name}"
            project_exists = self.env['project.project'].search([
                ('x_ref_offre', '=', ref_offre_bu)
            ])
            if not project_exists:
                project = self.env['project.project'].create({
                    'name': f"{self.name} [{bu.name}]",
                    'partner_id': self.partner_id.id,
                    'x_ref_offre': ref_offre_bu,
                    'x_bu_ids': [(6, 0, [bu.id])],
                    'x_statut': self.x_statut,
                    'x_responsable': self.x_responsable.id,
                    'x_deadline': self.x_deadline,
                    'x_priorite': self.x_priorite,
                    'x_avancement': self.x_avancement,
                    'x_date_demande': self.x_date_demande,
                    'x_forecast': str(self.x_forecast),
                    'x_blocage': self.x_blocage,
                    'x_etape_suivante': self.x_etape_suivante,
                })
                self._ccdoc_create_wbs(project)
            self._ccdoc_create_sale_order_bu(bu, ref_offre_bu)

    def _generate_ref_offre(self):
        bu_objs = self.x_bu_ids
        date_str = fields.Date.context_today(self).strftime('%d%m%Y')
        last_lead = self.env['crm.lead'].search([], order='id desc', limit=1)
        last_num = 1
        if last_lead and last_lead.x_ref_offre:
            try:
                last_num = int(last_lead.x_ref_offre.split('-')[-1]) + 1
            except Exception:
                last_num = last_lead.id + 1
        ref_offres = []
        for bu in bu_objs:
            ref_offres.append(f"{bu.name[:3].upper()}-{date_str}-{last_num}")
        self.x_ref_offre = ', '.join(ref_offres) if ref_offres else ''

    @api.onchange('x_bu_ids')
    def _onchange_bu_ids(self):
        self._generate_ref_offre()

    def create(self, vals):
        # Génération automatique de la REF Offre pour chaque BU sélectionnée
        bu_ids = vals.get('x_bu_ids', [(6, 0, [])])
        bu_list = []
        if bu_ids and isinstance(bu_ids, list) and bu_ids[0][0] == 6:
            bu_list = bu_ids[0][2]
        bu_objs = self.env['ccdoc.bu'].browse(bu_list)
        date_str = fields.Date.context_today(self).strftime('%d%m%Y')
        last_lead = self.env['crm.lead'].search([], order='id desc', limit=1)
        last_num = 1
        if last_lead and last_lead.x_ref_offre:
            try:
                last_num = int(last_lead.x_ref_offre.split('-')[-1]) + 1
            except Exception:
                last_num = last_lead.id + 1
        ref_offres = []
        for bu in bu_objs:
            ref_offres.append(f"{bu.name[:3].upper()}-{date_str}-{last_num}")
        # Si plusieurs BU, on stocke toutes les refs séparées par une virgule
        vals['x_ref_offre'] = ', '.join(ref_offres) if ref_offres else ''
        return super().create(vals)

    x_ref_offre = fields.Char(string='REF Offre', size=50, tracking=True)
    x_bu_ids = fields.Many2many('ccdoc.bu', string='BU', tracking=True)
    x_blocage = fields.Text(string='Blocage', tracking=True)
    x_etape_suivante = fields.Text(string='Étape suivante', tracking=True)
    x_date_depot = fields.Date(string='Date Dépôt', tracking=True)
    x_date_validation_dc = fields.Date(string='Date Validation DC', tracking=True)
    x_date_validation_dt = fields.Date(string='Date Validation DT', tracking=True)
    x_date_commande = fields.Date(string='Date Commande', tracking=True)
    x_statut = fields.Char(string='Statut', tracking=True)
    x_forecast = fields.Float(string='Forecast', tracking=True)
    x_responsable = fields.Many2one('res.users', string='Responsable', tracking=True)
    x_deadline = fields.Date(string='Deadline', tracking=True)
    x_priorite = fields.Selection([
        ('faible', 'Faible'),
        ('moyenne', 'Moyenne'),
        ('elevee', 'Élevée')
    ], string='Priorité', tracking=True)
    x_avancement = fields.Integer(string='Avancement (%)', tracking=True)
    x_date_demande = fields.Date(string='Date de demande', tracking=True)
    project_id = fields.Many2one('project.project', string='Projet lié', tracking=True)

    def _ccdoc_create_wbs(self, project):
        """Crée une structure WBS et des jalons contractuels sur le projet donné."""
        task_model = self.env['project.task']
        
        wbs = [
            {'name': 'Analyse'},
            {'name': 'Réalisation'},
            {'name': 'Recette'},
            {'name': 'Livraison'},
        ]
        for task in wbs:
            task_model.create({
                'name': task['name'],
                'project_id': project.id,
            })

    def _ccdoc_create_sale_order(self):
        """Crée une commande de vente liée à l'opportunité."""
        sale_order_model = self.env['sale.order']
        sale_order_line_model = self.env['sale.order.line']
        product = self.env['product.product'].search([], limit=1)
        for lead in self:
            if lead.partner_id and not sale_order_model.search([('opportunity_id', '=', lead.id)]):
                so = sale_order_model.create({
                    'partner_id': lead.partner_id.id,
                    'opportunity_id': lead.id,
                    'origin': lead.x_ref_offre or lead.name,
                    'client_order_ref': lead.x_ref_offre,
                })
                sale_order_line_model.create({
                    'order_id': so.id,
                    'product_id': product.id if product else False,
                    'name': lead.name,
                    'product_uom_qty': 1,
                    'price_unit': lead.x_forecast or 0.0,
                })

    def write(self, vals):
        stage_field = 'stage_id'
        today = fields.Date.context_today(self)
        
        # Intercepter le changement d'étape
        if stage_field in vals:
            stage = self.env['crm.stage'].browse(vals[stage_field])
            stage_name = stage.name.lower() if stage else ''
            
            # Remplir automatiquement la date Validation DC
            if 'validation dc' in stage_name:
                vals['x_date_validation_dc'] = today
            
            # Remplir automatiquement la date Validation DT
            if 'validation dt' in stage_name:
                vals['x_date_validation_dt'] = today
            
            # Remplir automatiquement la date Commande lors du passage en Gagné
            if stage and getattr(stage, 'is_won', False):
                vals['x_date_commande'] = today
                for lead in self:
                    # Si pas de justification ni pièce jointe, bloquer avec message d'erreur
                    if not lead.x_justification_win and not lead.x_signed_po_attachment_id:
                        raise UserError(
                            "⚠️ Justification requise !\n\n"
                            "Avant de marquer cette opportunité comme gagnée, vous devez :\n"
                            "1. Cliquer sur le bouton 'Justificatif de gain'\n"
                            "2. Renseigner la justification du gain\n"
                            "3. Uploader le bon de commande signé\n\n"
                            "Cette étape est obligatoire pour valider le passage en 'Gagné'."
                        )
                    elif not lead.x_justification_win:
                        raise UserError(
                            "⚠️ Justification manquante !\n\n"
                            "Veuillez renseigner la justification du gain via le bouton 'Justificatif de gain'."
                        )
                    elif not lead.x_signed_po_attachment_id:
                        raise UserError(
                            "⚠️ Document manquant !\n\n"
                            "Veuillez uploader le bon de commande signé via le bouton 'Justificatif de gain'."
                        )
                    # La création projet/vente se fait via action_create_project_and_sale
                    lead.action_create_project_and_sale()
        return super().write(vals)
    
    @api.constrains('x_date_depot', 'x_date_validation_dc', 'x_date_validation_dt', 'x_date_commande')
    def _check_dates_after_create_date(self):
        """Vérifie que les dates sont postérieures à la date de création de l'opportunité."""
        for lead in self:
            create_date = lead.create_date.date() if lead.create_date else False
            if not create_date:
                continue
            
            if lead.x_date_depot and lead.x_date_depot < create_date:
                raise ValidationError(
                    f"⚠️ La date de dépôt ({lead.x_date_depot}) doit être postérieure "
                    f"à la date de création de l'opportunité ({create_date})."
                )
            if lead.x_date_validation_dc and lead.x_date_validation_dc < create_date:
                raise ValidationError(
                    f"⚠️ La date de validation DC ({lead.x_date_validation_dc}) doit être postérieure "
                    f"à la date de création de l'opportunité ({create_date})."
                )
            if lead.x_date_validation_dt and lead.x_date_validation_dt < create_date:
                raise ValidationError(
                    f"⚠️ La date de validation DT ({lead.x_date_validation_dt}) doit être postérieure "
                    f"à la date de création de l'opportunité ({create_date})."
                )
            if lead.x_date_commande and lead.x_date_commande < create_date:
                raise ValidationError(
                    f"⚠️ La date de commande ({lead.x_date_commande}) doit être postérieure "
                    f"à la date de création de l'opportunité ({create_date})."
                )

    def _ccdoc_create_sale_order_bu(self, bu, ref_offre_bu):
        """Crée une commande de vente liée à l'opportunité et à la BU."""
        sale_order_model = self.env['sale.order']
        sale_order_line_model = self.env['sale.order.line']
        product = self.env['product.product'].search([], limit=1)
        for lead in self:
            if lead.partner_id and not sale_order_model.search([('opportunity_id', '=', lead.id), ('client_order_ref', '=', ref_offre_bu)]):
                so = sale_order_model.create({
                    'partner_id': lead.partner_id.id,
                    'opportunity_id': lead.id,
                    'origin': ref_offre_bu,
                    'client_order_ref': ref_offre_bu,
                    'name': f"{lead.name} [{bu.name}]"
                })
                sale_order_line_model.create({
                    'order_id': so.id,
                    'product_id': product.id,
                    'name': f"{lead.name} [{bu.name}]",
                    'price_unit': lead.x_forecast or 0.0,
                })
