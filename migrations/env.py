import os
from logging.config import fileConfig
import logging

from sqlalchemy import engine_from_config, pool, text
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger('alembic.env')

from server import create_app
from app.models import db

config_name = os.getenv('FLASK_CONFIG') or 'development'
app = create_app(config_name)

with app.app_context():
    config.set_main_option(
        'sqlalchemy.url', app.config.get('SQLALCHEMY_DATABASE_URI').replace('%', '%%'))
    target_metadata = app.extensions['migrate'].db.metadata

    def run_migrations_offline() -> None:
        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online() -> None:
        def process_revision_directives(context, revision, directives):
            if getattr(config.cmd_opts, 'autogenerate', False):
                script = directives[0]
                if script.upgrade_ops.is_empty():
                    directives[:] = []
                    logger.info('No changes in schema detected.')

        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix='sqlalchemy.',
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                process_revision_directives=process_revision_directives,
                **app.extensions['migrate'].configure_args
            )

            logger.info('Creating extension uuid-ossp...')
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            logger.info('Extension uuid-ossp created.')

            with context.begin_transaction():
                context.run_migrations()
                logger.info('Migrations have been run.')

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
