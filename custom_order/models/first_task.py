from odoo import models, fields, api 

class FirstTask(models.Model):

    _name = 'first.task'

    partner_id = fields.Many2one('res.partner', string="Name")
    phone = fields.Char(related="partner_id.phone")
    lines = fields.One2many('first.task.lines', 'rel_id')

    @api.model
    def default_get(self, fields):
        result = super(FirstTask, self).default_get(fields)
        lines = [(5, 0, 0)]
        m_obj = self.env['product.product'].search([('x_studio_is_custom_order', '=', True)])
        for m in m_obj:
            #if m.ttype == 'cement':
            line = (0 ,0,{
                    'product_id' : m.id,
                })
            lines.append(line)
        result.update({
            'lines' : lines
        })
        return result

class FirstTaskLines(models.Model):

    _name = 'first.task.lines'

    product_id = fields.Many2one('product.product')
    qty = fields.Integer(string="Qty", default=0)
    rel_id = fields.Many2one('first.task')
