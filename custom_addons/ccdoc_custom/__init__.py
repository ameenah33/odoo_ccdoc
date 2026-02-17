from . import models
from . import wizard


def _migrate_project_stages(env):
    """Migre les anciennes valeurs x_etat vers les nouvelles étapes dynamiques x_stage_id."""
    cr = env.cr

    # Vérifier si l'ancienne colonne x_etat existe encore dans la table
    cr.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'project_project' AND column_name = 'x_etat'"
    )
    if not cr.fetchone():
        return  # Rien à migrer

    # Mapping ancien x_etat → xml_id du nouveau stage
    mapping = {
        'attente_validation': 'ccdoc_custom.project_stage_attente_validation',
        'attente_paiement':   'ccdoc_custom.project_stage_attente_paiement',
        'en_cours':           'ccdoc_custom.project_stage_en_cours',
        'bloque':             'ccdoc_custom.project_stage_bloque',
        'en_recette':         'ccdoc_custom.project_stage_en_recette',
        'en_production':      'ccdoc_custom.project_stage_en_production',
        'termine':            'ccdoc_custom.project_stage_termine',
    }

    for old_val, xml_id in mapping.items():
        stage = env.ref(xml_id, raise_if_not_found=False)
        if stage:
            cr.execute(
                "UPDATE project_project SET x_stage_id = %s "
                "WHERE x_etat = %s AND (x_stage_id IS NULL)",
                (stage.id, old_val),
            )

    # Assigner la première étape aux projets sans étape
    default_stage = env.ref(
        'ccdoc_custom.project_stage_attente_validation', raise_if_not_found=False
    )
    if default_stage:
        cr.execute(
            "UPDATE project_project SET x_stage_id = %s WHERE x_stage_id IS NULL",
            (default_stage.id,),
        )
