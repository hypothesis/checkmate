"""Basic DB connection routines."""

import logging

import sqlalchemy
import zope.sqlalchemy
from sqlalchemy.orm import declarative_base, sessionmaker

LOG = logging.getLogger(__name__)

NAMING_CONVENTIONS = {
    "ix": "ix__%(column_0_label)s",
    "uq": "uq__%(table_name)s__%(column_0_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s",
}


class BaseClass:
    """Functions common to all SQLAlchemy models."""

    def __repr__(self):
        return "{class_}({kwargs})".format(  # pylint:disable=consider-using-f-string
            class_=self.__class__.__name__,
            kwargs=", ".join(
                f"{kwarg}={repr(getattr(self, kwarg))}"
                for kwarg in self.__table__.columns.keys()  # pylint:disable=no-member
            ),
        )


Base = declarative_base(
    # pylint: disable=line-too-long
    # Create a default metadata object with naming conventions for indexes and
    # constraints. This makes changing such constraints and indexes with
    # alembic after creation much easier. See:
    #   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
    cls=BaseClass,
    metadata=sqlalchemy.MetaData(naming_convention=NAMING_CONVENTIONS),
)


SESSION = sessionmaker()


def create_engine(database_url):  # pragma: no cover
    return sqlalchemy.create_engine(database_url)


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
    def close_the_sqlalchemy_session(_request):
        session.close()

    return session


def includeme(config):  # pragma: no cover
    """Pyramid config."""

    # Create the SQLAlchemy engine and save a reference in the app registry.
    database_url = config.registry.settings["database_url"]
    engine = create_engine(database_url)
    config.registry["database_engine"] = engine

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to ``request.db`` in order to
    # retrieve the current database session.
    config.add_request_method(_session, name="db", reify=True)
