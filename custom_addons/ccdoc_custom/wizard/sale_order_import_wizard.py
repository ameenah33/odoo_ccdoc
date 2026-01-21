import base64
import io
from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlrd
except ImportError:
    xlrd = None

import csv


class SaleOrderImportWizard(models.TransientModel):
    """Wizard pour importer des lignes de devis depuis un fichier Excel/CSV."""
    _name = 'sale.order.import.wizard'
    _description = 'Import de lignes de devis'

    sale_order_id = fields.Many2one('sale.order', string="Devis", required=True)
    partner_id = fields.Many2one('res.partner', related='sale_order_id.partner_id', string="Client")
    
    # Fichier
    file = fields.Binary(string="Fichier Excel/CSV", required=True)
    filename = fields.Char(string="Nom du fichier")
    
    # État du wizard
    state = fields.Selection([
        ('upload', 'Upload'),
        ('mapping', 'Mapping'),
        ('preview', 'Aperçu'),
    ], default='upload', string="État")
    
    # Mapping des colonnes
    mapping_template_id = fields.Many2one('import.mapping.template', string="Template existant")
    
    # Colonnes détectées
    detected_columns = fields.Text(string="Colonnes détectées")
    preview_data = fields.Text(string="Aperçu des données")
    
    # Mapping manuel
    col_reference = fields.Selection(selection='_get_column_selection', string="Colonne Référence")
    col_description = fields.Selection(selection='_get_column_selection', string="Colonne Description")
    col_quantity = fields.Selection(selection='_get_column_selection', string="Colonne Quantité")
    col_price = fields.Selection(selection='_get_column_selection', string="Colonne Prix unitaire")
    col_discount = fields.Selection(selection='_get_column_selection', string="Colonne Remise (%)")
    
    # Options
    skip_header = fields.Boolean(string="Ignorer la première ligne (en-tête)", default=True)
    create_product_if_not_found = fields.Boolean(
        string="Créer le produit si non trouvé", 
        default=True,
    )
    save_template = fields.Boolean(string="Sauvegarder ce mapping pour ce client", default=True)
    
    # Résultat
    import_result = fields.Text(string="Résultat de l'import")

    @api.model
    def _get_column_selection(self):
        """Retourne la liste des colonnes disponibles."""
        return [('-1', '-- Non mappé --')]

    def _read_file(self):
        """Lit le fichier et retourne les données sous forme de liste de listes."""
        if not self.file:
            raise UserError(_("Veuillez uploader un fichier."))
        
        file_content = base64.b64decode(self.file)
        filename = self.filename.lower() if self.filename else ''
        
        data = []
        headers = []
        
        if filename.endswith('.xlsx'):
            if not openpyxl:
                raise UserError(_("La bibliothèque 'openpyxl' n'est pas installée. Contactez l'administrateur."))
            workbook = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True)
            sheet = workbook.active
            for row in sheet.iter_rows(values_only=True):
                data.append([str(cell) if cell is not None else '' for cell in row])
            workbook.close()
            
        elif filename.endswith('.xls'):
            if not xlrd:
                raise UserError(_("La bibliothèque 'xlrd' n'est pas installée. Contactez l'administrateur."))
            workbook = xlrd.open_workbook(file_contents=file_content)
            sheet = workbook.sheet_by_index(0)
            for row_idx in range(sheet.nrows):
                data.append([str(cell.value) if cell.value else '' for cell in sheet.row(row_idx)])
                
        elif filename.endswith('.csv'):
            # Essayer différents encodages
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    content = file_content.decode(encoding)
                    # Détecter le délimiteur
                    dialect = csv.Sniffer().sniff(content[:1024], delimiters=',;\t|')
                    reader = csv.reader(io.StringIO(content), dialect)
                    data = [row for row in reader]
                    break
                except:
                    continue
            if not data:
                raise UserError(_("Impossible de lire le fichier CSV. Vérifiez l'encodage."))
        else:
            raise UserError(_("Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv"))
        
        if data:
            headers = data[0]
        
        return headers, data

    def action_analyze_file(self):
        """Analyse le fichier et passe à l'étape de mapping."""
        self.ensure_one()
        
        headers, data = self._read_file()
        
        if not data:
            raise UserError(_("Le fichier est vide."))
        
        # Stocker les colonnes détectées
        columns_info = []
        for idx, header in enumerate(headers):
            columns_info.append(f"{idx}: {header}")
        self.detected_columns = '\n'.join(columns_info)
        
        # Créer l'aperçu (5 premières lignes)
        preview_lines = []
        for i, row in enumerate(data[:6]):
            preview_lines.append(f"Ligne {i}: {' | '.join(row[:8])}")
        self.preview_data = '\n'.join(preview_lines)
        
        # Vérifier s'il existe un template pour ce client
        template = self.env['import.mapping.template'].search([
            ('partner_id', '=', self.partner_id.id)
        ], limit=1)
        
        if template:
            self.mapping_template_id = template.id
            self.col_reference = str(template.col_reference)
            self.col_description = str(template.col_description)
            self.col_quantity = str(template.col_quantity)
            self.col_price = str(template.col_price)
            self.col_discount = str(template.col_discount)
            self.skip_header = template.skip_header
            self.create_product_if_not_found = template.create_product_if_not_found
        
        self.state = 'mapping'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_import(self):
        """Importe les lignes dans le devis."""
        self.ensure_one()
        
        headers, data = self._read_file()
        
        # Indices des colonnes
        col_ref = int(self.col_reference) if self.col_reference and self.col_reference != '-1' else -1
        col_desc = int(self.col_description) if self.col_description and self.col_description != '-1' else -1
        col_qty = int(self.col_quantity) if self.col_quantity and self.col_quantity != '-1' else -1
        col_price = int(self.col_price) if self.col_price and self.col_price != '-1' else -1
        col_disc = int(self.col_discount) if self.col_discount and self.col_discount != '-1' else -1
        
        if col_desc == -1 and col_ref == -1:
            raise UserError(_("Vous devez au moins mapper la colonne Description ou Référence."))
        
        # Sauvegarder le template si demandé
        if self.save_template and self.partner_id:
            template = self.env['import.mapping.template'].search([
                ('partner_id', '=', self.partner_id.id)
            ], limit=1)
            
            template_vals = {
                'name': f"Template {self.partner_id.name}",
                'partner_id': self.partner_id.id,
                'col_reference': col_ref,
                'col_description': col_desc,
                'col_quantity': col_qty,
                'col_price': col_price,
                'col_discount': col_disc,
                'skip_header': self.skip_header,
                'create_product_if_not_found': self.create_product_if_not_found,
            }
            
            if template:
                template.write(template_vals)
            else:
                self.env['import.mapping.template'].create(template_vals)
        
        # Importer les lignes
        start_row = 1 if self.skip_header else 0
        lines_created = 0
        errors = []
        
        product_model = self.env['product.product']
        sol_model = self.env['sale.order.line']
        
        for row_idx, row in enumerate(data[start_row:], start=start_row + 1):
            try:
                # Récupérer les valeurs
                reference = row[col_ref].strip() if col_ref >= 0 and col_ref < len(row) else ''
                description = row[col_desc].strip() if col_desc >= 0 and col_desc < len(row) else ''
                
                # Quantité
                qty = 1.0
                if col_qty >= 0 and col_qty < len(row):
                    qty_str = row[col_qty].replace(',', '.').replace(' ', '')
                    try:
                        qty = float(qty_str) if qty_str else 1.0
                    except:
                        qty = 1.0
                
                # Prix
                price = 0.0
                if col_price >= 0 and col_price < len(row):
                    price_str = row[col_price].replace(',', '.').replace(' ', '').replace('€', '').replace('XOF', '').replace('CFA', '')
                    try:
                        price = float(price_str) if price_str else 0.0
                    except:
                        price = 0.0
                
                # Remise
                discount = 0.0
                if col_disc >= 0 and col_disc < len(row):
                    disc_str = row[col_disc].replace(',', '.').replace(' ', '').replace('%', '')
                    try:
                        discount = float(disc_str) if disc_str else 0.0
                    except:
                        discount = 0.0
                
                # Ignorer les lignes vides
                if not description and not reference:
                    continue
                
                # Chercher ou créer le produit
                product = None
                if reference:
                    product = product_model.search([
                        '|',
                        ('default_code', '=', reference),
                        ('name', 'ilike', reference)
                    ], limit=1)
                
                if not product and self.create_product_if_not_found:
                    product = product_model.create({
                        'name': description or reference,
                        'default_code': reference if reference else False,
                        'type': 'service',
                        'list_price': price,
                    })
                elif not product:
                    # Utiliser un produit générique ou ignorer
                    product = product_model.search([], limit=1)
                
                # Créer la ligne de commande
                sol_model.create({
                    'order_id': self.sale_order_id.id,
                    'product_id': product.id if product else False,
                    'name': description or reference,
                    'product_uom_qty': qty,
                    'price_unit': price,
                    'discount': discount,
                })
                lines_created += 1
                
            except Exception as e:
                errors.append(f"Ligne {row_idx}: {str(e)}")
        
        # Résultat
        result_msg = f"✅ {lines_created} lignes importées avec succès."
        if errors:
            result_msg += f"\n\n⚠️ {len(errors)} erreurs:\n" + '\n'.join(errors[:10])
            if len(errors) > 10:
                result_msg += f"\n... et {len(errors) - 10} autres erreurs."
        
        # Fermer le wizard et afficher le message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import terminé',
                'message': result_msg,
                'sticky': True,
                'type': 'success' if not errors else 'warning',
            }
        }

    def action_back(self):
        """Retour à l'étape upload."""
        self.state = 'upload'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
