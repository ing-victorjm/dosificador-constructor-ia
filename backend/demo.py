"""Proyecto de demostración: edificio multifamiliar de tres pisos.

No son números de relleno: es un edificio coherente de 10,00 × 12,00 m, tres
niveles de 2,80 m, con la misma cadena que exige un expediente — cada cantidad
tiene su fila de sustento, su lámina y su origen declarado.

Incluye a propósito tres situaciones incómodas, para que el control de calidad
tenga algo real que decir:

* una fila a la que le falta un dato (queda sin calcular, NO se asume cero),
* una partida observada,
* una partida aprobada y bloqueada.
"""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import servicios
from .db import sesion
from .models import Elemento, Item, Medicion, Proyecto, Ubicacion, Usuario, Version
from .motor import normas

log = logging.getLogger("metra.demo")

CODIGO = "DEMO-3P"
HOY = date.today().isoformat()

# Geometría del edificio de la demostración.
LARGO, ANCHO = "12.00", "10.00"
AREA_PISO = "120.00"
ALTURA_LIBRE = "2.60"      # 2,80 de entrepiso menos 0,20 de losa
N_COLUMNAS = "12"
N_ZAPATAS = "12"


def _fila(item_id, proyecto_id, orden, **campos):
    campos.setdefault("origen", "ingresado")
    campos.setdefault("fecha", HOY)
    return Medicion(item_id=item_id, proyecto_id=proyecto_id, orden=orden, **campos)


def crear(db: Session, usuario: Usuario) -> Proyecto:
    p = Proyecto(
        empresa_id=usuario.empresa_id,
        codigo=CODIGO,
        nombre="Edificio multifamiliar Los Álamos — 3 pisos",
        cliente="Inmobiliaria Los Álamos S.A.C.",
        ubicacion_texto="Av. Los Álamos 450, Trujillo, La Libertad",
        responsable=usuario.nombre,
        tipo="edificio", pisos=3, sotanos=0, sectores=1,
        pais="PE", moneda="PEN", sistema_unidades="metrico",
        etapa="expediente", fecha=HOY,
        normativa="Norma Técnica de Metrados para Obras de Edificación y "
                  "Habilitaciones Urbanas (R.D. N° 073-2010-VIVIENDA/VMCS-DNC)",
        reglas={
            "redondeo": {"decimales_metrado": 2, "decimales_precio": 2,
                         "decimales_parcial": 2, "modo": "medio_arriba"},
            "impuesto": {"nombre": "IGV", "tasa": "18"},
            "gastos_generales_pct": "10", "utilidad_pct": "5",
            "regimen": "OE", "exigir_lamina": True,
            "bloquear_dimension_incompatible": True, "desperdicio_en_metrado": False,
        },
        notas="Proyecto de demostración de METRA AI. Todas las cantidades tienen "
              "sustento; ninguna fue asumida.",
        creado_por=usuario.id,
    )
    db.add(p)
    db.flush()

    v = Version(proyecto_id=p.id, nombre="v1", numero=1,
                descripcion="Metrado inicial del expediente", creada_por=usuario.id)
    db.add(v)
    db.flush()
    p.version_actual_id = v.id
    db.commit()

    niveles = _estructura(db, p)
    servicios.aplicar_plantilla(db, p, "edificacion", usuario.id)
    _elementos(db, p, niveles)
    _mediciones(db, p, niveles, usuario)
    _precios(db, p)
    db.commit()
    log.info("Proyecto de demostración creado: %s", p.nombre)
    return p


