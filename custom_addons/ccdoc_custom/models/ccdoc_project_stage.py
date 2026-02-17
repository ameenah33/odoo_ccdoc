from odoo import models, fields, api


class CcdocProjectStage(models.Model):
    _name = 'ccdoc.project.stage'
    _description = 'Étape de projet CCDOC'
    _order = 'sequence, id'

    name = fields.Char(string='Nom', required=True, translate=True)
    sequence = fields.Integer(string='Séquence', default=10)
    fold = fields.Boolean(
        string='Plié dans le Kanban',
        default=False,
        help="Si coché, cette étape sera repliée par défaut dans la vue Kanban.",
    )
    color = fields.Integer(string='Couleur', default=0)
    description = fields.Text(string='Description')
    is_blocking = fields.Boolean(
        string='Étape bloquante',
        default=False,
        help="Si coché, un motif de blocage sera requis pour les projets dans cette étape.",
    )
    is_closing = fields.Boolean(
        string='Étape de clôture',
        default=False,
        help="Si coché, cette étape indique que le projet est terminé.",
    )
    active = fields.Boolean(default=True)
    project_count = fields.Integer(
        compute='_compute_project_count',
        string='Nombre de projets',
    )

    def _compute_project_count(self):
        read_group_data = self.env['project.project'].read_group(
            [('x_stage_id', 'in', self.ids)],
            ['x_stage_id'],
            ['x_stage_id'],
        )
        stage_counts = {d['x_stage_id'][0]: d['x_stage_id_count'] for d in read_group_data}
        for stage in self:
            stage.project_count = stage_counts.get(stage.id, 0)
