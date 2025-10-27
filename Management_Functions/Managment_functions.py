from fastapi import HTTPException
import re
def error_manager(message: str):
    raise HTTPException(status_code = 400, detail = f"ERRORE: {message}")

def validation_email(email: str):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None