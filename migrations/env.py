import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

fileConfig(config.config_file_name)

from server import create_app

config_name = os.getenv('FLASK_CONFIG') or 'development'
app = create_app(config_name)

database_uri = app.config['SQLALCHEMY_DATABASE_URI']
if not database_uri:
    raise ValueError("SQLALCHEMY_DATABASE_URI is not set")

config.set_main_option('sqlalchemy.url', database_uri.replace('%', '%%'))
target_metadata = app.extensions['migrate'].db.metadata

def process_revision_directives(context, revision, directives):
    if getattr(config.cmd_opts, 'autogenerate', False):
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] = []
            app.logger.info('No changes in schema detected.')

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()
            app.logger.info('Migrations have been run.')

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
