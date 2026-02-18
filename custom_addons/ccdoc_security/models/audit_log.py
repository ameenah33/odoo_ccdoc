# -*- coding: utf-8 -*-
"""
Journal d'audit des accès aux données sensibles.
Correctif pentest : recommandation de journalisation et détection d'anomalies.
"""
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Seuil d'alerte : nombre d'enregistrements retournés en une requête
SUSPICIOUS_RESULT_THRESHOLD = 30


class CcdocAuditLog(models.Model):
    _name = 'ccdoc.audit.log'
    _description = "Journal d'audit sécurité CCDOC"
    _order = 'create_date desc'
    _rec_name = 'model_name'

    user_id = fields.Many2one('res.users', string='Utilisateur', required=True, ondelete='set null')
    model_name = fields.Char('Modèle accédé', required=True)
    action = fields.Selection([
        ('search', 'Recherche'),
        ('read', 'Lecture'),
        ('write', 'Modification'),
        ('create', 'Création'),
        ('unlink', 'Suppression'),
    ], string='Action', required=True)
    domain = fields.Text('Filtre utilisé')
    result_count = fields.Integer('Nombre de résultats')
    is_suspicious = fields.Boolean('Activité suspecte', default=False)
    alert_reason = fields.Char('Raison de l\'alerte')

    @api.model
    def log_access(self, model_name, action, domain=None, result_count=0):
        """
        Enregistre un accès et détecte les comportements suspects.
        Appelé par les modèles sensibles.
        """
        is_suspicious = False
        reasons = []

        # Détection : extraction massive de données
        if result_count > SUSPICIOUS_RESULT_THRESHOLD:
            is_suspicious = True
            reasons.append(f"extraction massive ({result_count} enregistrements)")

        # Détection : usage de wildcards suspects dans les domaines RPC
        domain_str = str(domain or '')
        suspicious_patterns = ["'%'", '"%"', "ilike", "!=", "(1, '=', 1)"]
        for pattern in suspicious_patterns:
            if pattern in domain_str:
                is_suspicious = True
                reasons.append(f"opérateur suspect: {pattern}")
                break

        if is_suspicious:
            alert_msg = f"Activité suspecte: user={self.env.user.login}, model={model_name}, " \
                        f"action={action}, results={result_count}, raisons=[{', '.join(reasons)}]"
            _logger.warning("SECURITY ALERT: %s", alert_msg)

        # Créer l'entrée de log (sudo pour éviter les problèmes de droits)
        try:
            self.sudo().create({
                'user_id': self.env.user.id,
                'model_name': model_name,
                'action': action,
                'domain': domain_str[:500] if domain_str else False,
                'result_count': result_count,
                'is_suspicious': is_suspicious,
                'alert_reason': ', '.join(reasons) if reasons else False,
            })
        except Exception as e:
            _logger.error("Impossible d'écrire dans le journal d'audit: %s", e)

    @api.model
    def _cron_clean_old_logs(self):
        """Purge les logs de plus de 90 jours (cron mensuel)."""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=90)
        old_logs = self.search([('create_date', '<', cutoff)])
        count = len(old_logs)
        old_logs.unlink()
        _logger.info("SECURITY: %d entrées de journal d'audit purgées (> 90 jours)", count)
