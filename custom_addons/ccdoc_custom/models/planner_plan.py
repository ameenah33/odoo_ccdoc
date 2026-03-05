from odoo import models, fields, api


class PlannerPlanStage(models.Model):
    _name = 'planner.plan.stage'
    _description = 'Étape de plan Planner'
    _order = 'sequence, id'

    name = fields.Char(string='Nom', required=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(string='Plié dans le Kanban', default=False)


class PlannerPlan(models.Model):
    _name = 'planner.plan'
    _description = 'Plan CCDOC'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom du plan', required=True, tracking=True)
    description = fields.Html(string='Description')
    partner_id = fields.Many2one('res.partner', string='Client', tracking=True)
    stage_id = fields.Many2one(
        'planner.plan.stage',
        string='Étape',
        default=lambda self: self._default_stage(),
        group_expand='_read_group_stage_ids',
        tracking=True,
    )
    sequence = fields.Integer(default=10)
    color = fields.Integer(string='Couleur')
    user_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        tracking=True,
    )
    date_start = fields.Date(string='Date de début')
    date_end = fields.Date(string='Date de fin')
    project_id = fields.Many2one('project.project', string='Projet lié', tracking=True)
    opportunity_id = fields.Many2one('crm.lead', string='Opportunité liée', tracking=True)
    task_ids = fields.One2many('planner.task', 'plan_id', string='Tâches')
    task_count = fields.Integer(compute='_compute_task_count', string='Tâches')

    def _default_stage(self):
        return self.env['planner.plan.stage'].search([], order='sequence', limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.search([], order=order)

    @api.depends('task_ids')
    def _compute_task_count(self):
        for plan in self:
            plan.task_count = len(plan.task_ids)

    def action_open_tasks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tâches — %s' % self.name,
            'res_model': 'planner.task',
            'view_mode': 'kanban,list,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {'default_plan_id': self.id},
        }
