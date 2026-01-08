from odoo import models, fields, api



class CrmLead(models.Model):
    _inherit = 'crm.lead'

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

    x_ref_offre = fields.Char(string='REF Offre', size=50)
    x_bu_ids = fields.Many2many('ccdoc.bu', string='BU')
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
                    bu_list = lead.x_bu_ids or []
                    if not bu_list:
                        bu_list = [self.env['ccdoc.bu'].search([], limit=1)]  # fallback: 1er BU si aucun
                    for bu in bu_list:
                        ref_offre_bu = f"{lead.x_ref_offre or ''}-{bu.name}"
                        project_exists = self.env['project.project'].search([
                            ('x_ref_offre', '=', ref_offre_bu)
                        ])
                        if not project_exists:
                            project = self.env['project.project'].create({
                                'name': f"{lead.name} [{bu.name}]",
                                'partner_id': lead.partner_id.id,
                                'x_ref_offre': ref_offre_bu,
                                'x_bu_ids': [(6, 0, [bu.id])],
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
                            _logger.info(f"[CCDOC] Projet créé pour lead {lead.name} (ref: {ref_offre_bu})")
                            lead._ccdoc_create_wbs(project)
                        else:
                            _logger.info(f"[CCDOC] Projet déjà existant pour ref_offre {ref_offre_bu}")
                        # Création de la commande de vente pour chaque BU
                        lead._ccdoc_create_sale_order_bu(bu, ref_offre_bu)
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