def _estructura(db: Session, p: Proyecto) -> dict[str, Ubicacion]:
    edificio = Ubicacion(proyecto_id=p.id, tipo="edificio", nombre="Edificio principal",
                         codigo="ED-01", orden=1, area="360.00")
    db.add(edificio)
    db.flush()

    niveles: dict[str, Ubicacion] = {"edificio": edificio}
    cimentacion = Ubicacion(proyecto_id=p.id, padre_id=edificio.id, tipo="nivel",
                            nombre="Cimentación", codigo="CIM", orden=1, cota="-1.20")
    db.add(cimentacion)
    db.flush()
    niveles["cimentacion"] = cimentacion

    for n in (1, 2, 3):
        nivel = Ubicacion(proyecto_id=p.id, padre_id=edificio.id, tipo="nivel",
                          nombre=f"Piso {n}", codigo=f"N{n}", orden=n + 1,
                          cota=f"{(n - 1) * 2.8:.2f}", altura_piso="2.80",
                          area=AREA_PISO, perimetro="44.00")
        db.add(nivel)
        db.flush()
        niveles[f"piso{n}"] = nivel
        for nombre, largo, ancho in (("Sala-comedor", "5.50", "4.00"),
                                     ("Dormitorio principal", "4.00", "3.50"),
                                     ("Dormitorio 2", "3.50", "3.00"),
                                     ("Cocina", "3.00", "2.50"),
                                     ("Baño", "2.40", "1.60")):
            db.add(Ubicacion(
                proyecto_id=p.id, padre_id=nivel.id, tipo="ambiente", nombre=nombre,
                orden=1, area=f"{float(largo) * float(ancho):.2f}",
                perimetro=f"{2 * (float(largo) + float(ancho)):.2f}",
                altura_piso=ALTURA_LIBRE,
                atributos={"largo": largo, "ancho": ancho}))

    azotea = Ubicacion(proyecto_id=p.id, padre_id=edificio.id, tipo="nivel",
                       nombre="Azotea", codigo="AZ", orden=5, cota="8.40", area=AREA_PISO)
    db.add(azotea)
    db.flush()
    niveles["azotea"] = azotea
    db.commit()
    return niveles


def _elementos(db: Session, p: Proyecto, niveles: dict) -> None:
    db.add(Elemento(proyecto_id=p.id, ubicacion_id=niveles["cimentacion"].id,
                    tipo="zapata", marca="Z-1", nombre="Zapata aislada 1.50x1.50",
                    especialidad="estructuras", cantidad=N_ZAPATAS,
                    propiedades={"largo": "1.50", "ancho": "1.50", "peralte": "0.60",
                                 "profundidad": "1.20", "fc": "210"},
                    origen="ingresado", metrado=True))
    for n in (1, 2, 3):
        db.add(Elemento(proyecto_id=p.id, ubicacion_id=niveles[f"piso{n}"].id,
                        tipo="columna", marca="C-1", nombre="Columna 0.25x0.50",
                        especialidad="estructuras", cantidad=N_COLUMNAS,
                        propiedades={"lado_a": "0.25", "lado_b": "0.50",
                                     "altura": ALTURA_LIBRE, "fc": "210"},
                        origen="ingresado", metrado=True))
        db.add(Elemento(proyecto_id=p.id, ubicacion_id=niveles[f"piso{n}"].id,
                        tipo="viga", marca="V-101", nombre="Viga peraltada 0.25x0.50",
                        especialidad="estructuras", cantidad="1",
                        propiedades={"base": "0.25", "peralte": "0.50", "longitud": "46.00",
                                     "fc": "210"},
                        origen="ingresado", metrado=True))
        db.add(Elemento(proyecto_id=p.id, ubicacion_id=niveles[f"piso{n}"].id,
                        tipo="losa_aligerada", marca="LA-20",
                        nombre="Losa aligerada h=0.20 m", especialidad="estructuras",
                        cantidad="1", propiedades={"area": "100.00", "altura": "0.20"},
                        origen="ingresado", metrado=True))
    # Elemento registrado a propósito SIN metrar: alimenta el control de calidad.
    db.add(Elemento(proyecto_id=p.id, ubicacion_id=niveles["azotea"].id,
                    tipo="escalera", marca="ESC-1", nombre="Escalera de acceso a azotea",
                    especialidad="estructuras", cantidad="1",
                    propiedades={"ancho": "1.20", "n_pasos": "18", "paso": "0.25",
                                 "contrapaso": "0.175", "garganta": "0.15"},
                    origen="ingresado", metrado=False))
    db.commit()


def _buscar(db: Session, p: Proyecto, codigo: str, texto: str) -> Item | None:
    item = db.scalar(select(Item).where(Item.proyecto_id == p.id, Item.codigo == codigo,
                                        Item.tipo == "partida"))
    if item:
        return item
    return db.scalar(select(Item).where(Item.proyecto_id == p.id, Item.tipo == "partida",
                                        Item.descripcion.like(f"%{texto}%")))


