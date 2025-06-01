import importlib
import os
from operator import and_
from pathlib import Path
import time

from fastapi import HTTPException
from sqlalchemy import create_engine, URL, MetaData, Index, event
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker, Session, Query

from . import settings

# Use a direct import as the project root is added to PYTHONPATH
from apps.core.metrics import DB_QUERY_DURATION_SECONDS, DB_ERRORS_TOTAL, DB_TRANSACTIONS_TOTAL

testing = False


class DatabaseManager:
    """
    A utility class for managing database operations using SQLAlchemy.
    """
    engine: create_engine = None
    session: Session = None

    @classmethod
    def __init__(cls):
        """
        Initializes the DatabaseManager with master and replica connections.
        """
        global testing
        db_config = settings.DATABASES.copy()
        
        if testing:
            db_config["database"] = "test_" + db_config["database"]

        # Master database configuration
        cls.engine = create_engine(URL.create(**db_config))
        
        # For replica (if needed)
        cls.engine_replica = None
        if hasattr(settings, 'REPLICA_DB_CONFIG'):
            cls.engine_replica = create_engine(URL.create(**settings.REPLICA_DB_CONFIG))

        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        cls.session = session_factory()

        # Register SQLAlchemy event listeners for metrics on the main engine
        cls._setup_sqlalchemy_event_listeners(cls.engine)
        if cls.engine_replica:
            cls._setup_sqlalchemy_event_listeners(cls.engine_replica)

    @classmethod
    def _setup_sqlalchemy_event_listeners(cls, engine_to_listen):
        @event.listens_for(engine_to_listen, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())

        @event.listens_for(engine_to_listen, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            query_start_time = conn.info.setdefault('query_start_time', []).pop(-1)
            duration = time.time() - query_start_time
            
            query_type = statement.strip().split(" ", 1)[0].upper()
            # Basic table name extraction (can be improved for complex queries)
            table_name = "unknown"
            if "FROM" in statement.upper():
                try:
                    table_name = statement.upper().split("FROM")[1].strip().split(" ")[0]
                except IndexError:
                    pass # Could not parse table name
            elif "UPDATE" in statement.upper():
                 try:
                    table_name = statement.upper().split("UPDATE")[1].strip().split(" ")[0]
                 except IndexError:
                    pass
            elif "INSERT INTO" in statement.upper():
                 try:
                    table_name = statement.upper().split("INSERT INTO")[1].strip().split(" ")[0]
                 except IndexError:
                    pass

            DB_QUERY_DURATION_SECONDS.labels(query_type=query_type, table=table_name, success="true").observe(duration)

        @event.listens_for(engine_to_listen, "handle_error")
        def handle_error(context):
            # This event is triggered for various errors, including connection errors
            # and errors during query execution.
            # `context.original_exception` holds the actual exception object.
            # `context.statement` might be available if the error is related to a specific query.
            
            query_type = "unknown"
            operation = "unknown_operation"
            
            if context.statement:
                query_type = context.statement.strip().split(" ", 1)[0].upper()
                operation = query_type # or a more specific operation if parsable

            error_type_str = type(context.original_exception).__name__
            DB_ERRORS_TOTAL.labels(error_type=error_type_str, operation=operation).inc()

            # Log duration for failed queries as well
            conn = context.connection
            if conn and 'query_start_time' in conn.info and conn.info['query_start_time']:
                query_start_time = conn.info['query_start_time'].pop(-1)
                duration = time.time() - query_start_time
                table_name = "unknown" # Determine table name if possible
                DB_QUERY_DURATION_SECONDS.labels(query_type=query_type, table=table_name, success="false").observe(duration)
        
        # Session-level events for transactions
        @event.listens_for(Session, "after_commit")
        def after_commit(session):
            DB_TRANSACTIONS_TOTAL.labels(status="committed").inc()

        @event.listens_for(Session, "after_rollback")
        def after_rollback(session):
            DB_TRANSACTIONS_TOTAL.labels(status="rolled_back").inc()

    @classmethod
    def get_session(cls, read_only=False):
        """
        Returns a session - uses replica if read_only=True and replica is configured
        """
        if read_only and cls.engine_replica:
            return sessionmaker(bind=cls.engine_replica)()
        return sessionmaker(bind=cls.engine)()

    @classmethod
    def create_test_database(cls):
        """
        Create and configure a test database for use in tests.
        """
        global testing
        testing = True
        cls.__init__()
        cls.create_database_tables()

    @classmethod
    def drop_all_tables(cls):
        """
        Drop all tables in the current database.
        """
        if cls.engine:
            metadata = MetaData()
            metadata.reflect(bind=cls.engine)
            for table in metadata.tables.values():
                table.drop(cls.engine)

    @classmethod
    def create_database_tables(cls):
        """
        Create database tables based on SQLAlchemy models.
        """
        script_directory = os.path.dirname(os.path.abspath(__file__))
        project_root = Path(script_directory).parent
        apps_directory = project_root / "apps"

        for app_dir in apps_directory.iterdir():
            if app_dir.is_dir():
                models_file = app_dir / "models.py"
                if models_file.exists():
                    module_name = f"apps.{app_dir.name}.models"
                    try:
                        module = importlib.import_module(module_name)
                        if hasattr(module, "FastModel") and hasattr(module.FastModel, "metadata"):
                            module.FastModel.metadata.create_all(bind=cls.engine)
                    except ImportError:
                        pass

    @classmethod
    def get_testing_mode(cls):
        return testing


class FastModel(DeclarativeBase):
    """
    Base class for all models with CRUD operations.
    """
    @classmethod
    def __eq__(cls, **kwargs):
        filter_conditions = [getattr(cls, key) == value for key, value in kwargs.items()]
        return and_(*filter_conditions) if filter_conditions else True

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        session = DatabaseManager.session
        try:
            session.add(instance)
            session.commit()
            session.refresh(instance)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        return instance

    @classmethod
    def filter(cls, condition):
        with DatabaseManager.session as session:
            query: Query = session.query(cls).filter(condition)
        return query

    @classmethod
    def get(cls, pk):
        with DatabaseManager.session as session:
            instance = session.get(cls, pk)
        return instance

    @classmethod
    def get_or_404(cls, pk):
        with DatabaseManager.session as session:
            instance = session.get(cls, pk)
            if not instance:
                raise HTTPException(status_code=404, detail=f"{cls.__name__} not found")
        return instance

    @classmethod
    def update(cls, pk, **kwargs):
        with DatabaseManager.session as session:
            instance = session.get(cls, pk)
            if not instance:
                raise HTTPException(status_code=404, detail=f"{cls.__name__} not found")

            for key, value in kwargs.items():
                setattr(instance, key, value)

            try:
                session.commit()
                session.refresh(instance)
            except Exception:
                session.rollback()
                raise
        return instance

    @staticmethod
    def delete(instance):
        with DatabaseManager.session as session:
            session.delete(instance)
            try:
                session.commit()
            except Exception:
                session.rollback()
                raise