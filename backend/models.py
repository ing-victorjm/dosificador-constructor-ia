"""Modelo de datos de METRA AI.

Principios:

* **Trazabilidad primero.** Ninguna cantidad existe sin una fila de `Medicion`
  que diga de dónde salió: fórmula, variables, plano, página, origen y autor.
* **Jerarquía flexible.** Edificio → bloque → sector → nivel → ambiente se
  modela con UNA tabla auto-referenciada (`Ubicacion`) en vez de cinco tablas:
  un proyecto de carretera usa tramo → progresiva sin cambiar el esquema.
* **Cantidades como texto decimal.** `Numeric` sobre SQLite pierde precisión;
  se guardan como cadena y el motor las lee con `Decimal`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def uid() -> str:
    return uuid.uuid4().hex[:16]


def ahora() -> datetime:
    return datetime.now(timezone.utc)


class Marca:
    """Columnas de auditoría comunes."""
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora, onupdate=ahora)


# --------------------------------------------------------------------------- #
# Organización y personas
# --------------------------------------------------------------------------- #

class Empresa(Base, Marca):
    __tablename__ = "empresa"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    nombre: Mapped[str] = mapped_column(String(200))
    ruc: Mapped[str | None] = mapped_column(String(40))
    pais: Mapped[str] = mapped_column(String(2), default="PE")
    logo: Mapped[str | None] = mapped_column(String(300))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="empresa")
    proyectos: Mapped[list["Proyecto"]] = relationship(back_populates="empresa")


class Usuario(Base, Marca):
    __tablename__ = "usuario"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    empresa_id: Mapped[str | None] = mapped_column(ForeignKey("empresa.id", ondelete="SET NULL"))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    hash_clave: Mapped[str] = mapped_column(String(300))
    rol: Mapped[str] = mapped_column(String(20), default="metrador")
    # administrador | metrador | revisor | supervisor | cliente
    profesion: Mapped[str | None] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(40))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime)
    preferencias: Mapped[dict] = mapped_column(JSON, default=dict)

    empresa: Mapped["Empresa"] = relationship(back_populates="usuarios")


class MiembroProyecto(Base, Marca):
    """Rol de un usuario DENTRO de un proyecto (puede diferir del rol global)."""
    __tablename__ = "miembro_proyecto"
    __table_args__ = (UniqueConstraint("proyecto_id", "usuario_id", name="uq_miembro"),)
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    rol: Mapped[str] = mapped_column(String(20), default="metrador")

    usuario: Mapped["Usuario"] = relationship()


class Sesion(Base):
    """Token de sesión. Se guarda el hash, nunca el token en claro."""
    __tablename__ = "sesion"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), index=True)
    hash_token: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    expira_en: Mapped[datetime] = mapped_column(DateTime)
    agente: Mapped[str | None] = mapped_column(String(300))
    ip: Mapped[str | None] = mapped_column(String(60))


# --------------------------------------------------------------------------- #
# Proyecto y su estructura
# --------------------------------------------------------------------------- #

class Proyecto(Base, Marca):
    __tablename__ = "proyecto"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    empresa_id: Mapped[str | None] = mapped_column(ForeignKey("empresa.id", ondelete="SET NULL"), index=True)
    codigo: Mapped[str] = mapped_column(String(60), index=True)
    nombre: Mapped[str] = mapped_column(String(300))
    cliente: Mapped[str | None] = mapped_column(String(200))
    ubicacion_texto: Mapped[str | None] = mapped_column(String(300))
    responsable: Mapped[str | None] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(40), default="edificio")
    # vivienda | edificio | comercio | industria | carretera | saneamiento | otro
    pisos: Mapped[int] = mapped_column(Integer, default=1)
    sotanos: Mapped[int] = mapped_column(Integer, default=0)
    sectores: Mapped[int] = mapped_column(Integer, default=1)
    pais: Mapped[str] = mapped_column(String(2), default="PE")
    normativa: Mapped[str | None] = mapped_column(String(200))
    moneda: Mapped[str] = mapped_column(String(3), default="PEN")
    sistema_unidades: Mapped[str] = mapped_column(String(10), default="metrico")
    etapa: Mapped[str] = mapped_column(String(30), default="expediente")
    # anteproyecto | expediente | licitacion | ejecucion | liquidacion
    fecha: Mapped[str | None] = mapped_column(String(10))
    version_actual_id: Mapped[str | None] = mapped_column(String(16))
    estado: Mapped[str] = mapped_column(String(20), default="activo")
    # Reglas de cálculo del proyecto: redondeo, descuento de vanos, desperdicios,
    # impuesto, gastos generales. Todo parametrizable por país/normativa.
    reglas: Mapped[dict] = mapped_column(JSON, default=dict)
    notas: Mapped[str | None] = mapped_column(Text)
    creado_por: Mapped[str | None] = mapped_column(String(16))

    empresa: Mapped["Empresa"] = relationship(back_populates="proyectos")
    versiones: Mapped[list["Version"]] = relationship(back_populates="proyecto", cascade="all, delete-orphan")
    ubicaciones: Mapped[list["Ubicacion"]] = relationship(back_populates="proyecto", cascade="all, delete-orphan")


class Version(Base, Marca):
    """Versión del metrado. Permite comparar v2 contra v3 y congelar entregas."""
    __tablename__ = "version"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    numero: Mapped[int] = mapped_column(Integer, default=1)
    descripcion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    # borrador | en_revision | aprobada | congelada
    creada_por: Mapped[str | None] = mapped_column(String(16))
    congelada_en: Mapped[datetime | None] = mapped_column(DateTime)
    # Copia completa del metrado al congelar: permite comparar sin arqueología.
    instantanea: Mapped[dict | None] = mapped_column(JSON)

    proyecto: Mapped["Proyecto"] = relationship(back_populates="versiones")


class Ubicacion(Base, Marca):
    """Nodo de la jerarquía física: edificio, bloque, sector, nivel, ambiente."""
    __tablename__ = "ubicacion"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    padre_id: Mapped[str | None] = mapped_column(ForeignKey("ubicacion.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(20), default="nivel")
    # edificio | bloque | sector | nivel | ambiente | tramo | progresiva
    codigo: Mapped[str | None] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(200))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    cota: Mapped[str | None] = mapped_column(String(30))          # nivel +2.80
    altura_piso: Mapped[str | None] = mapped_column(String(30))   # altura libre del nivel
    area: Mapped[str | None] = mapped_column(String(30))          # área techada del ambiente
    perimetro: Mapped[str | None] = mapped_column(String(30))
    atributos: Mapped[dict] = mapped_column(JSON, default=dict)

    proyecto: Mapped["Proyecto"] = relationship(back_populates="ubicaciones")
    hijos: Mapped[list["Ubicacion"]] = relationship(cascade="all, delete-orphan")


class Elemento(Base, Marca):
    """Elemento constructivo identificable: C-1, V-101, muro M2, puerta P-1."""
    __tablename__ = "elemento"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    ubicacion_id: Mapped[str | None] = mapped_column(ForeignKey("ubicacion.id", ondelete="SET NULL"), index=True)
    tipo: Mapped[str] = mapped_column(String(40))
    # columna | viga | losa | zapata | muro | puerta | ventana | tuberia | luminaria ...
    marca: Mapped[str | None] = mapped_column(String(60))         # C-1, V-101
    nombre: Mapped[str | None] = mapped_column(String(200))
    especialidad: Mapped[str] = mapped_column(String(30), default="estructuras")
    cantidad: Mapped[str] = mapped_column(String(30), default="1")
    # Geometría y datos: {"largo":"4.20","ancho":"0.25","alto":"0.60","fc":"210"}
    propiedades: Mapped[dict] = mapped_column(JSON, default=dict)
    plano_id: Mapped[str | None] = mapped_column(ForeignKey("plano.id", ondelete="SET NULL"))
    origen: Mapped[str] = mapped_column(String(20), default="ingresado")
    # ingresado | medido | importado | detectado_ia
    confianza: Mapped[str | None] = mapped_column(String(10))     # 0..1 si viene de IA
    metrado: Mapped[bool] = mapped_column(Boolean, default=False)  # ¿ya tiene partidas?


# --------------------------------------------------------------------------- #
# Documentos y planos
# --------------------------------------------------------------------------- #

class Archivo(Base, Marca):
    __tablename__ = "archivo"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(300))
    tipo: Mapped[str] = mapped_column(String(20))   # pdf | dwg | dxf | ifc | rvt | xlsx | csv | img
    ruta: Mapped[str] = mapped_column(String(500))
    tamano: Mapped[int] = mapped_column(Integer, default=0)
    hash: Mapped[str | None] = mapped_column(String(64), index=True)
    paginas: Mapped[int] = mapped_column(Integer, default=0)
    estado: Mapped[str] = mapped_column(String(20), default="listo")
    # subiendo | procesando | listo | error
    mensaje: Mapped[str | None] = mapped_column(Text)
    subido_por: Mapped[str | None] = mapped_column(String(16))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class Plano(Base, Marca):
    """Una página de un archivo, con su calibración de escala."""
    __tablename__ = "plano"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    archivo_id: Mapped[str] = mapped_column(ForeignKey("archivo.id", ondelete="CASCADE"), index=True)
    pagina: Mapped[int] = mapped_column(Integer, default=1)
    codigo: Mapped[str | None] = mapped_column(String(60))     # A-01, E-03
    titulo: Mapped[str | None] = mapped_column(String(300))
    especialidad: Mapped[str | None] = mapped_column(String(30))
    ubicacion_id: Mapped[str | None] = mapped_column(ForeignKey("ubicacion.id", ondelete="SET NULL"))
    ancho_px: Mapped[int] = mapped_column(Integer, default=0)
    alto_px: Mapped[int] = mapped_column(Integer, default=0)
    # Calibración: cuántos metros reales mide un píxel del render.
    escala_texto: Mapped[str | None] = mapped_column(String(40))   # "1:50"
    metros_por_px: Mapped[str | None] = mapped_column(String(40))
    calibracion: Mapped[dict | None] = mapped_column(JSON)
    # {"p1":[x,y],"p2":[x,y],"distancia_real":"5.00","unidad":"m","por":"uid","fecha":"..."}
    rotacion: Mapped[int] = mapped_column(Integer, default=0)
    capas: Mapped[dict] = mapped_column(JSON, default=dict)


class Marcado(Base, Marca):
    """Trazo de medición sobre el plano: la evidencia gráfica de una cantidad."""
    __tablename__ = "marcado"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    plano_id: Mapped[str] = mapped_column(ForeignKey("plano.id", ondelete="CASCADE"), index=True)
    medicion_id: Mapped[str | None] = mapped_column(ForeignKey("medicion.id", ondelete="SET NULL"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))   # longitud | area | conteo | nota
    puntos: Mapped[list] = mapped_column(JSON, default=list)   # [[x,y],...] en píxeles del render
    valor: Mapped[str | None] = mapped_column(String(40))      # resultado en unidad real
    unidad: Mapped[str | None] = mapped_column(String(10))
    color: Mapped[str | None] = mapped_column(String(20))
    etiqueta: Mapped[str | None] = mapped_column(String(200))
    especialidad: Mapped[str | None] = mapped_column(String(30))
    autor: Mapped[str | None] = mapped_column(String(16))


# --------------------------------------------------------------------------- #
# Catálogo de partidas e insumos
# --------------------------------------------------------------------------- #

class PartidaCatalogo(Base, Marca):
    """Partida de biblioteca. `empresa_id` nulo = catálogo del sistema."""
    __tablename__ = "partida_catalogo"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    empresa_id: Mapped[str | None] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(40), index=True)
    descripcion: Mapped[str] = mapped_column(String(400))
    unidad: Mapped[str] = mapped_column(String(10))
    especialidad: Mapped[str] = mapped_column(String(30), index=True)
    capitulo: Mapped[str | None] = mapped_column(String(200))
    formula: Mapped[str | None] = mapped_column(String(500))
    plantilla_formula: Mapped[str | None] = mapped_column(String(40))
    regla_medicion: Mapped[str | None] = mapped_column(Text)   # texto literal de la norma
    norma: Mapped[str | None] = mapped_column(String(200))
    pais: Mapped[str | None] = mapped_column(String(2))
    desperdicio_pct: Mapped[str | None] = mapped_column(String(10))
    rendimiento: Mapped[str | None] = mapped_column(String(20))
    cuadrilla: Mapped[str | None] = mapped_column(String(100))
    favorita: Mapped[bool] = mapped_column(Boolean, default=False)
    verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    fuente: Mapped[str | None] = mapped_column(String(400))
    etiquetas: Mapped[list] = mapped_column(JSON, default=list)
    apu_base: Mapped[list] = mapped_column(JSON, default=list)  # composición sugerida

    __table_args__ = (Index("ix_catalogo_busqueda", "especialidad", "codigo"),)


class Insumo(Base, Marca):
    __tablename__ = "insumo"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    empresa_id: Mapped[str | None] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(40), index=True)
    descripcion: Mapped[str] = mapped_column(String(300))
    unidad: Mapped[str] = mapped_column(String(10))
    tipo: Mapped[str] = mapped_column(String(4))   # MO | MAT | EQ | SC
    grupo: Mapped[str | None] = mapped_column(String(100))
    precio_referencial: Mapped[str | None] = mapped_column(String(30))
    moneda: Mapped[str] = mapped_column(String(3), default="PEN")


class Precio(Base, Marca):
    """Precio de un insumo en una ubicación y fecha. Permite histórico real."""
    __tablename__ = "precio"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    insumo_id: Mapped[str] = mapped_column(ForeignKey("insumo.id", ondelete="CASCADE"), index=True)
    proyecto_id: Mapped[str | None] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    valor: Mapped[str] = mapped_column(String(30))
    moneda: Mapped[str] = mapped_column(String(3), default="PEN")
    fecha: Mapped[str] = mapped_column(String(10))
    lugar: Mapped[str | None] = mapped_column(String(120))
    fuente: Mapped[str | None] = mapped_column(String(300))


# --------------------------------------------------------------------------- #
# Hoja de metrados
# --------------------------------------------------------------------------- #

class Item(Base, Marca):
    """Fila del presupuesto: título (capítulo) o partida."""
    __tablename__ = "item"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[str | None] = mapped_column(ForeignKey("version.id", ondelete="CASCADE"), index=True)
    padre_id: Mapped[str | None] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), index=True)
    catalogo_id: Mapped[str | None] = mapped_column(ForeignKey("partida_catalogo.id", ondelete="SET NULL"))
    tipo: Mapped[str] = mapped_column(String(10), default="partida")   # titulo | partida
    codigo: Mapped[str | None] = mapped_column(String(40))
    descripcion: Mapped[str] = mapped_column(String(400))
    unidad: Mapped[str | None] = mapped_column(String(10))
    especialidad: Mapped[str] = mapped_column(String(30), default="arquitectura", index=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)
    desperdicio_pct: Mapped[str | None] = mapped_column(String(10))
    # Cantidad manual: solo si el usuario decide NO usar mediciones (se marca).
    cantidad_manual: Mapped[str | None] = mapped_column(String(30))
    precio_unitario: Mapped[str | None] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(String(15), default="borrador")
    # borrador | revisado | observado | aprobado
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)
    cantidad_contratada: Mapped[str | None] = mapped_column(String(30))
    cantidad_ejecutada: Mapped[str | None] = mapped_column(String(30))
    responsable: Mapped[str | None] = mapped_column(String(16))
    observaciones: Mapped[str | None] = mapped_column(Text)
    reglas: Mapped[dict] = mapped_column(JSON, default=dict)   # descuentos, factores propios
    # Familia normativa de descuento de vanos. NO es un interruptor global:
    # muros y tarrajeos descuentan todo vano sin umbral, mientras que pisos y
    # contrapisos no descuentan huecos menores a 0.25 m2. Un solo interruptor
    # para ambas familias produce error garantizado en una de las dos.
    familia_descuento: Mapped[str | None] = mapped_column(String(30))
    regla_medicion: Mapped[str | None] = mapped_column(Text)   # cita literal heredada del catálogo
    etiqueta_fuente: Mapped[str | None] = mapped_column(String(40))
    # NORMA | E060 | LITERATURA | FICHA_FABRICANTE | COSTUMBRE_OBRA | USUARIO

    mediciones: Mapped[list["Medicion"]] = relationship(
        back_populates="item", cascade="all, delete-orphan",
        order_by="Medicion.orden", lazy="selectin",
    )


class Medicion(Base, Marca):
    """UNA línea de la hoja de metrado. Aquí vive la trazabilidad."""
    __tablename__ = "medicion"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    item_id: Mapped[str] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), index=True)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    ubicacion_id: Mapped[str | None] = mapped_column(ForeignKey("ubicacion.id", ondelete="SET NULL"), index=True)
    elemento_id: Mapped[str | None] = mapped_column(ForeignKey("elemento.id", ondelete="SET NULL"))
    plano_id: Mapped[str | None] = mapped_column(ForeignKey("plano.id", ondelete="SET NULL"))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    descripcion: Mapped[str | None] = mapped_column(String(300))
    eje: Mapped[str | None] = mapped_column(String(60))       # eje A-B, tramo 0+000
    lamina: Mapped[str | None] = mapped_column(String(60))    # "E-03" aunque no haya PDF cargado
    # Columnas clásicas de la planilla de sustento. Un campo VACÍO se OMITE del
    # producto; no vale cero. Es la convención de todo expediente técnico y la
    # diferencia entre un parcial correcto y un parcial en cero.
    n: Mapped[str | None] = mapped_column(String(30))         # CANTIDAD (n° de elementos)
    veces: Mapped[str | None] = mapped_column(String(30))     # N° DE VECES
    largo: Mapped[str | None] = mapped_column(String(30))
    ancho: Mapped[str | None] = mapped_column(String(30))
    alto: Mapped[str | None] = mapped_column(String(30))
    formula: Mapped[str | None] = mapped_column(String(500))
    plantilla_formula: Mapped[str | None] = mapped_column(String(40))
    variables: Mapped[dict] = mapped_column(JSON, default=dict)   # variables extra de la fórmula
    parcial: Mapped[str | None] = mapped_column(String(40))       # resultado calculado (cache)
    unidad: Mapped[str | None] = mapped_column(String(10))
    signo: Mapped[int] = mapped_column(Integer, default=1)        # -1 para deducciones (vanos)
    origen: Mapped[str] = mapped_column(String(20), default="ingresado")
    # ingresado | medido_plano | importado | detectado_ia | supuesto
    confianza: Mapped[str | None] = mapped_column(String(10))
    supuesto: Mapped[str | None] = mapped_column(Text)     # qué se supuso y por qué
    estado: Mapped[str] = mapped_column(String(15), default="borrador")
    responsable: Mapped[str | None] = mapped_column(String(16))
    fecha: Mapped[str | None] = mapped_column(String(10))
    observacion: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(String(300))   # por qué no se pudo calcular

    item: Mapped["Item"] = relationship(back_populates="mediciones")


# --------------------------------------------------------------------------- #
# Costos
# --------------------------------------------------------------------------- #

class ApuDetalle(Base, Marca):
    """Renglón del análisis de precios unitarios de un item."""
    __tablename__ = "apu_detalle"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    item_id: Mapped[str] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), index=True)
    insumo_id: Mapped[str | None] = mapped_column(ForeignKey("insumo.id", ondelete="SET NULL"))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    tipo: Mapped[str] = mapped_column(String(4), default="MAT")
    descripcion: Mapped[str] = mapped_column(String(300))
    unidad: Mapped[str] = mapped_column(String(10))
    cuadrilla: Mapped[str | None] = mapped_column(String(30))
    cantidad: Mapped[str] = mapped_column(String(30), default="0")
    precio: Mapped[str] = mapped_column(String(30), default="0")
    rendimiento: Mapped[str | None] = mapped_column(String(30))


# --------------------------------------------------------------------------- #
# Calidad, colaboración y auditoría
# --------------------------------------------------------------------------- #

class Observacion(Base, Marca):
    __tablename__ = "observacion"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[str | None] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), index=True)
    medicion_id: Mapped[str | None] = mapped_column(ForeignKey("medicion.id", ondelete="CASCADE"))
    plano_id: Mapped[str | None] = mapped_column(ForeignKey("plano.id", ondelete="SET NULL"))
    punto: Mapped[dict | None] = mapped_column(JSON)     # {"x":..,"y":..} sobre el plano
    texto: Mapped[str] = mapped_column(Text)
    gravedad: Mapped[str] = mapped_column(String(10), default="media")   # baja | media | alta
    tipo: Mapped[str] = mapped_column(String(30), default="comentario")
    estado: Mapped[str] = mapped_column(String(15), default="abierta")   # abierta | resuelta | descartada
    autor: Mapped[str | None] = mapped_column(String(16))
    resuelta_por: Mapped[str | None] = mapped_column(String(16))


class Aprobacion(Base, Marca):
    __tablename__ = "aprobacion"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[str | None] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[str | None] = mapped_column(ForeignKey("version.id", ondelete="CASCADE"))
    accion: Mapped[str] = mapped_column(String(20))   # revisar | observar | aprobar | desbloquear
    usuario_id: Mapped[str | None] = mapped_column(String(16))
    comentario: Mapped[str | None] = mapped_column(Text)


class Historial(Base):
    """Registro de auditoría inmutable. Se escribe siempre, nunca se edita."""
    __tablename__ = "historial"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str | None] = mapped_column(String(16), index=True)
    entidad: Mapped[str] = mapped_column(String(40), index=True)
    entidad_id: Mapped[str | None] = mapped_column(String(16), index=True)
    accion: Mapped[str] = mapped_column(String(20))   # crear | editar | eliminar | aprobar | importar
    resumen: Mapped[str | None] = mapped_column(String(400))
    antes: Mapped[dict | None] = mapped_column(JSON)
    despues: Mapped[dict | None] = mapped_column(JSON)
    usuario_id: Mapped[str | None] = mapped_column(String(16), index=True)
    usuario_nombre: Mapped[str | None] = mapped_column(String(200))
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora, index=True)
    ip: Mapped[str | None] = mapped_column(String(60))


class AlertaDescartada(Base, Marca):
    """Alerta de calidad que el usuario revisó y decidió ignorar, con motivo."""
    __tablename__ = "alerta_descartada"
    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=uid)
    proyecto_id: Mapped[str] = mapped_column(ForeignKey("proyecto.id", ondelete="CASCADE"), index=True)
    clave: Mapped[str] = mapped_column(String(200), index=True)
    motivo: Mapped[str | None] = mapped_column(Text)
    usuario_id: Mapped[str | None] = mapped_column(String(16))