def _mediciones(db: Session, p: Proyecto, niveles: dict, usuario: Usuario) -> None:
    """Carga el sustento real del edificio, partida por partida."""
    pisos = [(n, niveles[f"piso{n}"]) for n in (1, 2, 3)]

    def agregar(codigo, texto, filas, **ajustes):
        item = _buscar(db, p, codigo, texto)
        if not item:
            log.warning("Partida no encontrada en la demo: %s / %s", codigo, texto)
            return None
        for i, campos in enumerate(filas, start=1):
            db.add(_fila(item.id, p.id, i * 10, responsable=usuario.id,
                         unidad=item.unidad, **campos))
        for campo, valor in ajustes.items():
            setattr(item, campo, valor)
        db.flush()
        return item

    # --- Preliminares -------------------------------------------------------
    agregar("OE.1.1.9", "Trazos, niveles y replanteo", [
        {"descripcion": "Área del terreno", "n": "1", "largo": LARGO, "ancho": ANCHO,
         "lamina": "A-01", "eje": "A-D / 1-4"},
    ])

    # --- Movimiento de tierras ---------------------------------------------
    agregar("OE.2.1.2", "Excavación para zapatas", [
        {"descripcion": "Zapatas Z-1 (incluye 0.15 m de sobreancho por cara)",
         "n": N_ZAPATAS, "largo": "1.80", "ancho": "1.80", "alto": "1.20",
         "lamina": "E-01", "eje": "Ejes A-D / 1-4",
         "ubicacion_id": niveles["cimentacion"].id},
    ])
    agregar("OE.2.1.6", "Eliminación de material excedente", [
        {"descripcion": "Volumen de excavación de zapatas",
         "n": "1", "largo": "46.66", "lamina": "E-01",
         "observacion": "Pendiente de aplicar el factor de esponjamiento del suelo. "
                        + normas.REGLA_ESPONJAMIENTO["explicacion"],
         "origen": "ingresado"},
    ])

    # --- Concreto simple ----------------------------------------------------
    agregar("OE.2.2.1", "Cimientos corridos", [
        {"descripcion": "Cimiento corrido perimetral", "n": "1", "largo": "44.00",
         "ancho": "0.60", "alto": "0.80", "lamina": "E-01", "eje": "Perímetro"},
        {"descripcion": "Cimiento corrido interior", "n": "1", "largo": "18.00",
         "ancho": "0.50", "alto": "0.80", "lamina": "E-01", "eje": "Eje B"},
    ])
    agregar("OE.2.2.9", "Falso piso", [
        {"descripcion": "Primer piso", "n": "1", "largo": LARGO, "ancho": ANCHO,
         "lamina": "A-02", "ubicacion_id": niveles["piso1"].id},
    ])

    # --- Zapatas ------------------------------------------------------------
    agregar("OE.2.3.2.1", "Zapatas — concreto", [
        {"descripcion": "Zapatas Z-1 1.50x1.50x0.60", "n": N_ZAPATAS, "largo": "1.50",
         "ancho": "1.50", "alto": "0.60", "lamina": "E-02",
         "ubicacion_id": niveles["cimentacion"].id},
    ])
    agregar("OE.2.3.2.2", "Zapatas — encofrado", [
        {"descripcion": "Caras laterales de zapatas Z-1 (perímetro × peralte)",
         "n": N_ZAPATAS, "largo": "6.00", "ancho": "0.60", "lamina": "E-02",
         "observacion": "Perímetro = 2 × (1.50 + 1.50) = 6.00 m. El fondo apoya sobre "
                        "el solado: no se encofra."},
    ])
    agregar("OE.2.3.2.3", "Zapatas — acero", [
        {"descripcion": "Z-1 · malla inferior Ø 5/8\" @ 0.15 · sentido X",
         "formula": "n * cantidad * longitud * peso_unitario",
         "variables": {"n": N_ZAPATAS, "cantidad": "10", "longitud": "1.60",
                       "peso_unitario": "1.552", "diametro": "5/8\""},
         "lamina": "E-02"},
        {"descripcion": "Z-1 · malla inferior Ø 5/8\" @ 0.15 · sentido Y",
         "formula": "n * cantidad * longitud * peso_unitario",
         "variables": {"n": N_ZAPATAS, "cantidad": "10", "longitud": "1.60",
                       "peso_unitario": "1.552", "diametro": "5/8\""},
         "lamina": "E-02"},
    ])

    # --- Columnas -----------------------------------------------------------
    agregar("OE.2.3.7.1", "Columnas — concreto", [
        {"descripcion": f"Columnas C-1 0.25x0.50 · piso {n}", "n": N_COLUMNAS,
         "largo": "0.25", "ancho": "0.50", "alto": ALTURA_LIBRE,
         "lamina": "E-03", "eje": "A-D / 1-4", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ])
    agregar("OE.2.3.7.2", "Columnas — encofrado", [
        {"descripcion": f"C-1 · perímetro 1.50 m × altura · piso {n}", "n": N_COLUMNAS,
         "largo": "1.50", "ancho": ALTURA_LIBRE, "lamina": "E-03",
         "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ])
    agregar("OE.2.3.7.3", "Columnas — acero", [
        {"descripcion": f"C-1 · 8 Ø 5/8\" longitudinal · piso {n}",
         "formula": "n * cantidad * longitud * peso_unitario",
         "variables": {"n": N_COLUMNAS, "cantidad": "8", "longitud": "3.20",
                       "peso_unitario": "1.552", "diametro": "5/8\"", "traslapes": "0.60"},
         "lamina": "E-03", "ubicacion_id": nivel.id,
         "observacion": "Incluye la longitud empotrada en la zapata: el arranque se "
                        "computa en la columna, no en la cimentación (OE.2.3)."}
        for n, nivel in pisos
    ])

    # --- Vigas --------------------------------------------------------------
    agregar("OE.2.3.8.1", "Vigas — concreto", [
        {"descripcion": f"Vigas V-101 0.25x0.50 · piso {n}", "n": "1", "largo": "46.00",
         "ancho": "0.25", "alto": "0.50", "lamina": "E-04", "ubicacion_id": nivel.id,
         "observacion": "Longitud medida entre caras de columnas."}
        for n, nivel in pisos
    ])
    agregar("OE.2.3.8.2", "Vigas — encofrado", [
        {"descripcion": f"V-101 · fondo + 2 costados · piso {n}", "n": "1",
         "largo": "46.00", "ancho": "1.25", "lamina": "E-04", "ubicacion_id": nivel.id,
         "observacion": "Ancho de contacto = 0.25 (fondo) + 2 × 0.50 (costados) = 1.25 m."}
        for n, nivel in pisos
    ])

    # --- Losa aligerada -----------------------------------------------------
    agregar("OE.2.3.9.2.1", "Losa aligerada — concreto", [
        {"descripcion": f"Aligerado h=0.20 · piso {n}",
         "formula": "area * concreto_por_m2",
         "variables": {"area": "100.00", "concreto_por_m2": "0.087"},
         "lamina": "E-05", "ubicacion_id": nivel.id, "origen": "supuesto",
         "supuesto": "Volumen de concreto por m² de aligerado h=0.20 m tomado de "
                     "literatura técnica (0.087 m³/m²). Debe contrastarse con la ficha "
                     "del ladrillo de techo que se use en obra."}
        for n, nivel in pisos
    ])
    agregar("OE.2.3.9.2.2", "Losa aligerada — encofrado", [
        {"descripcion": f"Fondo de aligerado · piso {n}", "n": "1", "largo": "100.00",
         "lamina": "E-05", "ubicacion_id": nivel.id,
         "observacion": "Se mide el área total del fondo, sin descontar el área de los "
                        "ladrillos de techo (OE.2.3.9.2.2)."}
        for n, nivel in pisos
    ])
    agregar("OE.2.3.9.2.4", "Losa aligerada — ladrillo", [
        {"descripcion": f"Ladrillo de techo 15x30x30 · piso {n}",
         "formula": "area * ladrillos_por_m2",
         "variables": {"area": "100.00", "ladrillos_por_m2": "8.33"},
         "lamina": "E-05", "ubicacion_id": nivel.id, "origen": "supuesto",
         "supuesto": "8.33 und/m² corresponde a viguetas @ 0.40 m con ladrillo de 0.30 m. "
                     "Verificar contra la ficha del fabricante."}
        for n, nivel in pisos
    ])

    # --- Muros: con descuento de vanos, sin umbral (OE.3.1) -----------------
    muros = agregar("OE.3.1.1", "Muro de ladrillo King Kong", [
        *[{"descripcion": f"Muros perimetrales · piso {n}", "n": "1", "largo": "44.00",
           "alto": ALTURA_LIBRE, "lamina": "A-03", "ubicacion_id": nivel.id}
          for n, nivel in pisos],
        *[{"descripcion": f"Tabiquería interior · piso {n}", "n": "1", "largo": "38.00",
           "alto": ALTURA_LIBRE, "lamina": "A-03", "ubicacion_id": nivel.id}
          for n, nivel in pisos],
        *[{"descripcion": f"Menos ventanas V-1 1.50x1.20 · piso {n}", "n": "6",
           "ancho": "1.50", "alto": "1.20", "signo": -1, "lamina": "A-03",
           "ubicacion_id": nivel.id,
           "observacion": "OE.3.1 — Se descuentan todos los vanos, sin umbral."}
          for n, nivel in pisos],
        *[{"descripcion": f"Menos puertas P-1 0.90x2.10 · piso {n}", "n": "5",
           "ancho": "0.90", "alto": "2.10", "signo": -1, "lamina": "A-03",
           "ubicacion_id": nivel.id,
           "observacion": "OE.3.1 — Se descuentan todos los vanos, sin umbral."}
          for n, nivel in pisos],
    ], familia_descuento="muros", estado="revisado")

    # --- Revoques -----------------------------------------------------------
    agregar("OE.3.2.2", "Tarrajeo en interiores", [
        {"descripcion": f"Caras interiores de muros · piso {n}", "n": "2", "largo": "82.00",
         "alto": ALTURA_LIBRE, "lamina": "A-04", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ], familia_descuento="revoques")
    agregar("OE.3.2.3", "Tarrajeo en exteriores", [
        {"descripcion": f"Fachadas · piso {n}", "n": "1", "largo": "44.00",
         "alto": ALTURA_LIBRE, "lamina": "A-04", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ], familia_descuento="revoques")
    agregar("OE.3.2.19", "Vestidura de derrames", [
        {"descripcion": f"Derrames de ventanas y puertas · piso {n}", "n": "1",
         "largo": "62.40", "lamina": "A-04", "ubicacion_id": nivel.id,
         "observacion": "Perímetro de vanos: ventanas 6 × 5.40 + puertas 5 × 6.00."}
        for n, nivel in pisos
    ])

    # --- Cielorrasos y pisos: umbral 0,25 m² --------------------------------
    agregar("OE.3.3.1", "Cielorraso con yeso", [
        {"descripcion": f"Cielorraso · piso {n}", "n": "1", "largo": LARGO, "ancho": ANCHO,
         "lamina": "A-05", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ], familia_descuento="cielorrasos")
    agregar("OE.3.4.1", "Contrapiso", [
        {"descripcion": f"Contrapiso · piso {n}", "n": "1", "largo": LARGO, "ancho": ANCHO,
         "lamina": "A-05", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ], familia_descuento="pisos")
    agregar("OE.3.4.2", "Piso cerámico", [
        {"descripcion": f"Piso cerámico 0.45x0.45 · piso {n}", "n": "1", "largo": "108.00",
         "lamina": "A-05", "ubicacion_id": nivel.id,
         "observacion": "Se descuenta el área de baños, que llevan otro acabado."}
        for n, nivel in pisos
    ], familia_descuento="pisos", desperdicio_pct="7")

    agregar("OE.3.5.2", "Contrazócalo", [
        {"descripcion": f"Contrazócalo cerámico h=0.10 · piso {n}", "n": "1",
         "largo": "126.00", "lamina": "A-05", "ubicacion_id": nivel.id,
         "observacion": "Perímetro de ambientes menos el ancho de los umbrales."}
        for n, nivel in pisos
    ])

    # --- Pintura ------------------------------------------------------------
    agregar("OE.3.11.1", "Pintura látex", [
        {"descripcion": f"Muros y cielorrasos · piso {n}", "n": "1", "largo": "546.40",
         "lamina": "A-06", "ubicacion_id": nivel.id,
         "observacion": "Hereda el área tarrajeada. El número de manos multiplica el "
                        "material en el APU, nunca el área metrada (OE.3.11.1)."}
        for n, nivel in pisos
    ], familia_descuento="pintura")

    # --- Carpintería --------------------------------------------------------
    agregar("OE.3.7.1", "Puerta contraplacada", [
        {"descripcion": "Puertas P-1 0.90x2.10", "n": "15", "lamina": "A-07",
         "observacion": "5 puertas por piso × 3 pisos."},
    ])
    agregar("OE.3.7.2", "Ventana de madera", [
        {"descripcion": "Ventanas V-1 1.50x1.20", "n": "18", "lamina": "A-07"},
    ])

    # --- Sanitarias ---------------------------------------------------------
    agregar("OE.4.2.1", "Salida de agua fría", [
        {"descripcion": f"Salidas de agua fría · piso {n}", "n": "8",
         "lamina": "IS-01", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ])
    agregar("OE.4.2.2", "Red de distribución de agua fría", [
        {"descripcion": f"Tubería PVC Ø 1/2\" · piso {n}", "n": "1", "largo": "34.00",
         "lamina": "IS-01", "ubicacion_id": nivel.id,
         "observacion": "Medida sobre el plano. No se descuenta la longitud de los "
                        "accesorios (OE.4)."}
        for n, nivel in pisos
    ])
    agregar("OE.4.3.1", "Salida de desagüe", [
        {"descripcion": f"Salidas de desagüe · piso {n}", "n": "7",
         "lamina": "IS-02", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ])

    # --- Eléctricas ---------------------------------------------------------
    agregar("OE.5.1.1", "Salida para alumbrado", [
        {"descripcion": f"Salidas de alumbrado · piso {n}", "n": "14",
         "lamina": "IE-01", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ])
    agregar("OE.5.1.2", "Salida para tomacorriente", [
        {"descripcion": f"Tomacorrientes dobles · piso {n}", "n": "18",
         "lamina": "IE-01", "ubicacion_id": nivel.id}
        for n, nivel in pisos
    ])
    # Fila incompleta A PROPÓSITO: falta la longitud, y el motor no asume cero.
    agregar("OE.5.2.3", "Conductor THW", [
        {"descripcion": "Conductor 2.5 mm2 — pendiente de medir en plano IE-02",
         "formula": "longitud_tuberia * n_conductores",
         "variables": {"n_conductores": "3"},
         "lamina": "IE-02", "origen": "ingresado",
         "observacion": "Falta la longitud de tubería. El conductor se obtiene de la "
                        "canalización que lo contiene (OE.5.2.3), no de un factor por punto."},
    ], estado="observado")

    # --- Varios -------------------------------------------------------------
    aprobada = agregar("OE.3.13.2", "Limpieza final", [
        {"descripcion": "Área techada total", "n": "3", "largo": LARGO, "ancho": ANCHO,
         "lamina": "A-01"},
    ])
    if aprobada:
        aprobada.estado = "aprobado"
        aprobada.bloqueado = True

    db.commit()


def _precios(db: Session, p: Proyecto) -> None:
    """Precios unitarios referenciales para que el presupuesto muestre algo real."""
    referencia = {
        "OE.1.1.9": "2.80", "OE.2.1.2": "38.50", "OE.2.1.6": "28.00",
        "OE.2.2.1": "265.00", "OE.2.2.9": "32.00",
        "OE.2.3.2.1": "352.00", "OE.2.3.2.2": "42.00", "OE.2.3.2.3": "5.20",
        "OE.2.3.7.1": "398.00", "OE.2.3.7.2": "58.00", "OE.2.3.7.3": "5.20",
        "OE.2.3.8.1": "375.00", "OE.2.3.8.2": "62.00",
        "OE.2.3.9.2.1": "368.00", "OE.2.3.9.2.2": "48.00", "OE.2.3.9.2.4": "3.10",
        "OE.3.1.1": "78.00", "OE.3.2.2": "26.50", "OE.3.2.3": "31.00",
        "OE.3.2.19": "18.00", "OE.3.3.1": "28.00", "OE.3.4.1": "34.00",
        "OE.3.4.2": "72.00", "OE.3.5.2": "22.00", "OE.3.11.1": "14.50",
        "OE.3.7.1": "420.00", "OE.3.7.2": "310.00",
        "OE.4.2.1": "95.00", "OE.4.2.2": "22.00", "OE.4.3.1": "115.00",
        "OE.5.1.1": "82.00", "OE.5.1.2": "88.00", "OE.3.13.2": "3.20",
    }
    for item in db.scalars(select(Item).where(Item.proyecto_id == p.id,
                                              Item.tipo == "partida")):
        if item.codigo in referencia:
            item.precio_unitario = referencia[item.codigo]
    db.commit()


def asegurar() -> str | None:
    """Crea la demostración si no existe. Se llama al arrancar."""
    with sesion() as db:
        ya = db.scalar(select(Proyecto).where(Proyecto.codigo == CODIGO))
        if ya:
            return ya.id
        usuario = db.scalar(select(Usuario).order_by(Usuario.creado_en))
        if not usuario:
            return None
        return crear(db, usuario).id


def rehacer() -> str | None:
    """Borra y vuelve a crear la demostración (útil tras cambiar el motor)."""
    with sesion() as db:
        for viejo in db.scalars(select(Proyecto).where(Proyecto.codigo == CODIGO)):
            db.delete(viejo)
        db.commit()
    return asegurar()
