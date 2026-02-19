# -*- coding: utf-8 -*-
"""
Sécurisation des modèles comptables
Correctif pentest : accès non autorisé aux écritures, journaux et plan comptable via RPC.

Seuls les membres du groupe Comptabilité et les admins peuvent accéder à ces données.
"""
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class AccountMoveSecurity(models.Model):
    _inherit = 'account.move'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kw):
        if not self.env.user.has_group('base.group_system') and \
           not self.env.user.has_group('account.group_account_invoice'):
            _logger.warning(
                "SECURITY: accès bloqué à account.move pour uid=%s (%s)",
                self.env.user.id, self.env.user.login
            )
            return []
        return super().search_read(domain, fields, offset=offset, limit=limit, order=order, **kw)


class AccountAccountSecurity(models.Model):
    _inherit = 'account.account'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kw):
        if not self.env.user.has_group('base.group_system') and \
           not self.env.user.has_group('account.group_account_invoice'):
            _logger.warning(
                "SECURITY: accès bloqué à account.account pour uid=%s (%s)",
                self.env.user.id, self.env.user.login
            )
            return []
        return super().search_read(domain, fields, offset=offset, limit=limit, order=order, **kw)


class AccountJournalSecurity(models.Model):
    _inherit = 'account.journal'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kw):
        if not self.env.user.has_group('base.group_system') and \
           not self.env.user.has_group('account.group_account_invoice'):
            _logger.warning(
                "SECURITY: accès bloqué à account.journal pour uid=%s (%s)",
                self.env.user.id, self.env.user.login
            )
            return []
        return super().search_read(domain, fields, offset=offset, limit=limit, order=order, **kw)
