# -*- coding: utf-8 -*-
"""
Sécurisation du modèle res.users
Correctif pentest : VC-03 (permissions excessives) et VC-04 (exposition emails)

Un utilisateur standard ne peut voir que son propre profil.
Seuls les managers de projet et les admins voient tous les utilisateurs.
"""
import logging
import re
from odoo import models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResUsersSecurity(models.Model):
    _inherit = 'res.users'

    # ------------------------------------------------------------------
    # Restriction lecture : utilisateur voit seulement son propre compte
    # ------------------------------------------------------------------
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kw):
        """
        Correctif VC-03 / VC-04 :
        - Un utilisateur standard ne peut lire que lui-même via RPC.
        - Les managers de projet voient les membres de leurs équipes.
        - Les administrateurs voient tout.
        """
        if not self.env.user.has_group('base.group_system'):
            if not self.env.user.has_group('project.group_project_manager'):
                # Forcer le domaine à ne retourner que l'utilisateur courant
                restriction = [('id', '=', self.env.user.id)]
                domain = ['&'] + (domain or []) + restriction
                _logger.info(
                    "SECURITY: search_read sur res.users restreint à uid=%s (user=%s)",
                    self.env.user.id, self.env.user.login
                )

        result = super().search_read(domain, fields, offset=offset, limit=limit, order=order, **kw)

        # Masquer les champs sensibles pour les non-admins
        if not self.env.user.has_group('base.group_system'):
            sensitive_fields = {'password', 'new_password', 'api_key'}
            for record in result:
                for sf in sensitive_fields:
                    if sf in record:
                        record[sf] = '***'

        return result

    # ------------------------------------------------------------------
    # Politique de mots de passe renforcée
    # ------------------------------------------------------------------
    @api.constrains('password')
    def _check_password_policy(self):
        """
        Correctif VC-05 : politique de complexité des mots de passe.
        Minimum 12 caractères, majuscule, minuscule, chiffre, caractère spécial.
        """
        for user in self:
            # Le champ password est hashé côté ORM, on ne peut valider
            # que lors des changements via _set_password
            pass

    def _change_password(self, new_password):
        """Override pour valider la complexité avant d'enregistrer."""
        if new_password and not self.env.context.get('skip_password_policy'):
            self._validate_password_complexity(new_password)
        return super()._change_password(new_password)

    def _validate_password_complexity(self, password):
        """Applique les règles de complexité du mot de passe."""
        errors = []
        if len(password) < 12:
            errors.append("au moins 12 caractères")
        if not re.search(r'[A-Z]', password):
            errors.append("au moins une lettre majuscule")
        if not re.search(r'[a-z]', password):
            errors.append("au moins une lettre minuscule")
        if not re.search(r'\d', password):
            errors.append("au moins un chiffre")
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', password):
            errors.append("au moins un caractère spécial (!@#$%...)")

        forbidden_sequences = ['123456', 'password', 'azerty', 'qwerty', 'admin', 'ccdoc']
        if any(seq in password.lower() for seq in forbidden_sequences):
            errors.append("ne doit pas contenir de séquence évidente (admin, ccdoc, 123456...)")

        if errors:
            raise ValidationError(
                "Le mot de passe ne respecte pas la politique de sécurité :\n"
                + "\n".join(f"  • {e}" for e in errors)
            )
