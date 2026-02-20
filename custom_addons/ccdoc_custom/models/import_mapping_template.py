from odoo import models, fields, api


class ImportMappingTemplate(models.Model):
    """Template de mapping pour l'import de lignes de devis par client."""
    _name = 'import.mapping.template'
    _description = 'Template de mapping import devis'
    _rec_name = 'name'

    name = fields.Char(string="Nom du template", required=True)
    partner_id = fields.Many2one('res.partner', string="Client", required=True)
    
    
    col_reference = fields.Integer(string="Colonne Référence produit", default=-1)
    col_description = fields.Integer(string="Colonne Description", default=-1)
    col_quantity = fields.Integer(string="Colonne Quantité", default=-1)
    col_price = fields.Integer(string="Colonne Prix unitaire", default=-1)
    col_discount = fields.Integer(string="Colonne Remise (%)", default=-1)
    
    # Options
    skip_header = fields.Boolean(string="Ignorer la première ligne (en-tête)", default=True)
    create_product_if_not_found = fields.Boolean(
        string="Créer le produit si non trouvé", 
        default=True,
        help="Si activé, crée automatiquement le produit s'il n'existe pas dans la base."
    )
    
    _sql_constraints = [
        ('partner_unique', 'unique(partner_id)', 'Un seul template par client est autorisé.')
    ]
