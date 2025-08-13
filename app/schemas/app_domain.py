from marshmallow import Schema, fields, validate


class AppDomainSchema(Schema):
    
    id = fields.String(dump_only=True)
    app_id = fields.String(dump_only=True)
    domain = fields.String(
        required=True, 
        validate=validate.Regexp(
            regex=r'^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$',
            error='Domain should be a valid domain, no protocol required'
        )
    )
    is_active = fields.Boolean(missing=False)
    is_generated = fields.Boolean(dump_only=True)
    date_created = fields.DateTime(dump_only=True)