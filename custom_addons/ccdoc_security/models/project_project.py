# -*- coding: utf-8 -*-
"""
Sécurisation du modèle project.project
Correctif pentest : VC-03 (permissions excessives)

Un utilisateur standard ne voit que les projets où il est membre ou responsable.
"""
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class ProjectProjectSecurity(models.Model):
    _inherit = 'project.project'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kw):
        """
        Correctif VC-03 :
        - Utilisateur standard : voit uniquement les projets où il est responsable ou membre d'équipe.
        - Manager de projet : voit tous les projets.
        - Admin : voit tout.
        """
        if not self.env.user.has_group('base.group_system') and \
           not self.env.user.has_group('project.group_project_manager'):

            uid = self.env.user.id
            restriction = ['|', '|',
                ('user_id', '=', uid),
                ('x_responsable', 'in', [uid]),
                ('x_equipe', 'in', [uid]),
            ]
            domain = restriction + (domain or [])
            _logger.info(
                "SECURITY: search_read projet restreint à uid=%s (%s)",
                uid, self.env.user.login
            )

        return super().search_read(domain, fields, offset=offset, limit=limit, order=order, **kw)
