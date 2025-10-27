from typing import List, Optional
from pydantic import BaseModel, Field

class DateRange(BaseModel):
    """Modello per l'intervallo di date"""
    from_date: str = Field(description="Data di inizio dell'intervallo in formato YYYY-MM-DD")
    to: str = Field(description="Data di fine dell'intervallo in formato YYYY-MM-DD")

class WeatherRequest(BaseModel):
    """Modello per la richiesta meteo parsata"""
    city: Optional[str] = Field(None, description="Nome della città per cui si richiedono i dati meteo.")
    metrics: List[str] = Field(
        default=["temperature"], 
        description="Elenco delle metriche meteo richieste."
    )
    date_range: Optional[DateRange] = Field(None, description="Intervallo di date richiesto.")
    valid: bool = Field(True, description="Indica se la richiesta è valida dopo il parsing.")
    missing_parameters: List[str] = Field(
        default_factory=list, 
        description="Lista di parametri obbligatori mancanti."
    )
