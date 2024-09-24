from marshmallow import Schema, fields, validate
from app.helpers.age_utility import get_item_age
from flask import current_app


class AppSchema(Schema):

    id = fields.String(dump_only=True)

    name = fields.String(required=True, error_messgae={
        "required": "name is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='name should be a valid string'
            ),
    ])
    image = fields.String(required=True, error_message={
        "required": "image is required"},
        validate=[
            validate.Regexp(
                regex=r'^(?!\s*$)', error='image should be a valid string'
            ),
    ])
    project_id = fields.String()
    alias = fields.String()
    url = fields.Url(dump_only=True)
    internal_url = fields.Method("get_service", dump_only=True)
    env_vars = fields.Dict()
    port = fields.Int()
    command = fields.String()
    private_image = fields.Bool()
    docker_server = fields.String()
    docker_username = fields.String()
    docker_password = fields.String()
    docker_email = fields.String()
    custom_domain = fields.String(validate=validate.Regexp(
        regex=r'^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$',
        error='custom domain should be a valid domain, no protocal required'))
    replicas = fields.Int(validate=validate.Range(min=1, max=4))
    date_created = fields.Date(dump_only=True)
    age = fields.Method("get_age", dump_only=True)
    has_custom_domain = fields.Boolean()
    disabled = fields.Boolean(dump_only=True)
    admin_disabled = fields.Boolean(dump_only=True)
    delete_env_vars = fields.List(fields.Str(), load_only=True)
    app_status = fields.String()
    is_ai = fields.Boolean(required=False)
    is_notebook = fields.Boolean(required=False)

    def get_age(self, obj):
        return get_item_age(obj.date_created)

    def get_service(self, obj):
        # For more infor https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
        KUBE_SERVICE_PORT = current_app.config['KUBE_SERVICE_PORT']
        service_url = f'http://{obj.alias}-service.{obj.project.alias}.svc.cluster.local'
        # Note: need to append port 3000 for preivously built apps
        if KUBE_SERVICE_PORT != 80:
            service_url += f':{KUBE_SERVICE_PORT}'

        return service_url


class AppMultiDeploySchema(AppSchema):
    dependant_env_vars = fields.Dict(load_only=True)


class AppDeploySchema(AppSchema):
    name = fields.String(required=False)
    image = fields.String(required=False)
    is_ai = fields.Boolean(required=False)
    is_notebook = fields.Boolean(required=False)
    project_id = fields.String(required=False)
    apps = fields.List(fields.Nested(AppMultiDeploySchema), load_only=True)
