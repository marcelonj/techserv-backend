import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class Equipo(BaseModel):
    tipo: str = Field(min_length=1, max_length=255)
    marca: str = Field(min_length=1, max_length=255)
    modelo: str = Field(min_length=1, max_length=255)
    numero_serie: str = Field(min_length=1, max_length=255)
    fecha_creacion: datetime | None = None
    cliente_id: uuid.UUID | None = None

class EquipoRead(Equipo):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

class EquipoCreate(Equipo):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None