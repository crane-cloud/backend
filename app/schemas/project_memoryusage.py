from marshmallow import Schema, fields, validate


class ProjectMemoryUsageSchema(Schema):

    start = fields.Float()
    end = fields.Float()
    step = fields.String(validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='step value should be a valid string'
            )
        ])

    
