from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlmodel import Field as SQLField
from sqlmodel import Session, SQLModel, create_engine, select

# Database
DB_URL = "sqlite:///estudiantes.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})


class Estudiante(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    nombre: str
    apellido: str
    correo: str
    edad: int


def create_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()
    yield


# App
app = FastAPI(lifespan=lifespan)


# Schemas
class EstudianteCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: EmailStr
    edad: int = Field(ge=0, le=120)


class EstudianteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str
    correo: EmailStr
    edad: int


# Endpoints
@app.post(
    "/estudiantes/", status_code=status.HTTP_201_CREATED, response_model=EstudianteRead
)
def crear_estudiante(datos: EstudianteCreate):
    estudiante = Estudiante(**datos.model_dump())
    with Session(engine) as session:
        session.add(estudiante)
        session.commit()
        session.refresh(estudiante)
        return estudiante


@app.get("/estudiantes/", response_model=list[EstudianteRead])
def obtener_estudiantes():
    with Session(engine) as session:
        return session.exec(select(Estudiante)).all()


@app.get("/estudiantes/{id}", response_model=EstudianteRead)
def obtener_estudiante(id: int):
    with Session(engine) as session:
        estudiante = session.get(Estudiante, id)
        if estudiante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Estudiante no encontrado"
            )
        return estudiante


@app.delete("/estudiantes/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_estudiante(id: int):
    with Session(engine) as session:
        estudiante = session.get(Estudiante, id)
        if estudiante is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Estudiante no encontrado"
            )
        session.delete(estudiante)
        session.commit()
