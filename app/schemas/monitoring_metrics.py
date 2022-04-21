from marshmallow import Schema, fields, validate


class MetricsSchema(Schema):

    start = fields.Float()
    end = fields.Float()
    step = fields.String(validate=[
        validate.Regexp(
            regex=r'^(?!\s*$)', error='step value should be a valid string'
        )
    ])


class UserGraphSchema(Schema):
    start = fields.Date()
    end = fields.Date()
    set_by = fields.String(
        validate=[
            validate.OneOf(["year", "month"],
                           error='set_by should be year or month'
                           ),
        ])


class AppGraphSchema(Schema):
    start = fields.Date()
    end = fields.Date()
    set_by = fields.String(
        validate=[
            validate.OneOf(["year", "month"],
                           error='set_by should be year or month'
                           ),
        ])


class BillingMetricsSchema(Schema):
    start = fields.Integer()
    end = fields.Integer()
    series = fields.Boolean()
    show_deployments = fields.Boolean()
    window = fields.String(validate=[
        validate.OneOf(["lastmonth", "lastweek"],
                       error='show from a certain period either pass "lastmonth" or "lastweek"'
                       ),
    ])
