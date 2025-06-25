#!/usr/bin/env python3
"""
Database manager for PixelTracker

Handles database connections and configuration for both SQLite and PostgreSQL.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for handling different database backends"""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        backend: str = "sqlite",
        **kwargs
    ):
        """
        Initialize database manager
        
        Args:
            database_url: Full database URL (overrides backend)
            backend: Database backend ('sqlite' or 'postgresql')
            **kwargs: Additional database configuration
        """
        self.backend = backend
        self.config = kwargs
        self._engine = None
        self._session_factory = None
        self._scoped_session = None
        
        # Set database URL
        if database_url:
            self.database_url = database_url
            self.backend = self._detect_backend(database_url)
        else:
            self.database_url = self._build_database_url()
        
        logger.info(f"Initializing database manager for {self.backend}")
    
    def _detect_backend(self, url: str) -> str:
        """Detect database backend from URL"""
        if url.startswith('postgresql'):
            return 'postgresql'
        elif url.startswith('sqlite'):
            return 'sqlite'
        else:
            raise ValueError(f"Unsupported database URL: {url}")
    
    def _build_database_url(self) -> str:
        """Build database URL based on backend and configuration"""
        if self.backend == "sqlite":
            db_path = self.config.get('db_path', 'pixeltracker.db')
            return f"sqlite:///{db_path}"
        
        elif self.backend == "postgresql":
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 5432)
            database = self.config.get('database', 'pixeltracker')
            username = self.config.get('username', 'pixeltracker')
            password = self.config.get('password', '')
            
            # Handle password from environment
            if not password:
                password = os.getenv('DATABASE_PASSWORD', '')
            
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with appropriate configuration"""
        engine_kwargs = {
            'echo': self.config.get('echo', False),
            'pool_pre_ping': True,
        }
        
        if self.backend == "sqlite":
            # SQLite-specific configuration
            engine_kwargs.update({
                'poolclass': StaticPool,
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 30,
                    'isolation_level': None  # For autocommit mode
                }
            })
        
        elif self.backend == "postgresql":
            # PostgreSQL-specific configuration
            engine_kwargs.update({
                'pool_size': self.config.get('pool_size', 5),
                'max_overflow': self.config.get('max_overflow', 10),
                'pool_timeout': self.config.get('pool_timeout', 30),
                'pool_recycle': self.config.get('pool_recycle', 3600),
                'connect_args': {
                    'connect_timeout': 10,
                    'application_name': 'PixelTracker'
                }
            })
        
        engine = create_engine(self.database_url, **engine_kwargs)
        
        # Add SQLite-specific optimizations
        if self.backend == "sqlite":
            self._configure_sqlite(engine)
        
        return engine
    
    def _configure_sqlite(self, engine: Engine):
        """Configure SQLite-specific optimizations"""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for performance and reliability"""
            cursor = dbapi_connection.cursor()
            
            # Performance optimizations
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            
            cursor.close()
    
    @property
    def engine(self) -> Engine:
        """Get or create database engine"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory
    
    @property
    def scoped_session(self):
        """Get or create scoped session"""
        if self._scoped_session is None:
            self._scoped_session = scoped_session(self.session_factory)
        return self._scoped_session
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self, drop_existing: bool = False):
        """Create database tables"""
        try:
            if drop_existing:
                logger.warning("Dropping existing tables")
                Base.metadata.drop_all(bind=self.engine)
            
            logger.info("Creating database tables")
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables"""
        try:
            logger.warning("Dropping all database tables")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def check_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            logger.info("Database connection check successful")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about database tables"""
        try:
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            table_info = {}
            for table_name, table in metadata.tables.items():
                with self.get_session() as session:
                    # Get row count
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                    row_count = session.execute(count_query).scalar()
                    
                    table_info[table_name] = {
                        'columns': len(table.columns),
                        'row_count': row_count,
                        'indexes': len(table.indexes)
                    }
            
            return {
                'backend': self.backend,
                'database_url': self.database_url.replace(
                    self.database_url.split('@')[0].split('//')[-1] + '@', '***@'
                ) if '@' in self.database_url else self.database_url,
                'tables': table_info,
                'total_tables': len(table_info)
            }
        
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {'error': str(e)}
    
    def vacuum_database(self):
        """Vacuum/optimize database (SQLite only)"""
        if self.backend != "sqlite":
            logger.warning("Vacuum operation only supported for SQLite")
            return False
        
        try:
            # Use raw connection for VACUUM (can't be in transaction)
            connection = self.engine.raw_connection()
            cursor = connection.cursor()
            cursor.execute("VACUUM")
            connection.close()
            logger.info("Database vacuum completed")
            return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False
    
    def analyze_database(self):
        """Analyze database for query optimization"""
        try:
            with self.get_session() as session:
                if self.backend == "sqlite":
                    session.execute("ANALYZE")
                elif self.backend == "postgresql":
                    session.execute("ANALYZE")
                
            logger.info("Database analysis completed")
            return True
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            return False
    
    def close(self):
        """Close database connections"""
        try:
            if self._scoped_session:
                self._scoped_session.remove()
            
            if self._engine:
                self._engine.dispose()
                
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

class DatabaseConfig:
    """Database configuration helper"""
    
    @staticmethod
    def from_env() -> Dict[str, Any]:
        """Load database configuration from environment variables"""
        config = {
            'backend': os.getenv('DATABASE_BACKEND', 'sqlite'),
        }
        
        # SQLite configuration
        if config['backend'] == 'sqlite':
            config.update({
                'db_path': os.getenv('SQLITE_DB_PATH', 'pixeltracker.db'),
                'echo': os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
            })
        
        # PostgreSQL configuration
        elif config['backend'] == 'postgresql':
            config.update({
                'host': os.getenv('DATABASE_HOST', 'localhost'),
                'port': int(os.getenv('DATABASE_PORT', '5432')),
                'database': os.getenv('DATABASE_NAME', 'pixeltracker'),
                'username': os.getenv('DATABASE_USER', 'pixeltracker'),
                'password': os.getenv('DATABASE_PASSWORD', ''),
                'pool_size': int(os.getenv('DATABASE_POOL_SIZE', '5')),
                'max_overflow': int(os.getenv('DATABASE_MAX_OVERFLOW', '10')),
                'echo': os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
            })
        
        return config
    
    @staticmethod
    def for_testing() -> Dict[str, Any]:
        """Get database configuration for testing"""
        return {
            'backend': 'sqlite',
            'db_path': ':memory:',
            'echo': False
        }
    
    @staticmethod
    def for_production() -> Dict[str, Any]:
        """Get database configuration for production"""
        config = DatabaseConfig.from_env()
        
        # Production-specific overrides
        config.update({
            'echo': False,  # Never echo in production
            'pool_pre_ping': True,
            'pool_recycle': 3600,
        })
        
        if config['backend'] == 'postgresql':
            config.update({
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30
            })
        
        return config

# Convenience functions for common database operations

def create_database_manager(
    config: Optional[Dict[str, Any]] = None,
    environment: str = "development"
) -> DatabaseManager:
    """Create database manager with appropriate configuration"""
    
    if config is None:
        if environment == "testing":
            config = DatabaseConfig.for_testing()
        elif environment == "production":
            config = DatabaseConfig.for_production()
        else:
            config = DatabaseConfig.from_env()
    
    return DatabaseManager(**config)

def get_default_database_manager() -> DatabaseManager:
    """Get default database manager instance"""
    return create_database_manager()
