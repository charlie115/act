from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from functools import wraps

def handle_db_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as err:
            # Adjust the error handling as needed based on your database/ORM
            if '23503' in str(err.orig.pgcode):
                detail = "Foreign key violation."
            else:
                detail = "Internal Database integrity error."
            raise HTTPException(status_code=400, detail=detail) from err
    return wrapper