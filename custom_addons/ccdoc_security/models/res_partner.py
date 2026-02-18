# -*- coding: utf-8 -*-
"""
Sécurisation du modèle res.partner
Correctif pentest : VC-02 (injection domaines) et VC-03 (permissions excessives)

Les partenaires marqués comme sensibles (ministères, banques, etc.)
ne sont visibles que par les managers et administrateurs.
"""
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Mots-clés qui déclenchent la classification automatique comme partenaire sensible
SENSITIVE_KEYWORDS = [
    'ministère', 'ministry', 'justice', 'bceao', 'banque', 'bank',
    'aibd', 'aéroport', 'airport', 'dtai', 'direction générale',
    'palais', 'présidence', 'dgctp', 'dirtrans', 'tresor', 'trésor',
    'dgid', 'douanes', 'gendarmerie', 'police', 'armée'
]


class ResPartnerSecurity(models.Model):
    _inherit = 'res.partner'

    is_sensitive = fields.Boolean(
        string='Client Sensible',
        default=False,
        help='Cocher pour les clients confidentiels (ministères, banques, infrastructures critiques). '
             'Ces partenaires ne sont visibles que par les managers et administrateurs.'
    )
    sensitivity_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Interne'),
        ('confidential', 'Confidentiel'),
        ('secret', 'Confidentiel Défense'),
    ], string='Niveau de confidentialité', default='internal', required=True)

    # ------------------------------------------------------------------
    # Classification automatique à la création
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = (vals.get('name') or '').lower()
            if not vals.get('is_sensitive') and any(kw in name for kw in SENSITIVE_KEYWORDS):
                vals['is_sensitive'] = True
                vals['sensitivity_level'] = 'confidential'
                _logger.info(
                    "SECURITY: partenaire '%s' automatiquement classifié comme sensible",
                    vals.get('name')
                )
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Restriction lecture : masquer partenaires sensibles aux utilisateurs standard
    # ------------------------------------------------------------------
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kw):
        """
        Correctif VC-03 :
        Les partenaires sensibles ne sont visibles qu'aux managers et admins.
        """
        if not self.env.user.has_group('base.group_system') and \
           not self.env.user.has_group('project.group_project_manager') and \
           not self.env.user.has_group('sales_team.group_sale_manager'):
            restriction = [('is_sensitive', '=', False)]
            domain = ['&'] + (domain or []) + restriction

        return super().search_read(domain, fields, offset=offset, limit=limit, order=order, **kw)
