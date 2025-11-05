from fastapi import HTTPException
import re
def error_manager(err):
    if isinstance(err, HTTPException):
        # Rilancia l'errore originale (mantiene status_code e messaggio)
        raise HTTPException(status_code=err.status_code, detail=err.detail)
    
    # Se non è un HTTPException, trattalo come errore interno
    raise HTTPException(status_code=500, detail=f"ERRORE INTERNO: {str(err)}")

def validation_email(email: str):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
