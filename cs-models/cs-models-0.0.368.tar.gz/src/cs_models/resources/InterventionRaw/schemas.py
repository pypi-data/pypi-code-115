from marshmallow import (
    Schema,
    fields,
    validate,
)


class InterventionRawResourceSchema(Schema):
    not_blank = validate.Length(min=1, error='Field cannot be blank')

    id = fields.Integer(dump_only=True)
    intervention_string = fields.String(validate=not_blank, required=True)
