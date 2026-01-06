from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_ref_offre = fields.Char(string='REF Offre', size=50)
    x_bu = fields.Selection([
        ('physical', 'Physical'),
        ('cyber', 'Cyber'),
        ('audit', 'Audit')
    ], string='BU')
    x_blocage = fields.Text(string='Blocage')
    x_etape_suivante = fields.Text(string='Étape suivante')
    x_date_depot = fields.Date(string='Date Dépôt')
    x_date_validation_dc = fields.Date(string='Date Validation DC')
    x_date_validation_dt = fields.Date(string='Date Validation DT')
    x_date_commande = fields.Date(string='Date Commande')
    x_statut = fields.Char(string='Statut')
    x_forecast = fields.Float(string='Forecast')
    x_responsable = fields.Many2one('res.users', string='Responsable')
    x_deadline = fields.Date(string='Deadline')
    x_priorite = fields.Selection([
        ('faible', 'Faible'),
        ('moyenne', 'Moyenne'),
        ('elevee', 'Élevée')
    ], string='Priorité')
    x_avancement = fields.Integer(string='Avancement (%)')
    x_date_demande = fields.Date(string='Date de demande')
    project_id = fields.Many2one('project.project', string='Projet lié')

    def _ccdoc_create_wbs(self, project):
        """Crée une structure WBS et des jalons contractuels sur le projet donné."""
        task_model = self.env['project.task']
        # Exemple de structure WBS (modifiable)
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
        import logging
        _logger = logging.getLogger(__name__)
        res = super().write(vals)
        stage_field = 'stage_id'
        if stage_field in vals:
            stage = self.env['crm.stage'].browse(vals[stage_field])
            _logger.info(f"[CCDOC] Passage à l'étape : {stage.name} (is_won={getattr(stage, 'is_won', False)})")
            if stage and getattr(stage, 'is_won', False):
                for lead in self:
                    _logger.info(f"[CCDOC] Test création projet pour lead {lead.name} (ref: {lead.x_ref_offre})")
                    if not self.env['project.project'].search([('x_ref_offre', '=', lead.x_ref_offre)]):
                        project = self.env['project.project'].create({
                            'name': lead.name,
                            'partner_id': lead.partner_id.id,
                            'x_ref_offre': lead.x_ref_offre,
                            'x_bu': lead.x_bu,
                            'x_statut': lead.x_statut,
                            'x_responsable': lead.x_responsable.id,
                            'x_deadline': lead.x_deadline,
                            'x_priorite': lead.x_priorite,
                            'x_avancement': lead.x_avancement,
                            'x_date_demande': lead.x_date_demande,
                            'x_forecast': str(lead.x_forecast),
                            'x_blocage': lead.x_blocage,
                            'x_etape_suivante': lead.x_etape_suivante,
                        })
                        _logger.info(f"[CCDOC] Projet créé pour lead {lead.name} (ref: {lead.x_ref_offre})")
                        lead._ccdoc_create_wbs(project)
                    else:
                        _logger.info(f"[CCDOC] Projet déjà existant pour ref_offre {lead.x_ref_offre}")
                    # Création de la commande de vente
                    lead._ccdoc_create_sale_order()
        return res
