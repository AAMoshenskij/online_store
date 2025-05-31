import importlib
import os
from operator import and_
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import create_engine, URL, MetaData, Index
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker, Session, Query

from . import settings

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

        session = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        cls.session = session()

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