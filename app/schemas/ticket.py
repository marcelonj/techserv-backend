import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.security import EstadoTicket, UrgenciaTicket

class ClienteTicket(BaseModel):
    id: uuid.UUID
    full_name: str = Field(min_length=3, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    phone: str = Field(min_length=3, max_length=255)

    model_config = ConfigDict(from_attributes=True)

class TecnicoTicket(BaseModel):
    id: uuid.UUID
    full_name: str = Field(min_length=3, max_length=255)

    model_config = ConfigDict(from_attributes=True)

class EquipoTicket(BaseModel):
    id: uuid.UUID
    tipo: str = Field(min_length=3, max_length=255) 
    marca: str = Field(min_length=2, max_length=255)    
    modelo: str = Field(min_length=3, max_length=255)    
    numero_serie: str = Field(min_length=3, max_length=255)  

    model_config = ConfigDict(from_attributes=True)         

class Ticket(BaseModel):
    titulo: str = Field(min_length=3, max_length=255)
    descripcion: str = Field(min_length=3, max_length=255)
    estado: EstadoTicket | None = None
    urgencia: UrgenciaTicket
    direccion: str = Field(min_length=1, max_length=255)
    fecha_creacion: datetime | None = None
    fecha_cierre: datetime | None = None
    cliente: ClienteTicket
    tecnico: TecnicoTicket | None = None
    equipo: EquipoTicket

class TicketRead(Ticket):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class TicketCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=255)
    descripcion: str = Field(min_length=3, max_length=255)
    estado: EstadoTicket | None = None
    urgencia: UrgenciaTicket
    direccion: str = Field(min_length=1, max_length=255)
    fecha_creacion: datetime | None = None
    fecha_cierre: datetime | None = None
    cliente_id: uuid.UUID | None = None 
    tecnico_id: uuid.UUID | None = None
    equipo_id: uuid.UUID | None = None
    id: uuid.UUID | None = None

class TicketUpdate(BaseModel):
    estado: EstadoTicket | None = None
    tecnico_id: uuid.UUID | None = None