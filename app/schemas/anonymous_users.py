from json import load
from marshmallow import Schema, fields,validate

class AnonymousUsersSchema(Schema):

    id = fields.UUID(dump_only=True)
<<<<<<< HEAD

=======
>>>>>>> 806df09 (work on pr feedback: reformat email)
    email = fields.String(required=True)
    role = fields.String(required=True, validate=[
            validate.OneOf(["owner", "admin", "member"],
                           error='role should either be owner, admin or member'
                           ),
        ])
    project_id = fields.String()

