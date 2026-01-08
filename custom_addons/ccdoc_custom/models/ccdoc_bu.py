from odoo import models, fields

class CCDOCBU(models.Model):
    _name = 'ccdoc.bu'
    _description = 'Business Unit CCDOC'

    name = fields.Char(string='Nom BU', required=True)