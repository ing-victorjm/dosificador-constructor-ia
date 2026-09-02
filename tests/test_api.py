"""Pruebas de la API sobre una base de datos temporal.

Recorren el camino completo: crear proyecto → agregar partida → agregar filas →
comprobar el total → exportar. Si alguna ruta se rompe, esto lo detecta.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

TEMPORAL = Path(tempfile.mkdtemp(prefix="metra_test_"))
os.environ["METRA_DIR_DATOS"] = str(TEMPORAL)
os.environ["METRA_DB_URL"] = f"sqlite:///{(TEMPORAL / 'prueba.db').as_posix()}"
os.environ["METRA_MODO"] = "local"

from fastapi.testclient import TestClient  # noqa: E402

from backend.db import crear_tablas  # noqa: E402
from backend.main import app  # noqa: E402


@pytest.fixture(scope="module")
def cliente():
    crear_tablas()
    from backend.semillas import sembrar
    sembrar()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def proyecto(cliente):
    r = cliente.post("/api/proyectos", json={
        "nombre": "Proyecto de prueba", "tipo": "vivienda", "pisos": 2,
        "pais": "PE", "generar_estructura": True,
    })
    assert r.status_code == 201, r.text
    return r.json()["proyecto"]


def test_referencia_trae_lo_que_la_interfaz_necesita(cliente):
    datos = cliente.get("/api/referencia").json()
    assert len(datos["unidades"]) > 30
    assert len(datos["especialidades"]) >= 10
    assert len(datos["plantillas_formula"]) >= 10
    assert "familias" in datos["reglas"]
    assert any(f["modo"] == "deducir_exceso" for f in datos["reglas"]["familias"])


def test_catalogo_normativo_sembrado(cliente):
    datos = cliente.get("/api/catalogo/partidas?q=muro&por_pagina=5").json()
    assert datos["total"] > 0
    assert all(p["codigo"] for p in datos["partidas"])


def test_crear_proyecto_genera_estructura(cliente, proyecto):
    datos = cliente.get(f"/api/proyectos/{proyecto['id']}").json()
    nombres = []

    def recorrer(nodos):
        for n in nodos:
            nombres.append(n["nombre"])
            recorrer(n["hijos"])

    recorrer(datos["ubicaciones"])
    assert "Piso 1" in nombres and "Piso 2" in nombres and "Azotea" in nombres


def test_ciclo_completo_de_metrado(cliente, proyecto):
    pid = proyecto["id"]

    r = cliente.post(f"/api/proyectos/{pid}/items", json={
        "tipo": "partida", "descripcion": "Muro de ladrillo de prueba",
        "unidad": "m2", "especialidad": "arquitectura",
    })
    assert r.status_code == 201, r.text
    item = r.json()["item"]
    assert item["familia_descuento"] == "muros"      # deducido del texto

    cliente.post(f"/api/items/{item['id']}/mediciones", json={
        "descripcion": "Paño A", "n": "1", "largo": "10.00", "alto": "2.60",
        "lamina": "A-01",
    })
    cliente.post(f"/api/items/{item['id']}/mediciones", json={
        "descripcion": "Menos puerta", "n": "1", "ancho": "0.90", "alto": "2.10",
        "signo": -1, "lamina": "A-01",
    })

    datos = cliente.get(f"/api/items/{item['id']}").json()
    assert datos["resumen"]["total"] == "24.11"      # 26.00 − 1.89
    assert datos["resumen"]["deducciones"] == "-1.89"


def test_bloqueo_dimensional_rechaza_la_fila(cliente, proyecto):
    r = cliente.post(f"/api/proyectos/{proyecto['id']}/items", json={
        "tipo": "partida", "descripcion": "Piso de prueba", "unidad": "m2",
    })
    item = r.json()["item"]
    r = cliente.post(f"/api/items/{item['id']}/mediciones", json={
        "n": "1", "largo": "5", "ancho": "3", "alto": "2.4",
    })
    assert r.status_code == 422
    assert "dimensional" in r.json()["detail"].lower()


def test_pegado_desde_excel(cliente, proyecto):
    r = cliente.post(f"/api/proyectos/{proyecto['id']}/items", json={
        "tipo": "partida", "descripcion": "Tarrajeo de prueba", "unidad": "m2",
    })
    item = r.json()["item"]
    texto = "Eje A\t1\t\t12.40\t\t2.60\nEje B\t1\t\t8.20\t\t2.60\nsin datos\t\t\t\t\t"
    r = cliente.post(f"/api/items/{item['id']}/mediciones/pegar", json={"texto": texto})
    datos = r.json()
    assert datos["creadas"] == 2
    assert len(datos["rechazadas"]) == 1
    assert datos["resumen"]["total"] == "53.56"     # 32.24 + 21.32


def test_repetir_filas_en_varios_niveles(cliente, proyecto):
    pid = proyecto["id"]
    ubicaciones = cliente.get(f"/api/proyectos/{pid}/ubicaciones").json()["ubicaciones"]
    niveles = [n["id"] for n in ubicaciones[0]["hijos"] if n["tipo"] == "nivel"][:2]

    r = cliente.post(f"/api/proyectos/{pid}/items", json={
        "tipo": "partida", "descripcion": "Contrapiso de prueba", "unidad": "m2",
    })
    item = r.json()["item"]
    m = cliente.post(f"/api/items/{item['id']}/mediciones", json={
        "descripcion": "Piso típico", "n": "1", "largo": "10", "ancho": "8",
    }).json()

    r = cliente.post(f"/api/items/{item['id']}/mediciones/repetir", json={
        "medicion_ids": [m["medicion_id"]], "ubicacion_ids": niveles,
    })
    assert r.json()["creadas"] == 2
    assert r.json()["resumen"]["total"] == "240.00"   # 80 original + 80 × 2


def test_descuento_de_vanos_respeta_la_familia(cliente, proyecto):
    r = cliente.post(f"/api/proyectos/{proyecto['id']}/items", json={
        "tipo": "partida", "descripcion": "Piso cerámico de prueba", "unidad": "m2",
        "familia_descuento": "pisos",
    })
    item = r.json()["item"]
    r = cliente.post(f"/api/items/{item['id']}/vanos", json={
        "vanos": [
            {"descripcion": "Rejilla chica", "n": "1", "ancho": "0.40", "alto": "0.40"},
            {"descripcion": "Ducto", "n": "1", "ancho": "0.80", "alto": "0.80"},
        ],
        "insertar": True,
    })
    datos = r.json()
    assert datos["evaluados"][0]["aplica"] is False   # 0.16 m² < 0.25
    assert datos["evaluados"][1]["aplica"] is True    # 0.64 m² ≥ 0.25
    assert datos["creadas"] == 1


def test_control_de_calidad_detecta_partidas_sin_metrar(cliente, proyecto):
    datos = cliente.get(f"/api/proyectos/{proyecto['id']}/calidad").json()
    assert datos["resumen"]["total"] > 0
    tipos = {a["tipo"] for a in datos["alertas"]}
    assert "sin_metrado" in tipos
    for a in datos["alertas"]:
        assert a["solucion"], "toda alerta debe decir cómo se corrige"


def test_trazabilidad_devuelve_el_paso_a_paso(cliente, proyecto):
    hoja = cliente.get(f"/api/proyectos/{proyecto['id']}/metrados").json()
    partidas = [n for n in hoja["items"] if n["tipo"] == "partida" and n.get("n_mediciones")]
    assert partidas
    t = cliente.get(f"/api/items/{partidas[0]['id']}/trazabilidad").json()
    assert t["detalle"]
    assert t["detalle"][0]["sustento"]


@pytest.mark.parametrize("reporte", ["metrados", "resumen", "presupuesto", "trazabilidad"])
@pytest.mark.parametrize("formato", ["xlsx", "csv", "pdf"])
def test_exportaciones_generan_archivo(cliente, proyecto, reporte, formato):
    r = cliente.get(
        f"/api/proyectos/{proyecto['id']}/exportar/{reporte}?formato={formato}")
    assert r.status_code == 200, r.text
    minimo = 90 if formato == "csv" else 900
    assert len(r.content) > minimo, f"{reporte}.{formato} salió vacío"
    if formato == "pdf":
        assert r.content[:4] == b"%PDF"
    if formato == "xlsx":
        assert r.content[:2] == b"PK"


def test_historial_registra_los_cambios(cliente, proyecto):
    datos = cliente.get(f"/api/proyectos/{proyecto['id']}/historial").json()
    acciones = {h["accion"] for h in datos["historial"]}
    assert "crear" in acciones
    assert all(h["frase"] for h in datos["historial"])


def test_asistente_no_modifica_sin_confirmacion(cliente, proyecto):
    r = cliente.post("/api/asistente", json={
        "texto": "crea una plantilla de metrados para una vivienda",
        "proyecto_id": proyecto["id"],
    }).json()
    acciones = r["acciones"]
    assert acciones and acciones[0]["requiere_confirmacion"] is True


def test_formula_maliciosa_no_se_evalua(cliente):
    r = cliente.post("/api/formula/validar", json={
        "expresion": "__import__('os').system('dir')",
    }).json()
    assert r["ok"] is False
