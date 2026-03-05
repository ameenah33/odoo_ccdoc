from odoo import models, fields, api


class PlannerTaskStage(models.Model):
    _name = 'planner.task.stage'
    _description = 'Étape de tâche Planner'
    _order = 'sequence, id'

    name = fields.Char(string='Nom', required=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(string='Plié dans le Kanban', default=False)


class PlannerTask(models.Model):
    _name = 'planner.task'
    _description = 'Tâche de plan CCDOC'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom de la tâche', required=True, tracking=True)
    plan_id = fields.Many2one(
        'planner.plan',
        string='Plan',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    stage_id = fields.Many2one(
        'planner.task.stage',
        string='Étape',
        default=lambda self: self._default_stage(),
        group_expand='_read_group_stage_ids',
        tracking=True,
    )
    user_ids = fields.Many2many('res.users', string='Assigné à')
    description = fields.Html(string='Description')
    deadline = fields.Date(string='Échéance', tracking=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'Élevée')], default='0')
    sequence = fields.Integer(default=10)
    color = fields.Integer(string='Couleur')
    kanban_state = fields.Selection([
        ('normal', 'En cours'),
        ('done', 'Prêt'),
        ('blocked', 'Bloqué'),
    ], string='État Kanban', default='normal', tracking=True)

    def _default_stage(self):
        return self.env['planner.task.stage'].search([], order='sequence', limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.search([], order=order)
