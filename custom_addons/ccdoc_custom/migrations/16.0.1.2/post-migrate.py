import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

STAGE_XMLIDS = [
    'ccdoc_custom.task_stage_attente_validation_client',
    'ccdoc_custom.task_stage_a_faire',
    'ccdoc_custom.task_stage_en_cours',
    'ccdoc_custom.task_stage_bloque',
    'ccdoc_custom.task_stage_termine',
]


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    stages = env['project.task.type']
    for xmlid in STAGE_XMLIDS:
        stage = env.ref(xmlid, raise_if_not_found=False)
        if stage:
            stages |= stage

    if not stages:
        _logger.warning("Migration 17.0.1.2: aucune étape prédéfinie trouvée, abandon.")
        return

    projects = env['project.project'].search([])
    for project in projects:
        project.type_ids = [(4, s.id) for s in stages]

    _logger.info(
        "Migration 17.0.1.2: %d projets mis à jour avec les étapes prédéfinies.",
        len(projects),
    )
