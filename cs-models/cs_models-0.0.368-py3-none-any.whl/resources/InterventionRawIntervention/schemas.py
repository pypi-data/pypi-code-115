from marshmallow import (
    Schema,
    fields,
    validate,
)


class InterventionRawInterventionResourceSchema(Schema):
    not_blank = validate.Length(min=1, error='Field cannot be blank')

    id = fields.Integer(dump_only=True)
    intervention_raw_id = fields.Integer(required=True)
    intervention_id = fields.Integer(required=True)
    score = fields.Float(required=True)
    updated_at = fields.DateTime()
