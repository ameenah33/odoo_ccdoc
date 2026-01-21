from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CrmLeadJustifyWinWizard(models.TransientModel):
    _name = 'crm.lead.justify.win.wizard'
    _description = 'Justification de gain de l\'opportunité'


    justification = fields.Text(string="Justification", required=True)
    signed_po_file = fields.Binary(string="Bon de commande signé", required=True)
    signed_po_filename = fields.Char(string="Nom du fichier")

    def action_confirm(self):
        # On suppose que le contexte contient l'ID du lead
        lead_id = self.env.context.get('active_id')
        lead = self.env['crm.lead'].browse(lead_id)
        if not lead:
            raise UserError(_("Aucune opportunité trouvée."))
        # On stocke la justification sur le lead
        lead.x_justification_win = self.justification
        # On crée une pièce jointe sur le lead
        attachment = None
        if self.signed_po_file:
            attachment = self.env['ir.attachment'].create({
                'name': self.signed_po_filename or 'Bon de commande signé',
                'datas': self.signed_po_file,
                'res_model': 'crm.lead',
                'res_id': lead.id,
                'type': 'binary',
            })
            lead.x_signed_po_attachment_id = attachment.id
            # Poster un message dans le chatter pour la traçabilité avec la pièce jointe
            body = Markup('''
            <div style="background: linear-gradient(135deg, #11998e 0%%, #38ef7d 100%%); padding: 15px; border-radius: 10px; color: white; margin-bottom: 15px;">
                <h3 style="margin: 0; color: white;">🏆 Opportunité validée pour passage en Gagné</h3>
            </div>
            <div style="background-color: #f0fff4; padding: 15px; border-radius: 8px; border-left: 4px solid #38ef7d;">
                <p style="margin: 0 0 10px 0;"><strong>📝 Justification :</strong></p>
                <p style="margin: 0; color: #333; background-color: white; padding: 10px; border-radius: 5px;">%s</p>
            </div>
            <div style="margin-top: 15px; padding: 10px; background-color: #e8f5e9; border-radius: 8px;">
                <p style="margin: 0;">📎 <strong>Document joint :</strong> %s</p>
            </div>
            ''') % (self.justification, self.signed_po_filename or 'Bon de commande signé')
            lead.message_post(
                body=body,
                attachment_ids=[attachment.id],
                subject="🏆 Justificatif de gain uploadé"
            )
        else:
            # Poster un message même sans pièce jointe
            body = Markup('''
            <div style="background: linear-gradient(135deg, #11998e 0%%, #38ef7d 100%%); padding: 15px; border-radius: 10px; color: white; margin-bottom: 15px;">
                <h3 style="margin: 0; color: white;">🏆 Opportunité validée pour passage en Gagné</h3>
            </div>
            <div style="background-color: #f0fff4; padding: 15px; border-radius: 8px; border-left: 4px solid #38ef7d;">
                <p style="margin: 0 0 10px 0;"><strong>📝 Justification :</strong></p>
                <p style="margin: 0; color: #333; background-color: white; padding: 10px; border-radius: 5px;">%s</p>
            </div>
            ''') % self.justification
            lead.message_post(
                body=body,
                subject="🏆 Justificatif de gain uploadé"
            )
        # On déclenche la création du projet et de la vente
        lead.action_create_project_and_sale()
        return {'type': 'ir.actions.act_window_close'}
