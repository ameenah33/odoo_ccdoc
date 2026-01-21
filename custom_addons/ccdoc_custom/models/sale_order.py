from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_open_import_wizard(self):
        """Ouvre le wizard d'import de lignes de devis."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Importer des lignes',
            'res_model': 'sale.order.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            },
        }
