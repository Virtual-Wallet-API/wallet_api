import logging

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import DB_URL

logging.basicConfig(level=logging.INFO,
                    filename="logs/database.log",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


# Retry on query failure
# Global rollback
class RetrySession(Session):

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def execute(self, *args, **kwargs):
        try:
            return super().execute(*args, **kwargs)

        except OperationalError as e:
            logger.error(f"OperationalError during execute, rolling back: {str(e)}")
            self.rollback()
            raise

        except Exception as e:
            logger.error(f"Unexpected error during execute, rolling back: {str(e)}")
            self.rollback()
            raise


engine = create_engine(DB_URL,
                       pool_size=5,
                       max_overflow=10,
                       pool_timeout=30,
                       pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=RetrySession)

Base = declarative_base()


def get_connection():
    db = SessionLocal()
    logger.info("Opening new database session")

    try:
        yield db

    except Exception as e:
        logger.error(f"Error in database session: {str(e)}")
        raise

    finally:
        logger.info("Closing database session")
        db.close()


@event.listens_for(engine, "handle_error")
def handle_db_error(context):
    original_exception = context.original_exception

    if isinstance(original_exception, OperationalError) and "timeout" in str(original_exception).lower():
        logger.error(f"Database timeout error: {str(original_exception)}")
        raise HTTPException(status_code=503, detail="Database connection timed out. Please try again later.")

    logger.error(f"Database error: {str(original_exception)}")
    raise HTTPException(status_code=500, detail="Database error occurred")
