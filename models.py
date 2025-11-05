from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class DateRange(BaseModel):
    """Modello per l'intervallo di date"""
    from_date: str = Field(..., description="Data di inizio nel formato YYYY-MM-DD")
    to: str = Field(..., description="Data di fine nel formato YYYY-MM-DD")

class WeatherRequest(BaseModel):
    """Modello per una richiesta meteo parsata"""
    city: Optional[str] = Field(None, description="Nome della città")
    metrics: List[str] = Field(
        default_factory=lambda: ["temperature"],
        description="Lista delle metriche richieste"
    )
    date_range: Optional[DateRange] = Field(None, description="Intervallo di date opzionale")
    time_of_day: Optional[str] = Field(
        None, 
        description="Momento della giornata: morning, afternoon, evening, night"
    )
    valid: bool = Field(True, description="Indica se la richiesta è valida")
    missing_parameters: List[str] = Field(
        default_factory=list,
        description="Lista dei parametri mancanti"
    )
