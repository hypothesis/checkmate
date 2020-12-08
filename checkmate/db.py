"""Basic DB connection routines."""

import logging

import alembic.command
import alembic.config
import sqlalchemy
import zope.sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

LOG = logging.getLogger(__name__)


class BaseClass:
    """Functions common to all SQLAlchemy models."""

    def __repr__(self):
        return "{class_}({kwargs})".format(
            class_=self.__class__.__name__,
            kwargs=", ".join(
                f"{kwarg}={repr(getattr(self, kwarg))}"
                for kwarg in self.__table__.columns.keys()  # pylint:disable=no-member
            ),
        )


BASE = declarative_base(
    # pylint: disable=line-too-long
    # Create a default metadata object with naming conventions for indexes and
    # constraints. This makes changing such constraints and indexes with
    # alembic after creation much easier. See:
    #   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
    cls=BaseClass,
    metadata=sqlalchemy.MetaData(
        naming_convention={
            "ix": "ix__%(column_0_label)s",
            "uq": "uq__%(table_name)s__%(column_0_name)s",
            "ck": "ck__%(table_name)s__%(constraint_name)s",
            "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
            "pk": "pk__%(table_name)s",
        }
    ),
)


SESSION = sessionmaker()


def create_engine(database_url, drop=False):  # pragma: no cover
    """Create all the database tables if they don't already exist.

    If `drop=True` is given then delete all existing tables first and then
    re-create them. Tests use this. If `drop=False` existing tables won't be
    touched.

    :param database_url: Postgres DSN to connect to
    :param drop: Whether or not to delete existing tables
    :return: An SQLAlchemy engine object
    """

    engine = sqlalchemy.create_engine(database_url)
    if drop:
        BASE.metadata.drop_all(engine)

    BASE.metadata.create_all(engine)

    return engine


def _stamp_db(engine):  # pragma: no cover
    """Stamp the database with the latest revision if it isn't already stamped.

    This is convenient in development environments to automatically stamp a new
    database after initializing it.

    """
    try:
        engine.execute("select 1 from alembic_version")
    except sqlalchemy.exc.ProgrammingError:
        alembic.command.stamp(alembic.config.Config("conf/alembic.ini"), "head")


def _session(request):  # pragma: no cover
    # This is set below in `includeme()`
    engine = request.registry["database_engine"]
    session = SESSION(bind=engine)

    # If the request has a transaction manager, associate the session with it.
    try:
        transaction_manager = request.tm
    except AttributeError:
        pass
    else:
        zope.sqlalchemy.register(session, transaction_manager=transaction_manager)

    # pyramid_tm doesn't always close the database session for us.
    #
    # If anything that executes later in the Pyramid request processing cycle
    # than pyramid_tm tween egress opens a new DB session (for example a tween
    # above the pyramid_tm tween, a response callback, or a NewResponse
    # subscriber) then pyramid_tm won't close that DB session for us.
    #
    # So as a precaution add our own callback here to make sure db sessions are
    # always closed.
    @request.add_finished_callback
    def close_the_sqlalchemy_session(_request):  # pylint: disable=unused-variable
        connections = (
            session.transaction._connections  # pylint:disable=protected-access,no-member
        )
        if len(connections) > 1:
            LOG.warning("closing an unclosed DB session")
        session.close()  # pylint:disable=no-member

    return session


def includeme(config):  # pragma: no cover
    """Pyramid config."""

    # Create the SQLAlchemy engine and save a reference in the app registry.
    database_url = config.registry.settings["database_url"]
    engine = create_engine(database_url)
    config.registry["database_engine"] = engine

    # This is set in conf/development.ini
    if config.registry.settings.get("dev"):
        _stamp_db(engine)

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to ``request.db`` in order to
    # retrieve the current database session.
    config.add_request_method(_session, name="db", reify=True)
