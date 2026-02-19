# -*- coding: utf-8 -*-
"""
Sécurisation des modèles très sensibles
Correctif pentest : exposition de res.groups (cartographie RBAC) et res.partner.bank
(données bancaires) via RPC sans restriction.

- res.groups       → admin uniquement
- res.partner.bank → admin uniquement
"""
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class ResGroupsSecurity(models.Model):
    _inherit = 'res.groups'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kw):
        if not self.env.user.has_group('base.group_system'):
            _logger.warning(
                "SECURITY: accès bloqué à res.groups pour uid=%s (%s)",
                self.env.user.id, self.env.user.login
            )
            return []
        return super().search_read(domain, fields, offset=offset, limit=limit, order=order, **kw)


class ResPartnerBankSecurity(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kw):
        if not self.env.user.has_group('base.group_system'):
            _logger.warning(
                "SECURITY: accès bloqué à res.partner.bank pour uid=%s (%s)",
                self.env.user.id, self.env.user.login
            )
            return []
        return super().search_read(domain, fields, offset=offset, limit=limit, order=order, **kw)
