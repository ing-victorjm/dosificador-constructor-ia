# 02 — Reglas de cálculo verificables para metrar estructuras (concreto armado y acero)

> Documento de investigación para el motor de cálculo de **metra-ai**.
> Cada número lleva su fuente y URL. Los valores no confirmados en fuente primaria van marcados
> explícitamente como **[NO VERIFICADO]** y se replican con `"verificado": false` en
> `02-tablas-estructuras.json`.
>
> Fecha de compilación: 2026-09-02.

---

## 0. Fuentes primarias usadas (y PDF descargados)

| # | Documento | Uso | URL | Copia local en `docs/normas/` |
|---|---|---|---|---|
| F1 | **Norma Técnica “Metrados para Obras de Edificación y Habilitaciones Urbanas”** (aprobada por **RD N.º 073-2010-VIVIENDA/VMCS-DNC**) | Reglas de medición de concreto, encofrado, acero, albañilería y estructuras metálicas | https://www.gob.pe/institucion/vivienda (documento difundido por el MVCS; copia SPIJ) | `RD-073-2010-VIVIENDA-VMCS-DNC-SPIJ.pdf`, `RD-073-2010-Norma-Metrados-mirror.pdf` |
| F2 | **RNE Norma E.060 Concreto Armado** (D.S. 010-2009-VIVIENDA) | Ganchos, diámetros de doblado, longitudes de desarrollo, empalmes, recubrimientos, losas nervadas | http://blog.pucp.edu.pe/blog/wp-content/uploads/sites/109/2009/08/Norma-E.060-2009.pdf | `RNE-E060-Concreto-Armado-2009-PUCP.pdf` |
| F3 | **Propuesta de actualización E.060 (2019) — SENCICO/CIP** | Contraste de versiones | https://www.cip.org.pe/publicaciones/2021/enero/portal/e.060-concreto-armado-sencico.pdf | `Propuesta-E060-2019-SENCICO-CIP.pdf` |
| F4 | **Aceros Arequipa — Hoja técnica “Fierro Corrugado ASTM A615 Grado 60 / NTP 341.031”** (rev. QCQA01-F100/06/JUN19) | Tabla oficial de dimensiones y pesos nominales **incluyendo 6 mm y 8 mm** | https://acerosarequipa.com/sites/default/files/fichas/2020-07/HOJA%20TECNICA_FIERRO%20CORRUGADO-A615.pdf | `AcerosArequipa-HT-FIERRO-CORRUGADO-A615-2020.pdf` |
| F5 | **Aceros Arequipa — Hoja técnica “Fierro Corrugado BINORMA A615/A706”** (rev. QCQA01-F171/01/MAY 23, ed. 2024) | Confirma la misma tabla + área de 6 mm/8 mm con 2 decimales + 7/8" | https://acerosarequipa.com/sites/default/files/fichas/2024-08/FIERRO-CORRUGADO-BINORMA_PERU..pdf | `AcerosArequipa-HT-FIERRO-CORRUGADO-BINORMA-2024.pdf` |
| F6 | **Aceros Arequipa — Hoja técnica “Fierro Corrugado A615 Grado 60”** (rev. QCQA01–F100/08/SET 24) | Versión 2025 de la misma tabla (sin 6/8 mm) + diámetros de doblado de ensayo | https://acerosarequipa.com/sites/default/files/fichas/2025-06/HT%20BARRAS%20CORRUGADO%20A615.pdf | `AcerosArequipa-HT-BARRAS-CORRUGADO-A615.pdf` |
| F7 | **Aceros Arequipa — Catálogo de Productos y Servicios (2020)** | Diámetros comerciales, propiedades mecánicas, series métricas de otros países | https://acerosarequipa.com//sites/default/files/catalogo/2020-02/Catalogoproductosacerosarequipa.pdf | `AcerosArequipa-Catalogo-Productos-2020.pdf` |
| F8 | **Aceros Arequipa — Hoja técnica “Estribos Corrugados”** (QCQA01-F135/03/JUN18) | Estribos prefabricados: tipos, dimensiones y pesos por paquete | https://acerosarequipa.com/sites/default/files/fichas/2020-07/HOJA%20TECNICA%20ESTRIBOS%20CORRUGADOS.pdf | `AcerosArequipa-HT-ESTRIBOS-CORRUGADOS.pdf` |
| F9 | **INDOT Recurring Plan Detail 703-B-316d — “Bar Bending Details”** (consistente con **ACI 318-14** y **CRSI Manual of Standard Practice**) | Dimensiones de detallado de ganchos (Hook A, D, J, H) para el cuadro de acero | https://www.in.gov/dot/div/contracts/standards/rsp/sep21/700/703-B-316d%20211201.pdf | `INDOT-703-B-316d-Standard-Hooks-ACI.pdf` |
| F10 | **RNE Norma E.020 Cargas** (edición digital oficial SENCICO) | Peso propio de losas aligeradas y pesos unitarios de materiales | https://cdn.www.gob.pe/uploads/document/file/2366640/50%20E.020%20CARGAS.pdf · índice: https://www.gob.pe/institucion/sencico/informes-publicaciones/887225-normas-del-reglamento-nacional-de-edificaciones-rne | `RNE_E020_Cargas_SENCICO_oficial.pdf`, `RNE_E020_Cargas_gobpe.pdf` |
| F11 | **RNE Norma E.070 Albañilería** (ed. digital oficial SENCICO 2020, ISBN 978-612-48427-6-4) | Espesor de junta (Art. 4.1.2), Tabla 1 (clases), Tabla 4 (morteros) | (índice SENCICO en gob.pe, misma URL que F10) | `RNE_E070_Albanileria_SENCICO_oficial.pdf` — ⚠ la copia del CIP `RNE_E070_Albanileria_CIP_SENCICO.pdf` es la **propuesta**, no la vigente |
| F12 | **RNE Norma E.090 Estructuras Metálicas** | Aceros estructurales admitidos | (ver §6) | `RNE-E090-Estructuras-Metalicas.pdf` |
| F13 | **Aceros Arequipa — Manual del Maestro Constructor**, “Aportes de materiales” | Fórmulas y tablas de ladrillos/m², mortero/m², ladrillos de techo y concreto por m² de aligerado | https://www.acerosarequipa.com/manuales/manual-del-maestro-constructor/aportes-de-materiales | (páginas web + imágenes de tabla) |
| F15 | **Aceros Arequipa — hojas técnicas de perfiles**: Ángulos A36 (F103/06/AGO 23), Ángulo Dual A36/A572-G50 (F101/06/SEP 24), Canales U (F115/06/JUL 26 + F242/02/NOV 23), Tees (F105/05/DIC 23), Platinas (F104/05/SET 23), Barras Cuadradas (F109/07/SET 25), Barras Redondas Lisas y Pulidas (F106/08/JUL 26), Planchas Estriadas LAC (F211/05/SET 23), Tubo A500 LAC/GALV (F219/06/AGO 23) | Pesos kg/m y dimensiones de perfiles comerciales peruanos | https://acerosarequipa.com/ (rutas completas en §6.3) | `AcerosArequipa-HT-*.pdf`, `AcerosArequipa-FT-TUBO-*.pdf` |
| F16 | **Aceros Arequipa — Catálogo de Productos y Servicios Perú, ed. 2026-01** | Vigas WF (lb/pie), planchas LAC, espesores comerciales | https://acerosarequipa.com/sites/default/files/catalogo/2026-01/Catalogodeproductos_Per%C3%BA.pdf | `AcerosArequipa-Catalogo-Productos-Peru.pdf`, `…-2026.pdf` |
| F17 | **AISC Shapes Database v15.0** (nov-2017) | Perfiles W, C, L: kg/m, área, dimensiones y perímetro PB para pintura | https://github.com/ambaker1/aisc-csv (espejo público del .xlsx original de AISC; aisc.org bloquea el acceso automatizado) | `AISC-Shapes-Database-v15.0.xlsx` |
| F18 | **RNE Norma E.090 Estructuras Metálicas** (*El Peruano*, 10-jun-2006) | Aceros ASTM admitidos (§1.3.1a), tamaño mínimo de filete (Tabla 10.2.4) | https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo3/02_E/RNE2006_E_090.pdf | `RNE-E090-Estructuras-Metalicas.pdf` |
| F14 | **Fichas técnicas de ladrilleras peruanas** — Pirámide (KK 18 Hércules v03, KK 18 huecos, KK 30 %, Estructural 9, Pandereta Raya, Tabicón 15, Bloqueta 12, Hueco 12/15/20), Lark (KK 18 huecos, Pandereta Acanalada), Maxx, Fortes | Dimensiones reales y rendimientos por junta | https://www.ladrillospiramide.com/productos/ · https://ladrilloslark.pe/FichasTecnicas/KK.pdf · https://ladrillosmaxx.com/ · https://www.ladrillosfortes.com/ | `FichaTecnica_Piramide_*.pdf`, `FichaTecnica_Lark_*.pdf` |

**Aviso de trazabilidad:** el PDF `RD-073-2010-VIVIENDA-VMCS-DNC-SPIJ.pdf` es una redifusión que lleva
un pie de página añadido por un tercero (`waltervillavicencio.com/metrados`). El **texto normativo**
coincide con la norma; se conserva además una segunda copia (`…-mirror.pdf`). Antes de publicar
comercialmente conviene sustituirlo por la copia servida por el MVCS.

---

## 1. ACERO DE REFUERZO

### 1.1 Pesos y áreas unitarias — sistema en pulgadas y mm (Perú)

Tabla **oficial del fabricante** (F4 y F5, idénticas). Es la que rige en obra en el Perú porque
NTP 341.031 y ASTM A615 fijan la **masa nominal**, no la derivan del área.

| Denominación | Ø nominal (mm) | Sección (mm²) | Sección (cm²) | Perímetro (mm) | **Peso (kg/m)** | Fuente |
|---|---|---|---|---|---|---|
| 6 mm | 6,00 | 28 (28,54 en F5) | 0,283 | 18,8 | **0,222** | F4, F5 |
| 8 mm | 8,00 | 50 (50,27 en F5) | 0,503 | 25,1 | **0,395** | F4, F5 |
| 3/8" | 9,525 | 71 | 0,71 | 29,9 | **0,560** | F4, F5, F6 |
| 12 mm | 12,00 | 113 | 1,13 | 37,7 | **0,888** | F4, F5, F6 |
| 1/2" | 12,70 | 129 | 1,29 | 39,9 | **0,994** | F4, F5, F6 |
| 5/8" | 15,875 | 199 | 1,99 | 49,9 | **1,552** | F4, F5, F6 |
| 3/4" | 19,05 | 284 | 2,84 | 59,8 | **2,235** | F4, F5, F6 |
| 7/8" | 22,225 | 387 | 3,87 | 69,8 | **3,042** | F4, F5, F6 |
| 1" | 25,40 | 510 | 5,10 | 79,8 | **3,973** | F4, F5, F6 |
| 1 3/8" | **35,81** (ver nota) | 1006 | 10,06 | 112,5 | **7,907** | F4, F5, F6 |

**Nota crítica para el motor de cálculo (1 3/8"):** la denominación comercial dice 1 3/8" = 34,925 mm,
pero el área (1006 mm²) y el perímetro (112,5 mm) del catálogo corresponden a **Ø = 35,81 mm**, que es
la barra **ASTM #11** (1,410 in). Si el motor calcula `db` desde la fracción de pulgada obtendrá
34,925 mm y se equivocará ~2,5 % en todo lo que dependa de `db` (ganchos, traslapes, ld). **Usar
35,81 mm.** Comprobación: `π/4 · 35,81² = 1007 mm²` ✔; `112,5/π = 35,81` ✔.

Comprobación cruzada de los demás diámetros (perímetro/π = Ø): 29,9/π = 9,52 ✔ · 39,9/π = 12,70 ✔ ·
49,9/π = 15,88 ✔ · 59,8/π = 19,03 ✔ · 69,8/π = 22,22 ✔ · 79,8/π = 25,40 ✔ · 18,8/π = 5,98 ✔ ·
25,1/π = 7,99 ✔ · 37,7/π = 12,00 ✔.

**Longitudes comerciales:** barras de **9 m y 12 m**; se suministra en paquetes de 2 t y en varillas (F4, F5, F7).

**Propiedades mecánicas (F4 — A615 G60 / NTP 341.031 G420):**
fy ≥ 420 MPa (4 280 kg/cm²) · R ≥ 620 MPa (6 320 kg/cm²) · R/fy ≥ 1,25 · doblado 180° bueno en todos
los diámetros. La versión 2025 (F6) declara **fy = 420–540 MPa** y **R ≥ 550 MPa** (armonizado con
ASTM A615-24 / A706).

### 1.2 Serie métrica Ø6 … Ø32

En el Perú Aceros Arequipa solo produce **6, 8 y 12 mm** de la serie métrica (F4). La serie completa
Ø6–Ø32 sí se produce en Bolivia bajo NB 732-500: **6, 8, 9.5, 12, 16, 20, 25, 32 mm** (F7, pág. 5),
pero el catálogo no publica sus pesos.

Los pesos de la serie métrica se obtienen de la **masa teórica** con ρ = 7 850 kg/m³:

```
m [kg/m] = (π/4) · d²[mm²] · 7850 · 1e-6  =  0,0061654 · d²[mm]
A [mm²]  = (π/4) · d²
```

| Ø (mm) | Área (mm²) | **Peso (kg/m)** | ¿Verificado en catálogo? |
|---|---|---|---|
| 6 | 28,27 | 0,222 | **Sí** (F4/F5) |
| 8 | 50,27 | 0,395 | **Sí** (F4/F5) |
| 10 | 78,54 | 0,617 | **No** — derivado |
| 12 | 113,10 | 0,888 | **Sí** (F4/F5) |
| 16 | 201,06 | 1,578 | **No** — derivado |
| 20 | 314,16 | 2,466 | **No** — derivado |
| 25 | 490,87 | 3,853 | **No** — derivado |
| 32 | 804,25 | 6,313 | **No** — derivado |

**[NO VERIFICADO]** los valores de Ø10, Ø16, Ø20, Ø25 y Ø32 no se confirmaron contra una hoja técnica
de fabricante peruano; son la masa teórica exacta (coinciden con ISO 6935-2 / EN 10080, que es lo que
usa toda la industria).

> Cuidado con mezclar series: la barra **ASTM A615M** “soft-metric” usa otras denominaciones
> (No. 10 = 9,5 mm = 0,560 kg/m; No. 13 = 12,7 mm = 0,994; No. 16 = 15,9 = 1,552; No. 19 = 19,1 =
> 2,235; No. 22 = 22,2 = 3,042; No. 25 = 25,4 = 3,973; No. 36 = 35,8 = 7,907). Es la **misma barra en
> pulgadas** con nombre métrico, no la serie ISO Ø6–Ø32.

### 1.3 Ganchos estándar — E.060 Cap. 7 (idéntico a ACI 318)

**E.060 7.1 — Gancho estándar** (F2, pág. 51):

| Tipo | Doblez | Extensión recta hasta el extremo libre | Norma |
|---|---|---|---|
| Barra longitudinal, gancho 180° | 180° | **4 db, pero no menor de 65 mm** | E.060 7.1.1 |
| Barra longitudinal, gancho 90° | 90° | **12 db** | E.060 7.1.2 |
| Estribo / grapa, barras ≤ 5/8" | 90° | **6 db** | E.060 7.1.3(a) |
| Estribo / grapa, barras 3/4" a 1" | 90° | **12 db** | E.060 7.1.3(b) |
| Estribo / grapa, barras ≤ 1" | 135° | **6 db** | E.060 7.1.3(c) |
| **Gancho sísmico** (estribos de confinamiento y grapas) | **135° o más** | **8 db, pero no menor de 75 mm** | E.060 21.1 (F2, pág. 165) |

Grapa suplementaria: refuerzo transversal de **Ø mínimo 8 mm** con ganchos sísmicos en ambos extremos (E.060 21.1).

**E.060 7.2 — Diámetros interiores mínimos de doblado (Tabla 7.1)**:

| Diámetro de barra | Diámetro mínimo de doblado (interior) |
|---|---|
| 1/4" a 1" | **6 db** |
| 1 1/8" a 1 3/8" | **8 db** |
| 1 11/16" a 2 1/4" | **10 db** |

- **Estribos**: el diámetro interior de doblado **no menor de 4 db** para barras de **5/8" y menores**;
  para mayores rige la Tabla 7.1 (E.060 7.2.2).
- Malla electrosoldada para estribos: ≥ 4 db si el alambre corrugado es > 7 mm; ≥ 2 db si es menor (E.060 7.2.3).
- Todo el refuerzo se dobla **en frío** (E.060 7.3.1).

**Concordancia con ACI 318:** los diámetros de doblado de E.060 Tabla 7.1 coinciden con ACI 318
Tabla 25.3.1 (6 db para #3–#8, 8 db para #9–#11, 10 db para #14 y #18), y las extensiones 12 db (90°)
y 4 db / 65 mm (180°) son idénticas. **Diferencia:** ACI 318-19 exige además que la extensión del
gancho de estribo de 90°/135° no sea menor de **75 mm** (Tabla 25.3.2); E.060 solo fija ese mínimo
para el **gancho sísmico** (8 db ≥ 75 mm). Corroboración externa de la geometría ACI/CRSI en F9.

**Diámetros de doblado del ensayo de doblado** (no confundir con los de fabricación — F4/F6):
6 mm → 18 mm (3d) · 8 mm → 24 (3d) · 3/8" → 28,6 (3d) · 12 mm → 36 (3d) · 1/2" → 38,1 (3d) ·
5/8" → 47,6 (3d) · 3/4" → 95,3 (5d) · 7/8" → 111,1 (5d) · 1" → 127 (5d) · 1 3/8" → 244,5 (7d).

### 1.4 Longitud desarrollada de los ganchos (lo que suma el gancho al corte de la barra)

Esto es **geometría pura** a partir de los parámetros normativos; es exacto y auditable.
Sea `D = k·db` el diámetro interior de doblado y `R = (D + db)/2 = (k+1)·db/2` el radio del **eje**
de la barra.

```
arco(θ) = θ_rad · R = θ_rad · (k+1)·db/2
tangente (solo para 90°) = R = (k+1)·db/2
```

| Gancho | k (E.060) | Arco del eje | Extensión | **Longitud añadida desde el punto de tangencia** | **Longitud añadida desde la intersección de ejes** |
|---|---|---|---|---|---|
| 90° barra longitudinal | 6 | 5,498 db | 12 db | **17,50 db** | **14,00 db** |
| 180° barra longitudinal | 6 | 10,996 db | 4 db (≥65 mm) | **15,00 db** | — |
| 135° estribo ≤ 5/8" (sísmico, ext. 8 db) | 4 | 5,890 db | 8 db (≥75 mm) | **13,89 db** | — |
| 135° estribo ≤ 5/8" (ext. 6 db) | 4 | 5,890 db | 6 db | **11,89 db** | — |
| 90° estribo ≤ 5/8" (ext. 6 db) | 4 | 3,927 db | 6 db | **9,93 db** | **7,43 db** |

> Regla práctica que sale de aquí y conviene programar: **cada doblez de 90° “acorta” 0,4292·R**
> respecto de medir hasta la intersección de los ejes (2R − πR/2). Es la “deducción por doblez” de la
> planilla de fierros.

**Dimensiones de detallado tipo CRSI/ACI** (F9 — INDOT 703-B-316d, “consistent with ACI 318-14 and
CRSI Manual of Standard Practice”; todas las dimensiones de los diagramas de doblado se miden
**out-to-out**):

*Ganchos de extremo estándar*

| Barra | Ø equiv. | D | Gancho 180° “A” | 180° “J” | Gancho 90° “A” |
|---|---|---|---|---|---|
| #3 | 3/8" | 2 1/4" | 5" | 3" | 6" |
| #4 | 1/2" | 3" | 6" | 4" | 8" |
| #5 | 5/8" | 3 3/4" | 7" | 5" | 10" |
| #6 | 3/4" | 4 1/2" | 8" | 6" | 1'-0" |
| #7 | 7/8" | 5 1/4" | 10" | 7" | 1'-2" |
| #8 | 1" | 6" | 11" | 8" | 1'-4" |
| #9 | 1 1/8" | 9 1/2" | 1'-3" | 11 3/4" | 1'-7" |
| #10 | 1 1/4" | 10 3/4" | 1'-5" | 1'-1 1/4" | 1'-10" |
| #11 | 1 3/8" | 12" | 1'-7" | 1'-2 3/4" | 2'-0" |
| #14 | 1 3/4" | 18 1/4" | 2'-3" | 1'-9 3/4" | 2'-7" |
| #18 | 2 1/4" | 24" | 3'-0" | 2'-4 1/2" | 3'-5" |

*Ganchos de estribo / sísmicos*

| Barra | D | 135° “A” | H (aprox.) | 90° “A” |
|---|---|---|---|---|
| #3 | 1 1/2" | 4 1/4" | 3" | 4" |
| #4 | 2" | 4 1/2" | 3" | 4 1/2" |
| #5 | 2 1/2" | 5 1/2" | 3 3/4" | 6" |
| #6 | 4 1/2" | 8" | 4 1/2" | 1'-0" |
| #7 | 5 1/4" | 9" | 5 1/4" | 1'-2" |
| #8 | 6" | 10 1/2" | 6" | 1'-4" |

Fórmulas que reproducen **exactamente** la tabla de *ganchos de extremo estándar* (verificadas contra
las 11 filas), útiles para generalizarla a cualquier diámetro:

```
A(90°)  = D/2 + db + 12·db
A(180°) = D  + db + máx(4·db ; 2,5")
J(180°) = D  + 2·db
```
donde `D` es el diámetro interior de doblado ya “terminado” (incluye recuperación elástica) y todas las
dimensiones son **out-to-out**. Ejemplo #8: D = 6", db = 1" → A(90°) = 3 + 1 + 12 = 16" = 1'-4" ✔;
A(180°) = 6 + 1 + 4 = 11" ✔; J = 6 + 2 = 8" ✔.

### 1.5 Longitud de desarrollo (ld) — E.060 Cap. 12

**Tracción, caso favorable (E.060 Tabla 12.1)** — unidades SI (MPa, mm):

```
Alambres corrugados y barras de 3/4" y menores:   ld = ( fy·ψt·ψe·λ / (2,6·√f'c) ) · db
Barras mayores de 3/4":                            ld = ( fy·ψt·ψe·λ / (2,1·√f'c) ) · db
ld ≥ 300 mm                                        (E.060 12.2.1)
√f'c ≤ 8,3 MPa                                     (E.060 12.1.2)
```

Condición para usar la Tabla 12.1: espaciamiento libre ≥ db y recubrimiento libre ≥ db **con** estribos
mínimos según 11.5.6; o bien espaciamiento libre ≥ 2 db y recubrimiento libre ≥ db. En cualquier otro
caso rige la ecuación general **(12-1)**:

```
ld = ( 1/1,1 ) · ( fy / √f'c ) · ( ψt·ψe·ψs·λ / ((cb + Ktr)/db) ) · db     con (cb+Ktr)/db ≤ 2,5
Ktr = Atr·fyt / (10·s·n)          (se permite Ktr = 0)
```

**Factores (E.060 Tabla 12.2):**

| Factor | Condición | Valor |
|---|---|---|
| ψt | Barras superiores (≥ 300 mm de concreto fresco debajo) | **1,3** |
| ψt | Otras barras | 1,0 |
| ψe | Epóxico con recub. < 3 db o espaciamiento libre < 6 db | 1,5 |
| ψe | Otras barras con epóxico | 1,2 |
| ψe | Sin tratamiento superficial | 1,0 |
| ψs | Barras de 3/4" y menores | **0,8** |
| ψs | Barras mayores de 3/4" | 1,0 |
| λ | Concreto liviano | **1,3** |
| λ | Concreto de peso normal | 1,0 |
| — | ψt · ψe ≤ **1,7** | — |

> ⚠️ **Ojo con λ.** En E.060 λ está en el **numerador** y vale **1,3** para concreto liviano; en
> ACI 318 λ está en el **denominador** y vale 0,75. Ambos aumentan ld en liviano, pero **no son
> intercambiables**: si el motor usa la formulación de E.060, λ = 1,0 / 1,3.
>
> ⚠️ **Diferencia real E.060 ↔ ACI 318.** ACI 318-08/-14 (SI) usa coeficientes **2,1** (barras ≤ No.19)
> y **1,7** (barras ≥ No.22) en la tabla equivalente, con ψs ya incorporado. E.060 usa **2,6** y **2,1**.
> El 2,6 = 2,1/0,8 (coherente: incorpora ψs = 0,8 para barras chicas). Pero el **2,1 para barras
> mayores de 3/4"** equivale a aplicar también ψs = 0,8 a barras grandes, que ACI **no** permite: **E.060
> da ld ≈ 19 % menor que ACI para barras > 3/4"**. Recomendación para el motor: exponer una opción
> `norma: "E.060" | "ACI318"` y advertirlo en el reporte.

**Ganchos estándar en tracción (E.060 12.5):**

```
ldg = ( 0,24 · ψe · λ · fy / √f'c ) · db      [MPa, mm]
ψe = 1,2 (epóxico), λ = 1,3 (liviano), en otro caso 1,0
```
Mínimo: E.060 12.5.1 dice literalmente “no debe ser menor que **el menor** valor entre 8 db y 150 mm”.
**Esto es un error de redacción respecto de ACI 318 12.5.1, que exige “not less than 8 db and 150 mm”
(el mayor).** Para el motor usar **máx(8 db; 150 mm)** y dejar constancia.
Reducciones (12.5.3): ×0,7 con recubrimiento lateral ≥ 65 mm (y ≥ 50 mm más allá del gancho en 90°);
×0,8 si el gancho está confinado por estribos a ≤ 3 db. **Los ganchos no anclan barras en compresión** (12.5.4).

**Compresión (E.060 12.3):**
```
ldc = máx( 0,24·fy/√f'c · db ;  0,043·fy·db )   ≥ 200 mm
```
Reducciones: ×(As req/As prop); ×0,75 si está confinado por espiral Ø ≥ 1/4" con paso ≤ 100 mm o
estribos Ø 1/2" a ≤ 100 mm.

**Paquetes de barras (12.4):** ld individual **+20 %** en paquete de 3 barras, **+33 %** en paquete de 4.

### 1.6 Empalmes por traslape — E.060 Cap. 12

**Tracción (12.15):**
```
Clase A = 1,0 · ld        Clase B = 1,3 · ld        siempre ≥ 300 mm
```
`ld` se calcula según 12.2 para desarrollar fy, **sin** el factor de refuerzo en exceso (12.2.5).

**Tabla 12.3 — cuándo es Clase A y cuándo Clase B:**

| As proporcionado / As requerido en la zona de empalme | % máx. de As empalmado en la longitud requerida: **50 %** | **100 %** |
|---|---|---|
| ≥ 2 | **Clase A** | **Clase B** |
| < 2 | **Clase B** | **Clase B** |

**Compresión (12.16.1):**
```
fy ≤ 420 MPa:   l_traslape = 0,071 · fy · db          (= 29,8 db para fy = 420 MPa)
fy > 420 MPa:   l_traslape = (0,13·fy − 24) · db
mínimo 300 mm;  ×1,3 si f'c < 21 MPa
```

**Restricciones de ubicación (afectan el cómputo real de traslapes):**
- Barras **mayores de 1 3/8"** — **no se permite empalme por traslape** (12.14.2.1).
- Vigas sismorresistentes (21.5.2.3): **no** se permite traslape (a) dentro de los nudos,
  (b) a menos de **2·h** (dos veces el peralte) de la cara del nudo, (c) donde el análisis indique
  fluencia por flexión. Además exige estribos de confinamiento en toda la longitud del empalme
  con espaciamiento ≤ mín(d/4; 150 mm).
- Columnas sismorresistentes (21.6.3.2): los traslapes **solo dentro de la mitad central** de la
  altura del elemento, diseñados como traslape en tracción y rodeados de refuerzo transversal.
- Columnas en general (12.17.2.4): si los estribos en toda la longitud del traslape tienen
  área efectiva ≥ 0,0015·h·s, se puede multiplicar la longitud del traslape por **0,83** (≥ 300 mm);
  con espirales, por **0,75** (≥ 300 mm).
- Empalmes mecánicos o soldados deben desarrollar ≥ **1,25 fy** (12.14.3.2 / 12.14.3.4).

### 1.7 Tablas numéricas listas para uso (fy = 4 200 kg/cm² = 420 MPa, concreto normal, sin epóxico)

Coeficientes equivalentes en kg/cm² (derivados exactamente de las fórmulas de E.060 con
1 kg/cm² = 0,0980665 MPa):

```
ld (≤3/4")  = fy / (8,3025 · √f'c) · db        [fy, f'c en kg/cm²; db y ld en la misma unidad]
ld (>3/4")  = fy / (6,7078 · √f'c) · db
ldg         = 0,07516 · fy / √f'c · db
ldc         = máx( 0,07516·fy/√f'c ; 0,004217·fy ) · db
```

**Múltiplos de db** (antes de aplicar mínimos):

| f'c (kg/cm²) | ld ≤3/4" inferior | ld ≤3/4" superior (ψt=1,3) | ld >3/4" inferior | ld >3/4" superior | ldg | ldc | traslape compresión |
|---|---|---|---|---|---|---|---|
| 175 | 38,2 db | 49,7 db | 47,3 db | 61,5 db | 23,9 db | 23,9 db | **38,8 db** (×1,3) |
| **210** | **34,9 db** | **45,4 db** | **43,2 db** | **56,2 db** | **21,8 db** | **21,8 db** | **29,8 db** |
| 245 | 32,3 db | 42,0 db | 40,0 db | 52,0 db | 20,2 db | 20,2 db | 29,8 db |
| 280 | 30,2 db | 39,3 db | 37,4 db | 48,6 db | 18,9 db | 18,9 db | 29,8 db |
| 350 | 27,0 db | 35,1 db | 33,5 db | 43,5 db | 16,9 db | 17,7 db | 29,8 db |
| 420 | 24,7 db | 32,1 db | 30,6 db | 39,7 db | 15,4 db | 17,7 db | 29,8 db |

*Traslape en compresión = 0,071·fy·db con fy = 420 MPa → 29,8 db; **×1,3 si f'c < 21 MPa** (E.060
12.16.1). El caso f'c = 210 kg/cm² = 20,6 MPa está en el filo: el RNE lo trata como el grado nominal
de 21 MPa, así que **no** se aplica el ×1,3 a 210; sí a 175.*

> Traslape **Clase B = 1,3 × ld**. Para el caso más común (f'c = 210, barras ≤ 3/4", inferiores) da
> **45,4 db**, que es exactamente el origen de la regla de obra peruana *“traslape = 45 db”*. Para
> barras superiores sube a **59,0 db** (≈ 60 db).

**Longitudes en cm, f'c = 210 kg/cm², fy = 4 200 kg/cm²** (ya con los mínimos ld ≥ 30 cm,
traslape ≥ 30 cm, ldg ≥ máx(8 db; 15 cm)):

| Barra | db (mm) | ld inferior | ld superior | Traslape B inferior | Traslape B superior | ldg (gancho) |
|---|---|---|---|---|---|---|
| 6 mm | 6,00 | 30 cm | 30 cm | 30 cm | 35 cm | 15 cm |
| 8 mm | 8,00 | 30 cm | 36 cm | 36 cm | 47 cm | 17 cm |
| 3/8" | 9,525 | 33 cm | 43 cm | 43 cm | 56 cm | 21 cm |
| 12 mm | 12,00 | 42 cm | 54 cm | 54 cm | 71 cm | 26 cm |
| 1/2" | 12,70 | 44 cm | 58 cm | 58 cm | 75 cm | 28 cm |
| 5/8" | 15,875 | 55 cm | 72 cm | 72 cm | 94 cm | 35 cm |
| 3/4" | 19,05 | 67 cm | 86 cm | 86 cm | 112 cm | 41 cm |
| 7/8" | 22,225 | 96 cm | 125 cm | 125 cm | 162 cm | 48 cm |
| 1" | 25,40 | 110 cm | 143 cm | 143 cm | 185 cm | 55 cm |
| 1 3/8" | 35,81 | 155 cm | 201 cm | 201 cm | 261 cm | 78 cm |

**Longitudes en cm, f'c = 280 kg/cm²:**

| Barra | ld inferior | ld superior | Traslape B inferior | Traslape B superior | ldg |
|---|---|---|---|---|---|
| 3/8" | 30 cm | 37 cm | 37 cm | 49 cm | 18 cm |
| 1/2" | 38 cm | 50 cm | 50 cm | 65 cm | 24 cm |
| 5/8" | 48 cm | 62 cm | 62 cm | 81 cm | 30 cm |
| 3/4" | 58 cm | 75 cm | 75 cm | 97 cm | 36 cm |
| 7/8" | 83 cm | 108 cm | 108 cm | 141 cm | 42 cm |
| 1" | 95 cm | 124 cm | 124 cm | 161 cm | 48 cm |
| 1 3/8" | 134 cm | 174 cm | 174 cm | 226 cm | 68 cm |

*(Las tablas completas, en JSON, están en `02-tablas-estructuras.json`.)*

### 1.8 Recubrimientos mínimos (E.060 7.7.1) — necesarios para dimensionar estribos y ganchos

| Situación | Recubrimiento mínimo |
|---|---|
| Concreto vaciado contra el suelo y permanentemente expuesto a él | **70 mm** |
| En contacto permanente con suelo o intemperie — barras ≥ 3/4" | 50 mm |
| En contacto permanente con suelo o intemperie — barras ≤ 5/8" y mallas | 40 mm |
| No expuesto — losas, muros, viguetas — barras ≤ 1 3/8" | **20 mm** |
| No expuesto — losas, muros, viguetas — barras 1 11/16" y 2 1/4" | 40 mm |
| No expuesto — **vigas y columnas** (armadura principal, estribos y espirales) | **40 mm** |
| Cáscaras y losas plegadas — barras ≥ 3/4" | 20 mm |
| Cáscaras y losas plegadas — barras ≤ 5/8" y mallas | 15 mm |

Espaciamiento libre mínimo entre barras paralelas de una capa: **db, pero no menor de 25 mm** (E.060 7.6.1).

De aquí sale la fórmula del estribo cerrado rectangular:
```
a = b_col − 2·rec − 2·db_estribo          (dimensión out-to-out del estribo, si "rec" es al estribo)
Longitud desarrollada = 2(a + b) − 4·0,4292·R + 2·(longitud añadida por gancho)
   con R = (k+1)·db_estribo/2,  k = 4 para estribos ≤ 5/8"
```

### 1.9 Desperdicio de acero: qué dice la norma y qué se usa en la práctica

**Lo que sí es normativo (F1, OE.2.3, “Obras de Concreto Armado”, pág. 32-33):**

> «Para la armadura de acero se computa el peso total del fierro indicado en los planos. El cálculo
> se hará determinando primero la longitud de cada elemento **incluyendo los ganchos, dobleces y
> traslapes de varillas**. Luego se suman todas las longitudes agrupándose por diámetros iguales y se
> multiplican los resultados obtenidos por sus pesos unitarios correspondientes, expresados en kilos
> por metro (kg/m).»
>
> «El cómputo de la armadura de acero **no incluye los sobrantes de las barras (desperdicios),
> alambres, espaciadores, accesorios de apoyo ni desperdicios**, los mismos que irán como parte
> integrante de los **análisis de precios**, los que incluirán también la habilitación (corte y
> doblado) y colocación de la armadura.»

**Consecuencia de diseño para el motor:** el **metrado** (kg) es peso teórico neto; el **desperdicio**
se aplica en el **análisis de precios unitarios (APU)** como un factor sobre el insumo, nunca sobre la
partida metrada. El motor debe llevarlos en campos separados: `peso_metrado_kg` y
`factor_desperdicio` (solo APU).

**Justificación física del desperdicio:** las barras vienen en **9 m y 12 m** (F4). Toda pieza cuya
longitud desarrollada no sea divisor de 9 000 mm o 12 000 mm deja un retazo (“despunte”) que rara vez
se reutiliza; a eso se suma el traslape adicional cuando la pieza excede la barra comercial, y las
pérdidas de habilitación. Por eso el desperdicio **crece con el diámetro** (barras gruesas = piezas
largas y retazos más pesados) — un motor serio puede calcular el desperdicio **real** por
*nesting*/optimización de corte sobre barras de 9 m y 12 m, en vez de aplicar un porcentaje plano.

**Porcentajes de uso corriente (CAPECO, *Costos y Presupuestos en Edificación*, cuadro
“Proporciones y desperdicios en construcción”):** 3 % para Ø 3/8"; 5 % para Ø 1/2"; 7 % para Ø 5/8";
8 % para Ø 3/4"; 10 % para Ø 1".
**[NO VERIFICADO]** — estos valores circulan de forma consistente en material docente peruano y en
resúmenes del cuadro CAPECO, pero **no se logró abrir el cuadro original de CAPECO** (la publicación
no es de libre descarga; las copias en Scribd/Studocu/Academia no son fuentes admisibles). Se marcan
`"verificado": false`. El valor único de **5 %** para todo el acero es el más usado en presupuestos
públicos peruanos y también queda **[NO VERIFICADO]**.

### 1.10 Cómo se arma el “cuadro de acero” (planilla de fierros)

Estructura mínima, derivada del procedimiento que impone F1 (OE.2.3) y de la práctica de detallado
CRSI/ACI (F9):

| Campo | Contenido | Origen |
|---|---|---|
| `elemento` | Zapata Z-1, Columna C-2, Viga V-101, Losa… | Planos |
| `marca` | Identificador único de la barra (p. ej. `1`, `2`, `E-1`) | Práctica CRSI: nota 3 de F9 |
| `tipo_doblez` | Recta / L (1 gancho 90°) / U / Z / estribo cerrado / grapa | Catálogo de formas |
| `diametro` | 3/8", 1/2", … | Planos |
| `dimensiones_parciales` | a, b, c… **medidas out-to-out** (nota 1 de F9) | Planos |
| `longitud_desarrollada` | Σ tramos − deducciones por doblez + ganchos + traslapes | §1.4 y F1 |
| `cantidad` | N.º de barras iguales | Planos |
| `longitud_total` | `longitud_desarrollada × cantidad` | — |
| `peso_unitario` | kg/m de la tabla §1.1 | F4/F5 |
| `peso_total` | `longitud_total × peso_unitario` | F1 |

Reglas de agrupación que exige F1:
1. Sumar longitudes **por diámetro igual**, multiplicar por el peso unitario y recién ahí sumar los
   pesos parciales para obtener el total.
2. **Incluir** ganchos, dobleces y traslapes en la longitud de cada elemento.
3. **No incluir** desperdicios, alambre de amarre, espaciadores ni accesorios.

Reglas de **frontera entre elementos** (quién se lleva el acero) — F1, OE.2.3:

| Elemento | ¿Se computa el acero que “sale” hacia otro elemento? |
|---|---|
| **Cimientos reforzados** | **No** incluye vástagos ni arranques de columnas (OE.2.3.1) |
| **Zapatas** | **No** incluye arranques ni anclajes de columnas; en zapatas conectadas, **no** incluye las vigas de cimentación (OE.2.3.2) |
| **Vigas de cimentación** | **No** incluye vástagos de columnas ni de otros elementos empotrados (OE.2.3.3) |
| **Losas de cimentación** | **No** incluye vástagos de columnas ni de otros elementos empotrados (OE.2.3.4) |
| **Sobrecimientos reforzados** | **No** incluye armadura de otros elementos empotrados (OE.2.3.5) |
| **Muros de contención** | **Sí** incluye las barras que van empotradas en otros elementos (OE.2.3.6.1) |
| **Pantallas, barandas** | **Sí** incluye la parte empotrada en los apoyos (OE.2.3.6.3) |
| **Columnas** | **Sí** incluye las longitudes empotradas en otros elementos (zapatas, vigas…) (OE.2.3.7) |
| **Vigas** | **Sí** incluye la longitud de las barras empotradas en los apoyos (OE.2.3.8) |
| **Losas (macizas, aligeradas, nervadas)** | **Sí** incluye las barras empotradas en los apoyos; en aligerados con viguetas prefabricadas, **sí** incluye la armadura de temperatura y los bastones (OE.2.3.9.x) |
| **Escaleras** | **Sí** incluye tramos, descansos y los anclajes en otras estructuras (OE.2.3.10) |
| **Cajas de ascensor / cisternas / tanques** | **Sí** incluye la de muros y losas más los anclajes (OE.2.3.11 a .13) |

> Esta tabla es la que evita el doble conteo. El criterio general es: **el acero que arranca de la
> cimentación se carga a la columna/muro, no a la zapata.**

---

## 2. CONCRETO — reglas de medición (F1)

### 2.0 Reglas generales (F1, OE.2.3)

- Para cada elemento se indica su calidad por **f'c a 28 días**; se metra por separado cada f'c.
- En estructuras compuestas (cisternas, tanques, escaleras, pórticos) **el cálculo se hace por
  separado para cada elemento integrante** y luego se agrupa en las partidas de concreto, encofrado y
  armadura.
- Unidad: **m³** para concreto; **m²** para encofrado; **kg** para acero; **und** para ladrillos de techo.

### 2.1 Concreto simple (F1, OE.2.2)

| Elemento | Unidad | Regla de medición |
|---|---|---|
| **Cimientos corridos** | m³ | Suma del volumen de cada tramo. **En tramos que se cruzan, la intersección se mide una sola vez.** |
| **Sub-zapatas / falsa zapata** | m³ + m² | Suma de volúmenes; encofrado = área de contacto con el concreto |
| **Solados** | **m²** | Área efectiva **contada hasta 5 cm por fuera de la cara vertical** del elemento estructural que va encima |
| **Bases de concreto** | m³ + m² | Volumen real según geometría; encofrado = área efectiva |
| **Sobrecimientos** | m³ + m² | Suma por tramo; intersecciones **una sola vez**; **no incluye el volumen de la base de la columna** |
| **Gradas** | m³ + m² | Volumen efectivamente vaciado considerando el perfil de los pasos. Encofrado = contrapasos y costados. Si la sección es constante, se admite computar en **m** (la unidad ya incluye concreto + encofrado) |
| **Rampas** | **m²** (indicando espesor) + m² | Área real total, clasificada por espesor y calidad de concreto |
| **Falso piso** | **m²** | Superficie entre **caras interiores de muros o sobrecimientos sin revestir**; separar por espesores |

### 2.2 Concreto armado (F1, OE.2.3)

| Elemento | Regla de volumen |
|---|---|
| **Cimientos reforzados** | Igual que cimientos corridos (intersecciones una sola vez) |
| **Zapatas** | Según la forma geométrica de la zapata |
| **Vigas de cimentación** | Suma de volúmenes de cada viga |
| **Losas de cimentación** | Área total × espesor. **Las nervaduras de borde o interiores forman parte del volumen de la losa** |
| **Muros de contención** | Volúmenes efectivos en toda su longitud; **partes que se cruzan, la intersección una sola vez**; **no incluye la cimentación** (va en su propia partida) |
| **Muros, tabiques y placas de concreto** | Área de la sección transversal horizontal × altura. **Altura:** en plantas altas, de cara superior del entrepiso inferior a cara inferior del entrepiso superior; en 1.ª planta, de cara superior de la base/cimiento a cara inferior del entrepiso. **Se descuentan los vanos de puertas y ventanas** |
| **Pantallas, barandas** | Volumen efectivo según secciones de planos, **sin incluir partes de los elementos que las sostienen** |
| **Columnas** | Suma de volúmenes. **Altura:** 1.er nivel = de cara superior de la cimentación (**no incluye sobrecimiento**) a cara superior del entrepiso; niveles superiores = entre caras superiores de los entrepisos. En columnas endentadas con muros **se agrega el volumen que penetra en los muros** |
| **Vigas** | Suma de volúmenes individuales. **Longitud = entre caras de columnas.** En elementos que se cruzan, **la intersección se mide una sola vez**. En el encuentro losa-viga, **la losa termina en el costado de la viga**, por lo que **el peralte de la viga incluye el espesor de la parte empotrada de la losa** |
| **Losas macizas** | Área × espesor (sumando por espesores distintos). Si la losa descansa en un muro, **se incluye la parte empotrada o apoyada en el muro**; en el encuentro con vigas, la losa termina en el costado de la viga |
| **Losas aligeradas convencionales** | **Volumen total como si fuera maciza menos el volumen ocupado por los ladrillos huecos** |
| **Losas aligeradas con viguetas prefabricadas** | Volumen total como maciza **menos** el volumen de **viguetas y bloques** |
| **Losas nervadas** | Volumen total como maciza **menos** el volumen de los vacíos entre nervaduras |
| **Losa hongo** | Cada elemento con su norma; **la losa no incluye las columnas**, que van con sus capiteles en partidas independientes |
| **Escaleras** | Suma de los volúmenes de **los tramos en pendiente + las losas de descanso** |
| **Cajas de ascensor, cisternas, tanques elevados** | Suma de los volúmenes de las componentes |
| **Pilotes** | **m** (suma de longitudes, medida de la cota de fondo a la cota inferior del cabezal, agrupados por diámetro) **o und** (en cuyo caso la unidad incluye excavación, hincado, concreto, armadura y eliminación) |
| **Estructuras pre/postensadas** | Concreto m³, encofrado m², acero convencional kg, y el **proceso de anclaje y tensado como cifra global (Glb)** |

### 2.3 La regla de las intersecciones (resumen operativo)

La norma **no** ordena descontar el nudo viga-columna del volumen de la columna. Lo que ordena es:

1. **“En los elementos que se crucen se medirá la intersección una sola vez”** (F1, OE.2.3.8, vigas;
   también OE.2.2.1 cimientos, OE.2.2.6 sobrecimientos, OE.2.3.6.1 muros de contención).
2. La columna se mide **de cara superior de entrepiso a cara superior de entrepiso**, es decir
   **atraviesa el nudo**: el nudo pertenece a la columna.
3. La viga se mide **entre caras de columnas**: la viga **no** entra al nudo.
4. La losa termina **en el costado de la viga**: la losa **no** entra a la viga, y el peralte de la
   viga se cuenta completo (incluido el espesor de losa empotrado).

**Traducción a código:**
```
V_columna  = A_sección · (cota_sup_entrepiso_n − cota_sup_entrepiso_n−1)   [atraviesa el nudo]
V_viga     = b · h · (luz libre entre caras de columnas)                   [h incluye el espesor de losa]
V_losa     = A_neta_entre_caras_de_vigas · e
```
Con estas tres reglas **no hay solape ni hueco**: el nudo se contabiliza una sola vez, dentro de la columna.

---

## 3. ENCOFRADO — qué caras se miden (F1)

### 3.1 Regla general (F1, OE.2.3)

> «Como norma general de encofrados, **el área efectiva se obtendrá midiendo el desarrollo de la
> superficie del molde o encofrado en contacto con el concreto**, con excepción de las **losas
> aligeradas, donde se medirá el área total de la losa, que incluye la superficie del ladrillo
> hueco**. Los encofrados **“cara vista” se computarán por separado** de los encofrados “corrientes”.»

Es decir: **m² de contacto**, salvo aligerados (y nervadas), donde se mide la **proyección**.

### 3.2 Por elemento

| Elemento | Qué se mide |
|---|---|
| **Sub-zapatas, bases, sostenimiento de excavaciones** | Área de contacto efectivo con el concreto |
| **Sobrecimientos** | Suma de las áreas **por cara** en contacto efectivo |
| **Gradas** | Áreas en contacto: **contrapasos y costados** |
| **Cimientos reforzados** | Suma por tramo del área efectiva de contacto |
| **Zapatas** | Área efectiva de contacto (las 4 caras laterales; el fondo va sobre solado) |
| **Vigas de cimentación** | Área efectiva de contacto. **Generalmente no requieren encofrado de fondo** (van contra el terreno) |
| **Losas de cimentación** | Área efectiva de contacto (normalmente solo los **bordes verticales del contorno**) |
| **Muros de contención** | Área efectiva de contacto. **Se debe separar “encofrado de una cara” de “encofrado de dos caras”** (costos distintos) |
| **Muros, tabiques y placas** | Área efectiva de contacto de **ambas caras** |
| **Columnas** | Suma de las áreas por encofrar. Si la sección es constante: **perímetro × altura**. **Se suma el área del endentado** si existe y **se descuentan las caras empotradas en muros** |
| **Vigas** | Superficie de contacto efectivo (fondo + 2 costados; el costado superior queda tomado por la losa) |
| **Losas macizas** | Áreas netas de contacto. **Si hay frisos, se consideran** (encofrado del borde de la losa) |
| **Losas aligeradas (convencionales y con viguetas prefabricadas)** | **Se calcula como si fueran losas macizas**, aunque en obra solo se encofra la zona de las viguetas. Aun siendo m² en todos los casos, **los metrados deben diferenciar los distintos sistemas** porque sus costos unitarios no son iguales |
| **Losas nervadas** | **Área de la proyección horizontal como si fuese losa plana.** El encofrado de las nervaduras se toma en cuenta **en el análisis de costos**, no en el metrado |
| **Losas especiales (encasetonados, colaborantes, domos)** | Área neta de contacto **o** área de la proyección como superficie plana |
| **Escaleras** | Tramos en pendiente + descansos. **El área del tramo en pendiente considera solo el área de fondo**; **los costados, los contrapasos y los frisos se consideran (adicionalmente) en los metrados** |
| **Cajas de ascensor, cisternas, tanques** | Suma de las áreas efectivas de contacto con el concreto fresco |

### 3.3 Ladrillos de techo

> «Los ladrillos y bloques huecos que se usan como elementos de relleno en las losas aligeradas se
> computarán **por unidades o millares de unidades**. La cantidad de estos es **generalmente función
> de la superficie de encofrado**, pero **debe deducirse en el caso de viguetas con ensanches de
> concreto en los extremos**.» (F1, OE.2.3)
>
> «Se calculará la **cantidad neta** de ladrillos, bloques huecos o elementos livianos, es decir **sin
> considerar desperdicios**. El porcentaje de desperdicios se incluirá en el análisis de costo.»
> (F1, OE.2.3.9.2)

---

## 4. LOSA ALIGERADA — geometría y tablas

### 4.1 Restricciones normativas (E.060 8.11, “Disposiciones para losas nervadas”)

| Requisito | Valor |
|---|---|
| Ancho mínimo de nervadura (vigueta) | **≥ 100 mm** |
| Altura máxima de la nervadura | **≤ 3,5 × su ancho mínimo** |
| Espaciamiento libre máximo entre nervaduras | **≤ 750 mm** |
| Espesor mínimo de la losa superior | **≥ 1/12 de la distancia libre entre nervaduras y ≥ 50 mm** |
| Si no cumple 8.11.1–8.11.3 | Se diseña como losa y vigas comunes |
| Ductos embebidos | El espesor de losa en cualquier punto ≥ altura del ducto **+ 25 mm** |
| Bono de cortante | Vc de las nervaduras puede tomarse **10 % mayor** (E.060 8.11.8) |

El aligerado peruano estándar (vigueta de **10 cm** cada **40 cm** eje a eje → 30 cm libres, losa
superior de **5 cm**) cumple: 100 mm ✔, 300 mm ≤ 750 mm ✔, 50 mm ≥ 300/12 = 25 mm ✔.

### 4.2 Derivación geométrica exacta (independiente de cualquier tabla)

Con `s` = separación entre ejes de viguetas, `b` = ancho de vigueta, `t` = espesor de losa superior,
`h` = peralte total, `L` = longitud del ladrillo en la dirección de la vigueta:

```
ladrillos por m²        =  1 / (s · L)
concreto (m³/m²)        =  t + (b/s) · (h − t)
volumen de ladrillo/m²  =  h − [ t + (b/s)·(h − t) ]
```

Para el módulo peruano estándar (`s = 0,40 m`, `b = 0,10 m`, `t = 0,05 m`, `L = 0,30 m`):

```
ladrillos/m²  = 1 / (0,40 · 0,30) = 8,333 und/m²
concreto      = 0,05 + 0,25 · (h − 0,05)   [m³/m²]
```

| Peralte h (cm) | Alto del ladrillo (cm) | Ladrillos/m² | **Concreto (m³/m²)** | Volumen de ladrillo (m³/m²) |
|---|---|---|---|---|
| 12 | 7 | 8,33 | **0,0675** | 0,0525 |
| 15 | 10 | 8,33 | **0,0750** | 0,0750 |
| **17** | **12** | 8,33 | **0,0800** | 0,0900 |
| **20** | **15** | 8,33 | **0,0875** | 0,1125 |
| **25** | **20** | 8,33 | **0,1000** | 0,1500 |
| **30** | **25** | 8,33 | **0,1125** | 0,1875 |

**Confirmación en fuente primaria** — Aceros Arequipa, *Manual del Maestro Constructor*, sección
“Aportes de materiales” (https://www.acerosarequipa.com/manuales/manual-del-maestro-constructor/aportes-de-materiales):

- Publica la **misma fórmula** de ladrillos: `CL = 1 / ((A + V) · L)` con `A` = ancho del ladrillo,
  `V` = ancho de vigueta (0,10 m), `L` = longitud del ladrillo → **8,3 und/m²** (y 8,7 con 5 % de
  desperdicio, que es dato de APU, no de metrado).
- Publica el **ejemplo numérico**: `Vc = 1×1×0,17 − (8,3 × 0,12 × 0,30 × 0,30) = 0,08 m³/m²`.
- Publica la **tabla de concreto por m² de techo aligerado**: h = 17 → **0,080** ✔ · h = 20 → **0,087** ✔ ·
  h = 25 → **0,100** ✔ (además de cemento en bolsas/m² y arena/piedra en m³/m², aunque **sin declarar la
  proporción de mezcla**, por lo que esos aportes no son reutilizables a ciegas).

| Valor | Estado |
|---|---|
| 8,33 und/m² | ✔ Verificado (AA Manual del Maestro Constructor; y ficha Pirámide Hueco 15 Raya v03: *“Rendimiento — Viguetas 10 cm ancho: 8,3 und/m²”*) |
| 0,080 m³/m² (h = 17) | ✔ Verificado (AA) |
| 0,087 m³/m² (h = 20) | ✔ Verificado (AA; el valor exacto es 0,0875, AA lo trunca) |
| 0,100 m³/m² (h = 25) | ✔ Verificado (AA) |
| **0,113 m³/m² (h = 30)** | **[NO VERIFICADO]** — no aparece en la tabla de AA ni en otra fuente primaria. **0,1125** es el valor geométrico exacto con la fórmula que sí publica AA. Reportarlo como *derivado*, no como *citado* |
| 0,0675 (h = 12) y 0,0750 (h = 15) | **[NO VERIFICADO]** — derivados. Además **h = 12 cm es inviable** con losa de 5 cm (exigiría ladrillo de 7 cm, que no se fabrica). El escalón real por debajo de 17 cm es **h = 13 cm con ladrillo de 8 cm** (Lark Hueco 8, Pirámide Hueco 8) → 0,0700 m³/m² |

**Ojo con los rendimientos “comerciales”:** casi todos los fabricantes (Lark, Maxx, Pirámide en su web)
publican **9 und/m²**, que es 8,33 × 1,08 (≈8 % de desperdicio). Ese número **no sirve para el
metrado**, que la Norma exige **neto** (F1, OE.2.3.9.2). Único fabricante que publica el valor honesto:
**Pirámide, ficha Hueco 15 Raya v03 → 8,3 und/m²**.

**Ladrillos de techo peruanos verificados en ficha técnica** (dimensiones en cm, alto × 30 × 30 salvo
indicación):

| Fabricante | Producto | Dimensiones (cm) | Peso (kg) | Losa a la que aplica |
|---|---|---|---|---|
| Lark | Hueco 8 Acanalado | 8 × 30 × 30 | 4,5 | h = 13 |
| Lark | Hueco 12 Acanalado | 12 × 30 × 30 | 6,2 | h = 17 |
| Lark | Hueco 15 Acanalado | 15 × 30 × 30 | 7,6 | h = 20 |
| Lark | Hueco 20 Acanalado | 20 × 30 × 30 | 9,8 | h = 25 |
| Lark | Hueco 25 | 25 × 30 × 30 | 12,25 | h = 30 |
| Pirámide | Hueco 8 | 30 × 30 × 8 | 4,6 | h = 13 |
| Pirámide | Hueco 12 | 30 × 30 × 12 | 6,8 | **h = 17, hasta 4 m de paño** |
| Pirámide | Hueco 15 Raya | 30,0 ±4 mm × 30,0 × 15,0 ±4 mm | 7,8 | **h = 20, hasta 5 m** |
| Pirámide | Hueco 20 | 30 × 30 × 20 | 10,2 | **h = 25, hasta 6 m** |
| Maxx (Tacna) | Techo 12 / 15 / 20 | 12/15/20 × 30 × 30 | 7,1 / 7,8 / 10,6 | h = 17 / 20 / 25 |
| **Fortes** | **Techo 15** | **29,5 × 29,5 × 15** ⚠ | — | h = 20 |

⚠ **Fortes Techo 15 mide 29,5 × 29,5 cm**, no 30 × 30. Con esa unidad el rendimiento sube a
`1/((0,295 + 0,105)·0,295) = 8,47 und/m²`. Si el motor admite dimensiones por fabricante, esto importa.

> **Bovedillas ≠ aligerado convencional.** Lark Bovedilla 15 (15 × 39,5 × 25) → 9 und/m²;
> Pirámide Bovedilla 15 → 10 und/m²; Bovedilla 20 → 8 und/m². Usan **viguetas pretensadas @ 50 cm**,
> no viguetas vaciadas @ 40 cm, y se metran por la partida OE.2.3.9.3 (viguetas prefabricadas).

**Advertencias para el motor:**
- La fórmula asume **viguetas sin ensanche**. Donde haya ensanches de vigueta (zonas de cortante), el
  concreto sube y los ladrillos bajan — F1 exige **deducir** los ladrillos en esos tramos.
- Si el proyecto usa 8 viguetas/m con ladrillo de 25 cm o un módulo distinto, hay que recalcular con
  la fórmula general, no con la tabla.
- El **encofrado** del aligerado se mide como losa maciza (proyección), no como superficie de contacto.

### 4.3 Peso propio del aligerado — E.020 Cargas, Anexo 1 ✔ VERIFICADO

Tabla textual de la Norma E.020 (Anexo 1, *Pesos unitarios*), bajo el epígrafe
**“Losas aligeradas armadas en una sola dirección de Concreto Armado — Con vigueta 0,10 m de ancho y
0,40 m entre ejes”**:

| Espesor del aligerado (m) | Espesor de losa superior (m) | **Peso propio kPa (kgf/m²)** |
|---|---|---|
| 0,17 | 0,05 | 2,8 (**280**) |
| 0,20 | 0,05 | 3,0 (**300**) |
| 0,25 | 0,05 | 3,5 (**350**) |
| 0,30 | 0,05 | 4,2 (**420**) |

**Fuente:** RNE Norma E.020 Cargas, Anexo 1 (`RNE_E020_Cargas_gobpe.pdf`, págs. 19-20).
Nótese que la norma **condiciona la tabla al módulo de 0,10 m / 0,40 m**: para cualquier otro módulo
hay que calcular el peso, no leerlo de la tabla.

### 4.4 Pesos unitarios de materiales (E.020, Anexo 1) — para el motor ✔ VERIFICADO

| Material | kN/m³ | **kg/m³** |
|---|---|---|
| **Acero** | 78,5 | **7 850** |
| Concreto simple de grava | 23,0 | **2 300** |
| **Concreto armado** | 24,0 | **2 400** (“añadir 1,0 kN/m³ al concreto simple”) |
| Concreto simple de cascote de ladrillo | 18,0 | 1 800 |
| Albañilería — unidades cocidas **sólidas** | 18,0 | 1 800 |
| Albañilería — unidades cocidas **huecas** | 13,5 | 1 350 |
| Adobe | 16,0 | 1 600 |
| Mortero de cemento (enlucido) | 20,0 | 2 000 |
| Aluminio | 27,5 | 2 750 |
| Vidrio | 25,0 | 2 500 |

Con ρ_acero = 7 850 kg/m³ se cierra el círculo con la §1.2: `m[kg/m] = 0,0061654·d²[mm]` y
`plancha [kg/m²] = espesor[m] × 7 850`.

---

## 5. ALBAÑILERÍA

### 5.1 Reglas de medición (F1, OE.3.1 “Muros y tabiques de albañilería”)

**Unidad de medida: m².**

Definiciones que fija la propia norma y que el motor debe usar para clasificar el aparejo:

> «Tratándose de ladrillos, se denominan respectivamente **largo** (su mayor dimensión), **ancho** (su
> dimensión media) y **espesor** (su menor dimensión). Si el espesor del muro es igual al **largo** del
> ladrillo se dice **“muro de cabeza”**; si es igual al **ancho**, **“muro de soga”**; si es igual al
> **espesor** del ladrillo, **“muro de canto”**.»

Reglas de cómputo:

1. Cada tipo de muro identificado en planos va en **su partida específica**, señalando el tipo de
   unidad, **el aparejo o amarre** y el **acabado de sus caras**.
2. El área de cada tipo de muro es la **suma de las áreas de los tramos** correspondientes.
3. **Las áreas son netas: se descuentan los vanos de puertas, ventanas, mamparas y cualquier otro vacío.**
   *(La norma no fija un umbral mínimo de vano a descontar para muros; sí lo hace para coberturas
   metálicas, donde descuenta huecos ≥ 1,00 m² — OE.2.4.6.1.)*
4. En **albañilería armada o confinada**, la armadura y el concreto que forman parte del muro
   **se consideran en los análisis de precios unitarios**, no como partidas separadas de metrado del muro.
5. **Aceros de amarre** (mechas de conexión muro-columna): partida propia en **kg** (OE.3.1.18).
6. **Barandas y parapetos**: m² (o **m** si la altura es constante) — OE.3.1.15.
7. **Arcos** de ladrillo: **und** — OE.3.1.16.

Tipos de muro que la norma lista como partidas distintas (OE.3.1.1 a OE.3.1.14): King Kong de arcilla
(máquina o artesanal), ladrillo corriente de arcilla, pandereta de arcilla, block sílico-calcáreo K.K.
estándar, block sílico-calcáreo tabique (tres huecos), ladrillo de concreto, bloques huecos de
concreto, albañilería armada, albañilería confinada, drywall, piedra, adobe (simple o estabilizado),
tabiques con elementos leves.

### 5.2 Fórmula general de unidades por m²

```
unidades/m²  =  1 / [ (L_aparente + j) · (H_aparente + j) ]

  L_aparente, H_aparente = dimensiones de la cara del ladrillo que queda a la vista
                           según el aparejo:
     soga   → cara (largo × espesor)      ; espesor del muro = ancho del ladrillo
     cabeza → cara (ancho × espesor)      ; espesor del muro = largo del ladrillo
     canto  → cara (largo × ancho)        ; espesor del muro = espesor del ladrillo
  j = espesor de la junta (horizontal y vertical), en metros
```

```
mortero (m³/m²)  =  e_muro · [ 1 − unidades/m² · L_aparente · H_aparente ]
```
donde `e_muro` es el espesor del muro (sin tarrajeo). Es decir: **todo el volumen del muro que no es
unidad, es mortero** (se desprecia el mortero que entra en los alvéolos de las unidades huecas; si se
quiere ser exacto hay que sumar el relleno de alvéolos, que en pandereta/King Kong 18 huecos es
significativo — ver aviso en §5.4).

### 5.3 Espesor de junta (E.070 Albañilería, **Art. 4.1.2**) ✔ VERIFICADO

> «En la albañilería con unidades asentadas con mortero, **todas las juntas horizontales y verticales
> quedarán completamente llenas de mortero**. El espesor de las juntas de mortero será como **mínimo
> 10 mm** y el espesor **máximo será 15 mm** o **dos veces la tolerancia dimensional en la altura de la
> unidad de albañilería más 4 mm**, lo que sea mayor. En las juntas que contengan **refuerzo
> horizontal**, el espesor mínimo de la junta será **6 mm + el diámetro de la barra**.»
> — **E.070 vigente, Capítulo 4 “Procedimiento de construcción”, Art. 4.1.2**
> (edición digital oficial SENCICO 2020, ISBN 978-612-48427-6-4 →
> `RNE_E070_Albanileria_SENCICO_oficial.pdf`). En el capítulo de albañilería armada aparece la misma
> cláusula añadiendo «fuera de los alvéolos».

**Valor por defecto para el motor: j = 1,5 cm** (máximo normativo y el que usa la práctica peruana).
Ofrecer también 1,0 cm. **La junta de 2,0 cm NO es conforme con E.070** (el máximo es 15 mm, y la
cláusula de tolerancia — 2×tolerancia + 4 mm — da 8 mm para un ladrillo Tipo IV, muy por debajo de 15
mm): si el motor la admite, debe emitir advertencia.

> ⚠️ **Numeración del artículo.** La copia que más circula en Google
> (`e.070-alba-ileria-sencico.pdf` del CIP → `RNE_E070_Albanileria_CIP_SENCICO.pdf`) es la
> **“PROPUESTA de Norma E.070”**, donde esta misma cláusula está numerada **10.7**. Si la app cita
> artículos, debe citar **4.1.2** (norma vigente), no 10.7.

**E.070 Tabla 1 — Clase de unidad de albañilería para fines estructurales** ✔ VERIFICADO

| Clase | Var. dimensional (%) ≤100 mm / ≤150 mm / >150 mm | Alabeo máx. (mm) | f'b mínimo MPa (kg/cm²), área bruta |
|---|---|---|---|
| Ladrillo I | ±8 / ±6 / ±4 | 10 | 4,9 (50) |
| Ladrillo II | ±7 / ±6 / ±4 | 8 | 6,9 (70) |
| Ladrillo III | ±5 / ±4 / ±3 | 6 | 9,3 (95) |
| Ladrillo IV | ±4 / ±3 / ±2 | 4 | 12,7 (130) |
| Ladrillo V | ±3 / ±2 / ±1 | 2 | 17,6 (180) |
| Bloque P (portante) | ±4 / ±3 / ±2 | 4 | 4,9 (50) |
| Bloque NP (no portante) | ±7 / ±6 / ±4 | 8 | 2,0 (20) |

**E.070 Tabla 4 — Tipos de mortero** (proporciones volumétricas en estado suelto, Art. 3.2.4)

| Tipo | Cemento | Cal | Arena | Uso |
|---|---|---|---|---|
| P1 | 1 | 0 a ¼ | 3 a 3½ | Muros portantes |
| P2 | 1 | 0 a ½ | 4 a 5 | Muros portantes |
| NP | 1 | — | hasta 6 | Muros no portantes |

Absorción máxima (Art. 3.1.2.b): arcilla y sílico-calcáreo ≤ 22 %; bloque de concreto clase P ≤ 12 %;
clase NP ≤ 15 %.

### 5.4 Tablas de unidades por m² y mortero ✔ VERIFICADO (con salvedades)

**La fórmula de §5.2 es la que publica Aceros Arequipa** en su *Manual del Maestro Constructor*
(“Aportes de materiales”), literalmente:

```
CL  = 1 / ((L + Jh) · (H + Jv))         L, H = dimensiones de la cara expuesta
Vmo = Vmuro − Vladrillos                 (volumen de mortero por m²)
```
con su ejemplo textual: `Vmo = 1 × 1 × 0,13 − 38 × 0,09 × 0,13 × 0,24 = 0,023 m³/m²`
(King Kong soga, junta 1,5 cm).

#### 5.4.1 King Kong 18 huecos — **9 × 12,5 × 23 cm** (Lark, Pirámide, Fortes)

| Junta | SOGA und/m² | mortero m³/m² | CABEZA und/m² | mortero m³/m² | CANTO und/m² | mortero m³/m² |
|---|---|---|---|---|---|---|
| **10 mm** | **41,67** ✔ | 0,0172 | **74,07** ✔ | 0,0383 | 30,86 | 0,0101 |
| **15 mm** | **38,87** ✔ | 0,0244 | **68,03** ✔ | 0,0540 | 29,15 | 0,0146 |
| 20 mm ⚠ no conforme E.070 | 36,36 | 0,0309 | 62,70 | 0,0678 | 27,59 | 0,0186 |

✔ La ficha **King Kong 18 Hércules Pirámide (v03, 27-05-2026)** publica textualmente
*“Rendimiento — 41,7 soga (mortero 10,0 mm mín.) / 38,9 soga (mortero 15,0 mm máx.) / 74,1 cabeza /
68,0 cabeza”*: **coincidencia exacta con la geometría**. Ídem la ficha “Pirámide Estructural 9”.

#### 5.4.2 King Kong 30 % / INFES (“KK clásico”) — **9 × 13 × 24 cm**

| Junta | SOGA und/m² | mortero m³/m² | CABEZA und/m² | mortero m³/m² | CANTO und/m² | mortero m³/m² |
|---|---|---|---|---|---|---|
| **10 mm** | **40,00** ✔ | 0,0177 | **71,43** | 0,0394 | 28,57 | 0,0098 |
| **15 mm** | **37,35** ✔ | 0,0251 | **65,68** | 0,0556 | 27,05 | 0,0141 |
| 20 mm ⚠ | 34,97 | 0,0318 | 60,61 | 0,0698 | 25,64 | 0,0180 |

✔ Ficha **King Kong 30 % Pirámide (v03)**: *“40,0 soga (10 mm) / 37,3 soga (15 mm)”*.
✔ **Ladrillos Maxx INFES 9 × 13 × 24 → 40 und/m²**.

#### 5.4.3 Pandereta — **9 × 11 × 23 cm** (Pirámide, “Pandereta Raya”)

| Junta | SOGA und/m² | mortero m³/m² | CABEZA und/m² | mortero m³/m² | CANTO und/m² | mortero m³/m² |
|---|---|---|---|---|---|---|
| **10 mm** | **41,67** ✔ | 0,0151 | 83,33 | 0,0402 | 34,72 | 0,0109 |
| **15 mm** | **38,87** ✔ | 0,0215 | 76,19 | 0,0565 | 32,65 | 0,0156 |
| 20 mm ⚠ | 36,36 | 0,0272 | 69,93 | 0,0708 | 30,77 | 0,0199 |

#### 5.4.4 Pandereta acanalada Lark — **9 × 10,5 × 23 cm**

| Junta | SOGA und/m² | mortero m³/m² | CABEZA und/m² | mortero m³/m² | CANTO und/m² | mortero m³/m² |
|---|---|---|---|---|---|---|
| 10 mm | 41,67 | 0,0144 | 86,96 | 0,0410 | 36,23 | 0,0112 |
| 15 mm | 38,87 | 0,0205 | 79,37 | 0,0575 | 34,01 | 0,0161 |
| 20 mm ⚠ | 36,36 | 0,0260 | 72,73 | 0,0719 | 32,00 | 0,0204 |

⚠ **Lark publica 36 und/m²**, que no corresponde ni a 10 ni a 15 mm de junta (equivale a ~20 mm).
La ficha de Lark **no declara el espesor de junta**: dato comercial no auditable.

#### 5.4.5 Pandereta 9 × 12 × 24 cm (la que usa la tabla de Aceros Arequipa)

| Junta | SOGA und/m² | mortero m³/m² | CABEZA und/m² | mortero m³/m² | CANTO und/m² | mortero m³/m² |
|---|---|---|---|---|---|---|
| 10 mm | 40,00 | 0,0163 | 76,92 | 0,0406 | 30,77 | 0,0102 |
| 15 mm | 37,35 | 0,0232 | 70,55 | 0,0571 | 29,05 | 0,0147 |

#### 5.4.6 Otras unidades verificadas en ficha

| Unidad (fabricante) | L × A × H (cm) | Junta 10 mm | Junta 15 mm | Cara / observación |
|---|---|---|---|---|
| **Tabicón 15 Pirámide** | 25 × 8 × 15 | **24,04** ✔ (ficha: 24,0) | **22,87** ✔ (ficha: 22,9) | cara 25 × 15 |
| **Bloqueta 12 Pirámide** (arcilla) | 34 × 12 × 18 | **15,04** ✔ (ficha: 15,0) | **14,45** ✔ (ficha: 14,4) | cara 34 × 18 |
| Caravista 6 Pirámide | 24 × 12 × 6 | 57,14 (publica 60, +5 %) | 52,29 (publica 55) | soga |
| Pastelero Pirámide | 24 × 24 × 3 | 16,0 (publica 17) | 15,4 (publica 16) | piso de azotea |
| Pandereta / Hércules I Maxx | 24 × 14 × 10 | 36,36 ✔ (publica 36) | 34,10 | |
| Tabimax Maxx | 24,5 × 8 × 17 | ≈22 ✔ (publica 22) | | |
| Blocker II Maxx | 28 × 12 × 17 | ≈17 ✔ (publica 17) | | |
| Pandereta Fortes | **21 × 11 × 9** ⚠ | 45,45 | 42,33 | no publica und/m² |

#### 5.4.7 Tabla de contraste publicada por Aceros Arequipa (ya con desperdicio)

*Cantidad de ladrillos por m² de muro:*

| Tipo | Dim. (cm) | Junta (cm) | CABEZA | SOGA | CABEZA +5 % | SOGA +5 % |
|---|---|---|---|---|---|---|
| King Kong | 9×13×24 | 1,0 | 72 | 40 | 76 | 42 |
| King Kong | 9×13×24 | 1,5 | 66 | 38 | 69 | 40 |
| Pandereta | 9×12×24 | 1,0 | 77 | 40 | 81 | 42 |
| Pandereta | 9×12×24 | 1,5 | 71 | 38 | 75 | 40 |

*Mortero, cemento y arena gruesa por m² de muro:*

| Tipo | Dim. | Junta | Mortero CAB. m³/m² | Mortero SOGA m³/m² | Cemento bol/m² CAB. | SOGA | Arena m³/m² CAB. | SOGA |
|---|---|---|---|---|---|---|---|---|
| King Kong | 9×13×24 | 1,0 | 0,038 | 0,018 | 0,3 | 0,1 | 0,04 | 0,02 |
| King Kong | 9×13×24 | 1,5 | 0,055 | 0,023 | 0,4 | 0,2 | 0,06 | 0,02 |
| Pandereta | 9×12×24 | 1,0 | 0,040 | 0,016 | 0,3 | 0,1 | 0,04 | 0,02 |
| Pandereta | 9×12×24 | 1,5 | 0,056 | 0,022 | 0,4 | 0,2 | 0,06 | 0,02 |

AA **redondea siempre hacia arriba** el número de unidades (71,43→72; 65,68→66; 37,35→38) y con ese N
inflado calcula el mortero, lo que lo reduce 2-8 %. **Recomendación: implementar la forma cerrada
exacta y redondear solo al presentar.**

#### 5.4.8 Advertencias que el motor debe emitir

1. ⚠ **Todas las fórmulas de mortero tratan la unidad como sólida (volumen bruto)**, ignorando que el
   mortero penetra los alvéolos. Es la convención peruana estándar (y la de AA), pero en King Kong 18
   huecos (vacíos < 50 %) y pandereta (< 53 %) el consumo real en obra es mayor.
2. ⚠ **Conflicto documentado sobre las dimensiones del “King Kong 18 huecos”.** Aceros Arequipa lo
   tabula como 9 × 13 × 24 en su Manual del Maestro Constructor, pero **ningún fabricante grande lo
   produce hoy con esa medida**: Lark, Pirámide y Fortes lo hacen de **9 × 12,5 × 23**. El 9 × 13 × 24
   corresponde al **King Kong 30 % / INFES**. La diferencia es **40 → 41,67 und/m² (+4 %)**. El motor
   debe tener las **dos entradas separadas**, no una sola.
3. ⚠ La web de Pirámide publica “46 und/m²” para el KK 18 Hércules, **inconsistente con su propia ficha
   v03** (41,7 neto @1 cm ⇒ 44 con 5 %). **Usar la ficha PDF, no la página web.**
4. ⚠ La junta de **20 mm no cumple E.070 Art. 4.1.2**.

#### 5.4.9 Huecos de información (datos que NO se consiguieron)

| Faltante | Estado |
|---|---|
| **Bloques de concreto (39×19×9/12/14/19)** | **[NO VERIFICADO]** — no se consiguió ficha técnica de fabricante peruano (Unicon, Firth, Bloquesa no publican fichas accesibles; COMACSA redirige a Holcim Perú sin listar bloques). Solo cabe el cálculo geométrico con dimensiones asumidas. **No publicar como verificado.** |
| **Ladrillo sílico-calcáreo** | **[NO VERIFICADO]** — ningún fabricante peruano con ficha en línea. La Norma de Metrados sí reconoce las partidas OE.3.1.4 y OE.3.1.5, y E.070 les fija absorción ≤ 22 %, pero **no hay dimensiones ni und/m² verificables** |
| **Casetones / bloques de poliestireno para aligerado** | **[NO VERIFICADO]** — ningún fabricante peruano publica dimensiones ni und/m². Lo único normativo es su peso: 2,0 kN/m³ (200 kg/m³) en E.020 |
| **Ladrillos Rex** | El dominio no resuelve; nada verificable |
| **Ladrillera El Diamante (Arequipa)** | Su web no publica dimensiones ni rendimientos (pestaña “Ficha técnica” vacía) |

---

## 6. ESTRUCTURAS METÁLICAS

### 6.1 Reglas de medición (F1, OE.2.4)

> «Comprende el cómputo de las estructuras metálicas tanto de celosía como de perfiles y considera el
> **suministro de materiales y todos los trabajos necesarios para su construcción y montaje,
> incluyendo los anclajes, ganchos, tornillos, pernos, tuercas, soldaduras, etc.** necesarios para su
> instalación.»
>
> «En las estructuras metálicas el **armado** se refiere a la construcción del elemento **en taller
> fuera de obra o al pie de obra**, que incluye todos los accesorios fijos al elemento; el **montaje**
> es la colocación en el lugar definitivo, incluyendo los accesorios sueltos, los que se medirán aparte.»

| Partida | Unidad de medida | Forma de medición |
|---|---|---|
| **Columnas o pilares** (OE.2.4.1) | **Und** para armado + **Und** para montaje | Se cuenta la cantidad de piezas de **iguales características y longitud** |
| **Vigas** (OE.2.4.2) | Und + Und | Ídem |
| **Viguetas** (OE.2.4.3) | Und + Und | Ídem |
| **Tijerales y reticulados** (OE.2.4.4) | Und + Und | Ídem |
| **Correas** (OE.2.4.5) | Und + Und | Ídem |
| **Coberturas** (OE.2.4.6) | **m²** o **und** | Superficie geométrica **realmente ejecutada, sin desarrollo de ondulaciones ni juntas**. **Se descuenta la superficie de cajones de ventilación, chimeneas y aberturas ≥ 1,00 m²**. La unidad incluye los elementos de sujeción |
| **Cumbreras, canaletas, bajantes** (OE.2.4.7) | **m** o **und** | Longitudes por tipo; la unidad incluye ganchos de sujeción, abrazaderas y elementos de sostén |

En todos los casos: *«La unidad de **armado** comprende material, mano de obra y accesorios fijos. La
unidad de **montaje** comprende soldadura y mano de obra.»*

> **Consecuencia importante:** la Norma Técnica de Metrados peruana **NO metra el acero estructural en
> kg** — lo metra por **unidad de pieza**. El **kg** aparece dentro del análisis de precios unitarios
> de esa unidad. Un motor de cálculo debe, por tanto, producir **ambos**: el conteo de piezas
> (metrado normativo) y el peso teórico en kg (insumo del APU y base de compra).

### 6.2 Peso del acero estructural

```
Perfil        :  kg = Σ (peso_lineal[kg/m] · longitud[m])
Plancha       :  kg/m² = espesor[m] · 7 850          (E.020 Anexo 1: acero = 78,5 kN/m³)
Barra redonda :  kg/m = 0,0061654 · d²[mm]
Barra cuadrada:  kg/m = 0,007850 · a²[mm]
Tubo          :  kg/m = perímetro_medio · espesor · 7 850  (o el valor de catálogo)
```

### 6.3 Tablas de perfiles — Aceros Arequipa ✔ VERIFICADO en hoja técnica

#### 6.3.1 Ángulos estructurales de alas iguales, **sistema métrico**, ASTM A36
*(Hoja técnica “Ángulos Estructurales — Calidad ASTM A36”, QCQA01-F103/06/AGO 23 →
`AcerosArequipa-HT-ANGULOS-ESTRUCTURALES-A36.pdf`. Longitud comercial: **6 m**, paquetes de 1 t.)*

| L × L × e (mm) | kg/m | kg/6 m |
|---|---|---|
| 20 × 20 × 2,0 | 0,60 | 3,58 |
| 20 × 20 × 2,3 | 0,68 | 4,09 |
| 20 × 20 × 2,5 | 0,74 | 4,42 |
| 20 × 20 × 3,0 | 0,87 | 5,23 |
| 25 × 25 × 2,0 | 0,75 | 4,52 |
| 25 × 25 × 2,3 | 0,86 | 5,17 |
| 25 × 25 × 2,5 | 0,93 | 5,59 |
| 25 × 25 × 3,0 | 1,11 | 6,64 |
| 25 × 25 × 4,5 | 1,61 | 9,64 |
| 25 × 25 × 5,0 | 1,77 | 10,60 |
| 25 × 25 × 6,0 | 2,07 | 12,43 |
| 30 × 30 × 2,0 | 0,91 | 5,47 |
| 30 × 30 × 2,3 | 1,04 | 6,25 |
| 30 × 30 × 2,5 | 1,13 | 6,77 |
| 30 × 30 × 3,0 | 1,34 | 8,05 |
| 30 × 30 × 4,5 | 1,96 | 11,77 |
| 30 × 30 × 5,5 | 2,35 | 14,12 |
| 30 × 30 × 6,0 | 2,54 | 15,26 |
| 38 × 38 × 2,0 | 1,16 | 6,97 |

fy ≥ 250 MPa (2 530 kg/cm²) · fu = 400-550 MPa · tolerancia de peso **+3,0 % / −2,5 %** del nominal.

#### 6.3.2 Ángulo estructural **dual A36/A572-G50**, sistema inglés
*(Hoja técnica “Ángulo Estructural Dual”, QCQA01-F101/06/SEP 24 →
`AcerosArequipa-HT-ANGULOS-DUAL-A36-A572-G50.pdf`. Longitudes: **6 m y 12 m**, paquetones de 2 t.)*

| L × L × e (pulg) | lb/pie | **kg/m** | kg/6 m | kg/12 m |
|---|---|---|---|---|
| 1 1/2 × 1 1/2 × 3/32 | 0,93 | **1,38** | 8,29 | 16,58 |
| 1 1/2 × 1 1/2 × 1/8 | 1,23 | **1,83** | 10,98 | 21,97 |
| 1 1/2 × 1 1/2 × 3/16 | 1,80 | **2,68** | 16,07 | 32,14 |
| 1 1/2 × 1 1/2 × 1/4 | 2,34 | **3,48** | 20,89 | 41,79 |
| 2 × 2 × 1/8 | 1,65 | **2,46** | 14,73 | 29,47 |
| 2 × 2 × 3/16 | 2,44 | **3,63** | 21,79 | 43,57 |
| 2 × 2 × 1/4 | 3,19 | **4,75** | 28,48 | 56,97 |
| 2 × 2 × 5/16 | 3,92 | **5,83** | 35,00 | 70,00 |
| 2 × 2 × 3/8 | 4,70 | **6,99** | 41,97 | 83,93 |
| 2 1/2 × 2 1/2 × 3/16 | 3,07 | **4,57** | 27,41 | 54,82 |
| 2 1/2 × 2 1/2 × 1/4 | 4,10 | **6,10** | 36,61 | 73,22 |
| 2 1/2 × 2 1/2 × 5/16 | 5,00 | **7,44** | 44,65 | 89,29 |
| 2 1/2 × 2 1/2 × 3/8 | 5,90 | **8,78** | 52,68 | 105,36 |
| 3 × 3 × 1/4 | 4,90 | **7,29** | 43,75 | 87,50 |
| 3 × 3 × 5/16 | 6,10 | **9,08** | 54,47 | 108,93 |
| 3 × 3 × 3/8 | 7,20 | **10,72** | 64,29 | 128,58 |
| 3 × 3 × 1/2 | 9,40 | **13,99** | 83,93 | 167,86 |
| 4 × 4 × 1/4 | 6,60 | **9,82** | 58,93 | 117,86 |
| 4 × 4 × 5/16 | 8,20 | **12,20** | 73,22 | 146,44 |
| 4 × 4 × 3/8 | 9,80 | **14,58** | 87,50 | 175,01 |
| 4 × 4 × 1/2 | 12,80 | **19,05** | 114,29 | 228,58 |

fy ≥ 345 MPa (3 520 kg/cm²) · fu = 450-550 MPa · soldabilidad buena.
Factor de conversión usado por el fabricante: **1 lb/pie = 1,48816 kg/m** (verificado fila a fila).

#### 6.3.3 Canales U, ASTM A36 y dual A36/A572-G50
*(Hoja técnica “Canales U”, QCQA01-F115/06/JUL 26 y F242/02/NOV 23 →
`AcerosArequipa-HT-CANALES-U-A36-A572G50.pdf`. Longitud comercial: **6 m**, paquetes de 2 t.
Tolerancia de peso −2,5 % / +3,0 %.)*

**Calidad A36:**

| Designación | lb/pie | **kg/m** | Área (pulg²) | Alma A (pulg) | Ala B (pulg) | t_w (mm) | t_f (mm) |
|---|---|---|---|---|---|---|---|
| C 2" | 2,58 | 3,84 | 0,76 | 2,00 | 1,00 | 4,75 | 4,75 |
| C 3" | 4,10 | 6,10 | 1,21 | 3,00 | 1,41 | 6,93 | 4,32 |
| C 3" | 5,00 | 7,44 | 1,47 | 3,00 | 1,50 | 6,93 | 6,55 |
| C 4" | 5,40 | 8,04 | 1,59 | 4,00 | 1,58 | 7,52 | 4,67 |
| C 4" | 7,25 | 10,79 | 2,13 | 4,00 | 1,72 | 7,52 | 8,15 |

**Calidad dual A36/A572-G50:**

| Designación | lb/pie | **kg/m** | Área (pulg²) | Alma A (pulg) | Ala B (pulg) | t_w (mm) | t_f (mm) |
|---|---|---|---|---|---|---|---|
| C 3" | 6,00 | 8,93 | 1,76 | 3,00 | 1,60 | 6,93 | 9,04 |
| C 4" | 4,50 | 6,70 | 1,32 | 4,00 | 1,58 | 7,52 | 3,18 |
| C 5" | 6,70 | 9,97 | 1,97 | 5,00 | 1,75 | 8,13 | 4,83 |
| C 5" | 9,00 | 13,39 | 2,64 | 5,00 | 1,89 | 8,13 | 8,26 |
| C 6" | 8,20 | 12,20 | 2,40 | 6,00 | 1,92 | 8,71 | 5,08 |
| C 6" | 10,50 | 15,63 | 3,09 | 6,00 | 2,03 | 8,71 | 7,98 |
| C 6" | 13,00 | 19,35 | 3,83 | 6,00 | 2,16 | 8,71 | 11,10 |
| C 7" | 9,80 | 14,58 | 2,87 | 7,00 | 2,09 | 9,30 | 5,33 |
| C 7" | 12,25 | 18,23 | 3,60 | 7,00 | 2,19 | 9,30 | 7,98 |
| C 7" | 14,75 | 21,95 | 4,33 | 7,00 | 2,30 | 9,30 | 10,64 |
| C 8" | 11,50 | 17,11 | 3,38 | 8,00 | 2,26 | 9,91 | 5,59 |
| C 8" | 13,75 | 20,46 | 4,04 | 8,00 | 2,34 | 9,91 | 7,70 |
| C 8" | 18,75 | 27,90 | 5,51 | 8,00 | 2,53 | 9,91 | 12,37 |
| C 9" | 13,40 | 19,94 | 3,94 | 9,00 | 2,43 | 10,49 | 5,92 |
| C 9" | 15,00 | 22,32 | 4,41 | 9,00 | 2,49 | 10,49 | 7,24 |
| C 9" | 20,00 | 29,76 | 5,88 | 9,00 | 2,65 | 10,49 | 11,38 |
| C 10" | 15,30 | 22,77 | 4,49 | 10,00 | 2,60 | 11,07 | 6,10 |
| C 10" | 20,00 | 29,76 | 5,88 | 10,00 | 2,74 | 11,07 | 9,63 |
| C 10" | 25,00 | 37,20 | 7,35 | 10,00 | 2,89 | 11,07 | 13,36 |
| C 10" | 30,00 | 44,64 | 8,82 | 10,00 | 3,03 | 11,07 | 17,09 |
| C 12" | 20,70 | 30,80 | 6,09 | 12,00 | 2,94 | 12,73 | 7,16 |
| C 12" | 25,00 | 37,20 | 7,35 | 12,00 | 3,05 | 12,73 | 9,83 |
| C 12" | 30,00 | 44,64 | 8,82 | 12,00 | 3,17 | 12,73 | 12,95 |
| C 15" | 33,90 | 50,45 | 9,96 | 15,00 | 3,40 | 16,51 | 10,16 |
| C 15" | 40,00 | 59,53 | 11,80 | 15,00 | 3,52 | 16,51 | 13,21 |
| C 15" | 50,00 | 74,41 | 14,70 | 15,00 | 3,72 | 16,51 | 18,19 |

*(Los kg/m son la conversión exacta de los lb/pie que publica el fabricante: `kg/m = lb/pie × 1,48816`.
La hoja técnica publica la columna en lb/pie; el peso métrico se marca `verificado: true` porque la
conversión es exacta, no una estimación.)*

#### 6.3.4 Tees, ASTM A36
*(Hoja técnica “Tees”, QCQA01-F105/05/DIC 23 → `AcerosArequipa-HT-TEES.pdf`. Longitud: **6 m**, paquetes de 1 t.)*

| Sistema | Dimensiones | **kg/m** | kg/barra 6 m |
|---|---|---|---|
| Inglés | 1/4 × 1 1/4 × 1/8 pulg | 1,54 | 9,24 |
| Inglés | 1 1/2 × 1 1/2 × 1/8 pulg | 1,84 | 11,04 |
| Inglés | 1 1/2 × 1 1/2 × 3/16 pulg | 2,72 | 16,32 |
| Inglés | 2 × 2 × 1/4 pulg | 4,97 | 29,82 |
| Métrico | 20 × 20 × 3,0 mm | 0,88 | 5,28 |
| Métrico | 25 × 25 × 3,0 mm | 1,10 | 6,60 |

#### 6.3.5 Platinas ASTM A36
*(Hoja técnica “Platinas”, QCQA01-F104/05/SET 23 → `AcerosArequipa-HT-PLATINAS.pdf`.
Barras de **6 m**, paquetes de 2 t.)*

| e × ancho (pulg) | kg/m | kg/6 m | | e × ancho (pulg) | kg/m | kg/6 m |
|---|---|---|---|---|---|---|
| 1/8 × 1/2 | 0,32 | 1,92 | | 3/8 × 1 | 1,92 | 11,52 |
| 1/8 × 5/8 | 0,39 | 2,34 | | 3/8 × 1 1/4 | 2,38 | 14,28 |
| 1/8 × 3/4 | 0,48 | 2,88 | | 3/8 × 1 1/2 | 2,85 | 17,10 |
| 1/8 × 1 | 0,64 | 3,84 | | 3/8 × 2 | 3,80 | 22,80 |
| 1/8 × 1 1/4 | 0,80 | 4,80 | | 3/8 × 2 1/2 | 4,74 | 28,44 |
| 1/8 × 1 1/2 | 0,95 | 5,70 | | 3/8 × 3 | 5,70 | 34,20 |
| 1/8 × 2 | 1,27 | 7,62 | | 3/8 × 4 | 7,60 | 45,60 |
| 3/16 × 1/2 | 0,48 | 2,88 | | 1/2 × 1 | 2,54 | 15,24 |
| 3/16 × 5/8 | 0,61 | 3,66 | | 1/2 × 1 1/2 | 3,79 | 22,74 |
| 3/16 × 3/4 | 0,74 | 4,44 | | 1/2 × 2 | 5,06 | 30,36 |
| 3/16 × 1 | 0,98 | 5,88 | | 1/2 × 2 1/2 | 6,33 | 37,98 |
| 3/16 × 1 1/4 | 1,18 | 7,08 | | 1/2 × 3 | 7,60 | 45,60 |
| 3/16 × 1 1/2 | 1,42 | 8,52 | | 1/2 × 4 | 10,13 | 60,78 |
| 3/16 × 2 | 1,90 | 11,40 | | 5/8 × 2 1/2 | 7,91 | 47,46 |
| 3/16 × 2 1/4 | 2,14 | 12,84 | | 5/8 × 3 | 9,50 | 57,00 |
| 3/16 × 2 1/2 | 2,37 | 14,22 | | 5/8 × 4 | 12,66 | 75,96 |
| 3/16 × 3 | 2,85 | 17,10 | | 3/4 × 4 | 15,19 | 91,14 |
| 1/4 × 1/2 | 0,64 | 3,84 | | 1 × 3 | 15,19 | 91,14 |
| 1/4 × 5/8 | 0,80 | 4,80 | | 1 × 4 | 20,26 | 121,56 |
| 1/4 × 3/4 | 0,95 | 5,70 | | **12 × 200 mm** | 18,84 | 113,04 |
| 1/4 × 1 | 1,28 | 7,68 | | | | |
| 1/4 × 1 1/4 | 1,58 | 9,48 | | | | |
| 1/4 × 1 1/2 | 1,90 | 11,40 | | | | |
| 1/4 × 2 | 2,53 | 15,18 | | | | |
| 1/4 × 2 1/2 | 3,16 | 18,96 | | | | |
| 1/4 × 3 | 3,80 | 22,80 | | | | |
| 1/4 × 4 | 5,06 | 30,36 | | | | |

#### 6.3.6 Barras redondas lisas / pulidas y barras cuadradas, ASTM A36 / SAE 1045
*(Hojas técnicas “Barras Redondas Lisas y Pulidas” QCQA01-F106/08/JUL 26 y “Barras Cuadradas”
QCQA01-F109/07/SET 25 → `AcerosArequipa-HT-BARRAS-REDONDAS-LISAS.pdf`,
`AcerosArequipa-HT-BARRAS-CUADRADAS.pdf`. Longitud: **6 m**.)*

**Redondas lisas (kg/m):** 3/8" → 0,56 · 1/2" → 0,99 · 5/8" → 1,55 · 3/4" → 2,24 · 7/8" → 3,05 ·
1" → 3,98 · 1 1/4" → 6,22 · 1 3/8" → 7,52 · 2" → 15,91 · 2 1/4" → 20,14.
**Redondas pulidas (kg/m):** 1 1/8" → 5,03 · 1 1/4" → 6,22 · 1 1/2" → 8,95 · 1 3/4" → 12,18 ·
2" → 15,91 · 2 1/2" → 24,86.
**Cuadradas (kg/m):** 1/4" → 0,317 · 3/8" → 0,713 · 5/8" → 1,983 · 3/4" → 2,849 · 7/8" → 3,878;
métricas: 9 mm → 0,64 · 10 → 0,79 · 12 → 1,13 · 15 → 1,77.

El catálogo Aceros Arequipa (versión Colombia 2023, pág. 5) publica además, con más decimales:
3/8" → 0,559 · 1/2" → 0,994 · 5/8" → 1,554 · 3/4" → 2,237 · 7/8" → 3,045 · 1" → 3,978 kg/m.
Todos coinciden con la masa teórica `0,0061654·d²` (redonda) y `0,007850·a²` (cuadrada) — lo que
confirma que **el fabricante usa ρ = 7 850 kg/m³**, igual que E.020.

#### 6.3.7 Tubos estructurales ASTM A500 (LAC y galvanizados)
*(Ficha “Tubo ASTM A500 LAC y GALV”, QCQA01-F219/06/AGO 23 → `AcerosArequipa-FT-TUBO-LAC-A500.pdf`.
Longitudes: redondos **6,40 m y 6 m**; cuadrados y rectangulares **6 m**.)*

**Cuadrados, sistema métrico (kg/m), por espesor:**

| Ext (mm) | 1,5 | 1,8 | 2 | 2,5 | 3 | 4 | 4,5 | 6 | 8 | 10 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 × 25 | 1,061 | 1,311 | 1,460 | 1,766 | – | – | – | – | – | – | – |
| 30 × 30 | 1,300 | 1,594 | 1,700 | – | – | – | – | – | – | – | – |
| 37,5 × 37,5 | 1,696 | – | – | – | – | – | – | – | – | – | – |
| 38 × 38 | – | 2,046 | 2,261 | **3,787 ⚠️** | 3,297 | – | – | – | – | – | – |
| 40 × 40 | 1,770 | – | 2,244 | 2,944 | 3,320 | – | – | – | – | – | – |
| 50 × 50 | 2,250 | **2,274 ⚠️** | 3,122 | 3,872 | 4,316 | 5,777 | 6,429 | 8,289 | – | – | – |
| 50,8 × 50,8 | – | – | 3,122 | 3,872 | 4,316 | – | – | – | – | – | – |
| 75 × 75 | – | – | 4,500 | 5,560 | 6,810 | 8,917 | 9,961 | 13,000 | – | – | – |
| 100 × 100 | – | – | 6,165 | 7,675 | 9,174 | 12,133 | 13,594 | 16,980 | – | – | – |
| 125 × 125 | – | – | – | – | 11,492 | – | 17,027 | – | – | – | – |
| 150 × 150 | – | – | – | – | 13,847 | 18,338 | 20,559 | 27,130 | 35,670 | 43,690 | 51,998 |
| 200 × 200 | – | – | – | – | 18,557 | – | 27,624 | 36,550 | 48,230 | – | – |
| 250 × 250 | – | – | – | – | – | 34,689 | – | 45,970 | – | 75,360 | – |
| 300 × 300 | – | – | – | – | – | – | – | 55,390 | 73,350 | 91,060 | 108,520 |
| 400 × 200 | – | – | – | – | – | – | – | – | – | 122,46 | 146,200 |

**Cuadrados y rectangulares, sistema inglés (kg/m):**

| Designación | 1,8 | 2,0 | 2,3 | 2,5 | 3,0 | 4,0 | 4,5 | 6,0 |
|---|---|---|---|---|---|---|---|---|
| □ 1" | 1,36 | 1,50 | 1,70 | 1,84 | 2,17 | – | – | – |
| □ 1 1/4" | 1,71 | 1,90 | 2,16 | 2,34 | 2,77 | – | – | – |
| □ 1 1/2" | 2,07 | 2,29 | 2,62 | 2,84 | 3,37 | – | – | – |
| □ 2" | 2,79 | 3,09 | 3,54 | 3,83 | 4,56 | 5,99 | – | – |
| □ 3" | – | 4,69 | 5,37 | 5,83 | 6,96 | 9,18 | – | – |
| □ 4" | – | 6,28 | – | 7,82 | 9,35 | 12,37 | 13,86 | – |
| ▭ 1"×2" | 2,10 | 2,32 | – | – | – | – | – | – |
| ▭ 2"×3" | 3,54 | 3,92 | – | 4,87 | 5,81 | – | – | – |
| ▭ 2"×4" | – | 4,71 | – | 5,85 | 6,98 | 9,21 | 10,31 | – |
| ▭ 2"×6" | – | 6,34 | – | 7,89 | 9,43 | 12,48 | 13,98 | – |
| ▭ 4"×10" | – | – | – | – | – | – | – | 34,60 |

> 🚨 **Tres defectos detectados en la ficha del fabricante — NO copiar la tabla tal cual al motor:**
> 1. `38 × 38 × 2,5` figura **3,787**; el valor coherente es **≈2,787** (la fila debe crecer con el espesor).
> 2. `50 × 50 × 1,8` figura **2,274**; el coherente es **≈2,724** (transposición de dígitos).
> 3. En la tabla de **tubos redondos**, las columnas de **2 mm y 2,5 mm** están **corridas una fila hacia
>    arriba** desde 1 1/2" (en la celda de 1 1/2" aparecen dos números superpuestos). Los valores
>    correctos, recalculados con `m = π·(D − t)·t·7,85e-3`:
>    1 1/2"×2,0 = 2,284 · 1 1/2"×2,5 = 2,823 · 2"×2,0 = 2,876 · 2"×2,5 = 3,564 · 2 1/2"×2,0 = 3,503 ·
>    2 1/2"×2,5 = 4,347 · 3"×2,0 = 4,285 · 3"×2,5 = 5,327 · 4"×2,0 = 5,539 · 4"×2,5 = 6,892.
>
> **Regla para el motor:** para tubos, calcular siempre `kg/m = π·(D − t)·t·ρ` (redondos) o
> `kg/m = [2(a + b) − 4t]·t·ρ` (rectangulares, sin esquinas redondeadas) y usar el catálogo solo como
> contraste; si difieren más del 3 % (tolerancia del fabricante), avisar.

#### 6.3.8 Vigas H de alas anchas (WF) y perfiles AISC

Aceros Arequipa **comercializa** vigas WF bajo **ASTM A36 / A572 Gr.50 / A992** (catálogo Perú 2026-01,
págs. 15-16), en barras de **20, 30 y 40 pies** (≈6,10 / 9,14 / 12,19 m), desde 4"×13,00 hasta
36"×232,00 lb/pie. **El catálogo publica lb/pie, no kg/m.**

**La regla de designación es definitoria y resuelve el problema:** en las series W, C, MC y L de AISC,
el número después de la × **es el peso nominal en lb/pie**. Así, `W12X40` pesa **40 lb/pie por
definición**. Conversión exacta: **kg/m = lb/pie × 1,4881639**.

Subconjunto W habitual en Perú (AISC Shapes Database v15.0):

| AISC | Etiqueta SI | lb/pie | **kg/m** | A (cm²) | d (mm) | bf (mm) | tw (mm) | tf (mm) |
|---|---|---|---|---|---|---|---|---|
| W6X9 | W150X13.5 | 9 | 13,5 | 17,3 | 150 | 100 | 4,32 | 5,46 |
| W6X12 | W150X18 | 12 | 18 | 22,9 | 153 | 102 | 5,84 | 7,11 |
| W6X15 | W150X22.5 | 15 | 22,5 | 28,6 | 152 | 152 | 5,84 | 6,60 |
| W6X20 | W150X29.8 | 20 | 29,8 | 37,9 | 157 | 153 | 6,60 | 9,27 |
| W8X10 | W200X15 | 10 | 15 | 19,1 | 200 | 100 | 4,32 | 5,21 |
| W8X13 | W200X19.3 | 13 | 19,3 | 24,8 | 203 | 102 | 5,84 | 6,48 |
| W8X18 | W200X26.6 | 18 | 26,6 | 33,9 | 207 | 133 | 5,84 | 8,38 |
| W8X24 | W200X35.9 | 24 | 35,9 | 45,7 | 201 | 165 | 6,22 | 10,2 |
| W8X31 | W200X46.1 | 31 | 46,1 | 58,9 | 203 | 203 | 7,24 | 11,0 |
| W8X40 | W200X59 | 40 | 59 | 75,5 | 210 | 205 | 9,14 | 14,2 |
| W10X12 | W250X17.9 | 12 | 17,9 | 22,8 | 251 | 101 | 4,83 | 5,33 |
| W10X15 | W250X22.3 | 15 | 22,3 | 28,5 | 254 | 102 | 5,84 | 6,86 |
| W10X22 | W250X32.7 | 22 | 32,7 | 41,9 | 259 | 146 | 6,10 | 9,14 |
| W10X30 | W250X44.8 | 30 | 44,8 | 57,0 | 267 | 148 | 7,62 | 13,0 |
| W10X33 | W250X49.1 | 33 | 49,1 | 62,6 | 247 | 202 | 7,37 | 11,0 |
| W10X49 | W250X73 | 49 | 73 | 92,9 | 254 | 254 | 8,64 | 14,2 |
| W12X14 | W310X21 | 14 | 21 | 26,8 | 302 | 101 | 5,08 | 5,72 |
| W12X19 | W310X28.3 | 19 | 28,3 | 35,9 | 310 | 102 | 5,97 | 8,89 |
| W12X26 | W310X38.7 | 26 | 38,7 | 49,4 | 310 | 165 | 5,84 | 9,65 |
| W12X35 | W310X52 | 35 | 52 | 66,5 | 318 | 167 | 7,62 | 13,2 |
| W12X40 | W310X60 | 40 | 60 | 75,5 | 302 | 203 | 7,49 | 13,1 |
| W12X50 | W310X74 | 50 | 74 | 94,2 | 310 | 205 | 9,40 | 16,3 |
| W12X58 | W310X86 | 58 | 86 | 110,0 | 310 | 254 | 9,14 | 16,3 |
| W14X22 | W360X32.9 | 22 | 32,9 | 41,9 | 348 | 127 | 5,84 | 8,51 |
| W14X30 | W360X44 | 30 | 44 | 57,1 | 351 | 171 | 6,86 | 9,78 |
| W14X43 | W360X64 | 43 | 64 | 81,3 | 348 | 203 | 7,75 | 13,5 |
| W14X53 | W360X79 | 53 | 79 | 101,0 | 353 | 205 | 9,40 | 16,8 |
| W14X68 | W360X101 | 68 | 101 | 129,0 | 356 | 254 | 10,5 | 18,3 |
| W16X26 | W410X38.8 | 26 | 38,8 | 49,5 | 399 | 140 | 6,35 | 8,76 |
| W16X31 | W410X46.1 | 31 | 46,1 | 58,9 | 404 | 140 | 6,99 | 11,2 |
| W16X40 | W410X60 | 40 | 60 | 76,1 | 406 | 178 | 7,75 | 12,8 |
| W16X50 | W410X75 | 50 | 75 | 94,8 | 414 | 180 | 9,65 | 16,0 |
| W18X35 | W460X52 | 35 | 52 | 66,5 | 450 | 152 | 7,62 | 10,8 |
| W18X40 | W460X60 | 40 | 60 | 76,1 | 455 | 153 | 8,00 | 13,3 |
| W18X50 | W460X74 | 50 | 74 | 94,8 | 457 | 191 | 9,02 | 14,5 |
| W18X60 | W460X89 | 60 | 89 | 114,0 | 462 | 192 | 10,5 | 17,7 |
| W21X44 | W530X66 | 44 | 66 | 83,9 | 526 | 165 | 8,89 | 11,4 |
| W21X50 | W530X74 | 50 | 74 | 94,8 | 528 | 166 | 9,65 | 13,6 |
| W21X62 | W530X92 | 62 | 92 | 118,0 | 533 | 209 | 10,2 | 15,6 |
| W21X73 | W530X109 | 73 | 109 | 139,0 | 538 | 211 | 11,6 | 18,8 |
| W24X55 | W610X82 | 55 | 82 | 105,0 | 599 | 178 | 10,0 | 12,8 |
| W24X68 | W610X101 | 68 | 101 | 130,0 | 602 | 228 | 10,5 | 14,9 |
| W24X76 | W610X113 | 76 | 113 | 145,0 | 607 | 228 | 11,2 | 17,3 |
| W24X94 | W610X140 | 94 | 140 | 179,0 | 617 | 230 | 13,1 | 22,2 |

Fuente: **AISC Shapes Database v15.0** (nov-2017), archivo original de AISC obtenido de un espejo
público (`AISC-Shapes-Database-v15.0.xlsx` en `docs/normas/`) porque aisc.org bloquea el acceso
automatizado. Contiene los **2 091 perfiles** completos (W hasta W44X335, HP, M, S, C, MC, L, WT, 2L,
HSS y PIPE). ⚠️ **Verificar los términos de licencia de AISC antes de redistribuir esa base en un
producto comercial.**

**Comprobación cruzada valiosa:** los ángulos “de pulgada” y los canales U de Aceros Arequipa **son**
los perfiles L y C de AISC (L4X4X1/2 = 12,8 lb/pie = 19,05 kg/m en ambas fuentes; C3X6 → A = 1,76 pulg²,
d = 3,00", bf = 1,60", idénticos). Es decir, **una sola tabla AISC sirve para ambos**.

#### 6.3.9 Planchas de acero

Con ρ = 7 850 kg/m³ (E.020 Anexo 1) — y el mismo valor que usa Aceros Arequipa en sus propias tablas
(comprobado: platina 1/4"×2" = 322,6 mm² → 2,532 kg/m, AA publica 2,53 ✔; barra redonda 1" =
506,7 mm² → 3,978, AA publica 3,98 ✔):

| Espesor (mm) | kg/m² | | Espesor (mm) | kg/m² |
|---|---|---|---|---|
| 1,5 | 11,78 | | 8,0 | 62,80 |
| 2,0 | 15,70 | | 9,0 | 70,65 |
| 3,0 | 23,55 | | 12,0 | 94,20 |
| 4,0 | 31,40 | | 19,0 | 149,15 |
| 4,5 | 35,33 | | 25,0 | 196,25 |
| 6,0 | 47,10 | | 32,0 | 251,20 |

**[DERIVADO]** — `kg/m² = espesor(m) × 7 850`. La densidad sí es normativa; los kg/m² son cálculo directo.
**No hay discrepancia entre fuentes:** 7 850 kg/m³ = 7,85 t/m³ = 0,2836 lb/in³ = 490 lb/ft³ son el mismo
número, y es también el valor implícito en ASTM A6/AISC.

**Planchas estriadas LAC** — el relieve pesa más; usar la masa específica publicada
(`AcerosArequipa-HT-PLANCHAS-ESTRIADAS-LAC.pdf`, QCQA01-F211/05/SET 23):

| Espesor nominal (mm) | **Masa nominal (kg/m²)** | Tolerancia +/− (%) |
|---|---|---|
| 2,5 | 20,69 | 8 / 5 |
| 2,9 | 23,67 | 8 / 5 |
| 4,4 | 35,58 | 6 / 5 |
| 5,9 | 47,39 | 5 / 3 |

Formatos 1 200 × 2 400 mm. El relieve añade ≈**1,0 kg/m²** sobre la plancha lisa equivalente
(2,5 mm lisa = 19,63 kg/m²; estriada = 20,69).

Espesores comerciales de plancha LAC A36 (catálogo AA 2026, dimensiones JIS G3193-2008): 1,5 · 1,8 ·
1,9 · 2,0 · 2,2 · 2,3 · 2,4 · 2,5 · 2,9 · 3,0 · 3,9 · 4,0 · 4,4 · 4,5 · 4,8 · 5,0 · 5,9 · 6 · 6,35 ·
6,4 · 8 · 9 · 9,5 · 12 · 12,5 · 16 · 19 · 20 · 22 · 25 · 32 · 38 · 50 · 63 · 75 · 100 · 125 · 150 mm.

#### 6.3.10 Perfiles conformados en frío (Tupemesa)

Tupemesa fabrica **Canal C**, **Canal U** y **Perfil Z** en ASTM A36, espesores **1,8 a 4 mm**, largos
**4,00 a 12,00 m**, en medidas 4×2 hasta 12×3 pulg.
❌ **Tupemesa NO publica los kg/m.** Para el motor:
`kg/m = (ancho desarrollado de la plantilla en m) × (espesor en m) × 7 850`.
**Precor**: el dominio no resuelve. **Calaminon**: no auditado.

### 6.4 Pintura de estructuras metálicas

**Regla normativa (F1, OE.3.11.6 “Pintura de estructuras metálicas”):** unidad **m²**;
*«se medirán las áreas netas a pintarse y estarán diferenciadas por el tipo de pintura»*.
La norma **no** dice cómo obtener el área a partir del perfil.

**Fuente cuantitativa para hacerlo:** la **AISC Shapes Database v15.0** publica el perímetro de la
sección de cada perfil:
- `PB` = *shape perimeter* (AISC Design Guide 19) → **m²/m de pintura = PB(mm)/1000**
- `PA` = perímetro menos una cara de ala (perfil con losa encima)
- `PC` / `PD` = perímetro “en caja” (protección tipo cajón)
- `PA2` = ángulo simple menos la cara del ala larga

| Perfil | kg/m | PB (mm) | **m²/m** | **m²/ton** |
|---|---|---|---|---|
| W6X9 | 13,5 | 681 | 0,681 | 50,4 |
| W8X10 | 15 | 780 | 0,780 | 52,0 |
| W8X18 | 26,6 | 922 | 0,922 | 34,7 |
| W8X31 | 46,1 | 1 190 | 1,190 | 25,8 |
| W10X22 | 32,7 | 1 080 | 1,080 | 33,0 |
| W10X33 | 49,1 | 1 270 | 1,270 | 25,9 |
| W12X26 | 38,7 | 1 250 | 1,250 | 32,3 |
| W12X40 | 60 | 1 380 | 1,380 | 23,0 |
| W12X50 | 74 | 1 400 | 1,400 | 18,9 |
| W14X30 | 44 | 1 350 | 1,350 | 30,7 |
| W14X43 | 64 | 1 470 | 1,470 | 23,0 |
| W16X31 | 46,1 | 1 340 | 1,340 | 29,1 |
| W16X50 | 75 | 1 510 | 1,510 | 20,1 |
| W18X35 | 52 | 1 480 | 1,480 | 28,5 |
| W18X50 | 74 | 1 640 | 1,640 | 22,2 |
| W21X44 | 66 | 1 670 | 1,670 | 25,3 |
| W21X62 | 92 | 1 860 | 1,860 | 20,2 |
| W24X55 | 82 | 1 870 | 1,870 | 22,8 |
| W24X76 | 113 | 2 080 | 2,080 | 18,4 |
| C6X8.2 | 12,2 | 480 | 0,480 | 39,3 |
| C10X15.3 | 22,8 | 747 | 0,747 | 32,8 |
| C12X20.7 | 30,8 | 879 | 0,879 | 28,5 |
| L2X2X1/4 | 4,7 | 203 | 0,203 | 43,2 |
| L3X3X1/4 | 7,3 | 305 | 0,305 | 41,8 |
| L4X4X3/8 | 14,6 | 406 | 0,406 | 27,8 |
| L6X6X1/2 | 29,2 | 610 | 0,610 | 20,9 |

**Conclusión operativa:** el rango real para acero estructural corriente es **≈18-35 m²/ton**, subiendo
a 40-52 m²/ton en perfiles ligeros. La “regla de bolsillo” de 25 m²/ton cae dentro del rango pero
**[NO VERIFICADA]** en ninguna fuente: **el motor debe calcular `PB/W` perfil por perfil**, que es exacto.

### 6.5 Soldadura

**Lo que sí es normativo — RNE E.090, Tabla 10.2.4 “Tamaño mínimo de soldaduras de filete”:**

| Espesor de la parte unida más gruesa (mm) | Tamaño mínimo de filete (mm) |
|---|---|
| Hasta 6 inclusive | 3 |
| Sobre 6 hasta 13 | 5 |
| Sobre 13 hasta 19 | 6 |
| Sobre 19 | 8 |

*(«Debe emplearse soldadura en sólo una pasada»; el tamaño máximo se rige por 10.2.2b.)*

**Metrado:** la Norma de Metrados **no tiene partida de soldadura por ml** — la declara *incluida* en
las partidas de armado y montaje (OE.2.4). El “ml de soldadura” es una partida de contrato/taller,
no de norma.

**Metal depositado (aritmética, apoyada en ρ = 7 850 kg/m³ de E.020):**
```
Filete de cateto z (mm), sección triangular:  área = z²/2   (+~10 % si el filete es convexo)
kg de metal depositado por metro = z² × 3,925e-3
   z = 3 mm → 0,035    z = 6 mm  → 0,141
   z = 4 mm → 0,063    z = 8 mm  → 0,251
   z = 5 mm → 0,098    z = 10 mm → 0,393
Electrodo consumido = metal depositado / eficiencia de deposición
```
**[NO VERIFICADO]** — las **eficiencias de deposición por proceso** (SMAW, FCAW, GMAW, SAW) no se
obtuvieron de fuente citable (Soldexa redirige a ESAB, que bloquea; el Manual Oerlikon/EXSA no está
archivado). **No se estiman.** Dejar la eficiencia como parámetro configurable.

### 6.6 Norma E.090 — aceros estructurales admitidos ✔ VERIFICADO

Fuente: **RNE E.090 Estructuras Metálicas**, *El Peruano*, 10 de junio de 2006, sección **1.3.1a
Designaciones ASTM** (`RNE-E090-Estructuras-Metalicas.pdf`;
https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo3/02_E/RNE2006_E_090.pdf):

A36 (AASHTO M270 Gr.36) · A53 Gr.B (tubos redondos negros y galvanizados) · A242 · **A500** (tubos
conformados en frío) · A501 (conformados en caliente) · A514 · A529 · A570 Gr.275/310/345 · **A572**
(AASHTO M270 Gr.50) · A588 · A606 · A607 · A618 · A852 · A709 Gr.36/50/50W/70W/100/100W.

> 🚨 **ASTM A992 NO figura en E.090** (verificado por búsqueda de texto: cero apariciones). E.090 es de
> 2006 y sigue el AISC ASD/LRFD de los años 90. Sin embargo **Aceros Arequipa comercializa sus vigas WF
> bajo A36/A572/A992**. Es una brecha real entre norma vigente y mercado: el motor debería marcarla en
> la memoria de cálculo cuando el usuario especifique A992.

Otras disposiciones útiles: §1.3.1b permite acero no identificado solo en elementos secundarios (con
superficie conforme a ASTM A6); §1.3.1c fija requisitos Charpy (27 J a +20 °C) para perfiles pesados
Grupos 4 y 5 de ASTM A6 empalmados con soldadura de penetración total, y para planchas > 50 mm.

### 6.7 Lo que falta cerrar en perfiles

| Faltante | Estado |
|---|---|
| **AISC Code of Standard Practice (ANSI/AISC 303)** | **[NO VERIFICADO]** — aisc.org bloquea el acceso automatizado (403/404). No se cita ninguna clausula sobre peso facturable ni reglas de conexiones |
| **Consumo de electrodo por metro de cordon (kg/m) y eficiencias de deposicion** | **[NO VERIFICADO]** — Soldexa redirige a ESAB (bloqueado); el Manual Oerlikon/EXSA no esta archivado. Solo se entrega la aritmetica del metal depositado |
| **Porcentajes de desperdicio (2-5 %) y de conexiones (5-10 %)** | **[NO VERIFICADO]** — sin fuente primaria peruana ni AISC. Tratar como parametros configurables, no como dato normativo |
| **Regla de bolsillo de 25 m2/ton de pintura** | **[NO VERIFICADO]** — usar PB/W de la base AISC, que si es exacto |
| **kg/m de los perfiles conformados en frio C, Z, U de Tupemesa** | El fabricante no los publica. Calcular por ancho desarrollado x espesor x 7850 |
| **Precor** | El dominio precor.com.pe no resuelve DNS. **Calaminon**: no auditado |
| **Catalogo completo de SiderPeru / Gerdau Peru** | El sitio devuelve 403 a peticiones automatizadas. Solo se obtuvo la ficha de Barras Tee (que ademas **no publica kg/m**). Faltan angulos, canales, planchas y barras de SiderPeru |
| **Tabla metrica completa de angulos A36 de Aceros Arequipa** | El PDF publicado **se corta en 38x38x2,0** (confirmado renderizando la pagina). No hay 40x40, 50x50, 65x65 ni 75x75 metricos publicados |
| **Vigas WF de Aceros Arequipa en kg/m** | El catalogo solo publica lb/pie; la conversion es exacta (x1,4881639) pero el fabricante no publica la columna en kg/m |
| **Gerdau Corsa (Mexico)** | Descargado, pero sus tablas son imagenes y usa nomenclatura mexicana (IR/IE). No se extrajeron datos |
| **Licencia de la AISC Shapes Database** | Verificar terminos antes de redistribuirla dentro de un producto comercial |

---

## 7. Reglas operativas para el motor de cálculo (síntesis)

### 7.1 Invariantes que el motor NUNCA debe violar

| # | Regla | Fuente |
|---|---|---|
| R1 | El **metrado de acero** no incluye desperdicio, alambre, dados ni accesorios. El desperdicio vive solo en el APU. | F1 OE.2.3 |
| R2 | La **longitud** de cada barra **sí** incluye ganchos, dobleces y traslapes. | F1 OE.2.3 |
| R3 | Se agrupa **por diámetro**, se multiplica por el peso unitario, y **luego** se suman los pesos parciales. | F1 OE.2.3 |
| R4 | Una **intersección** entre elementos que se cruzan se mide **una sola vez**. | F1 OE.2.2.1, OE.2.2.6, OE.2.3.6.1, OE.2.3.8 |
| R5 | La **columna atraviesa el nudo** (se mide de cara superior de entrepiso a cara superior de entrepiso); la **viga se mide entre caras de columnas**; la **losa termina en el costado de la viga**. | F1 OE.2.3.7, .8, .9 |
| R6 | El **peralte de la viga incluye el espesor de losa empotrado**. | F1 OE.2.3.8 |
| R7 | El **encofrado** es área de **contacto** con el concreto, **salvo aligerados y nervadas**, donde es la **proyección**. | F1 OE.2.3, OE.2.3.9.2, OE.2.3.9.4 |
| R8 | El **encofrado de escaleras**: solo el **fondo** del tramo inclinado; costados, contrapasos y frisos se metran adicionalmente. | F1 OE.2.3.10 |
| R9 | El **acero de arranque de columnas** se carga a la **columna**, no a la zapata / viga de cimentación / losa de cimentación. | F1 OE.2.3.1, .2, .3, .4 |
| R10 | En **muros y placas** de concreto se **descuentan los vanos** de puertas y ventanas. | F1 OE.2.3.6.2 |
| R11 | En **albañilería** las áreas son **netas**: se descuentan vanos y vacíos. | F1 OE.3.1 |
| R12 | Los **ladrillos de techo** se computan en **cantidad neta** (sin desperdicio) y se **deducen** en tramos con ensanche de vigueta. | F1 OE.2.3, OE.2.3.9.2 |
| R13 | El **encofrado “cara vista”** va en partida separada del “corriente”; el **encofrado de una cara** separado del de **dos caras**. | F1 OE.2.3, OE.2.3.6.1 |
| R14 | Los aligerados de distinto sistema (convencional vs. vigueta prefabricada) **se separan aunque compartan la unidad m²**, porque su costo unitario difiere. | F1 OE.2.3.9.3 |

### 7.2 Pseudocódigo de la longitud desarrollada de una barra

```python
def longitud_desarrollada(tramos, dobleces, ganchos, db, k_doblado):
    """
    tramos     : dimensiones medidas out-to-out o entre intersecciones de ejes
    dobleces   : lista de angulos de doblez intermedios (grados)
    ganchos    : lista de ('90'|'180'|'135e'|'135s'|'90e', ...)
    k_doblado  : D/db  -> 6 (barra longitudinal <= 1"), 8 (1 1/8"-1 3/8"), 4 (estribo <= 5/8")
    """
    R = (k_doblado + 1) * db / 2.0          # radio del eje de la barra
    L = sum(tramos)

    # 1) Deduccion por cada doblez intermedio medido a la interseccion de ejes
    for ang in dobleces:
        a = math.radians(ang)
        L -= 2 * R * math.tan(a / 2) - R * a      # para 90 grados = 0.4292 * R

    # 2) Ganchos de extremo (longitud anadida desde el punto de tangencia)
    EXT = {'90': 12*db, '180': max(4*db, 65.0),
           '90e': 6*db, '135e': 6*db, '135s': max(8*db, 75.0)}
    ANG = {'90': 90, '180': 180, '90e': 90, '135e': 135, '135s': 135}
    for g in ganchos:
        L += math.radians(ANG[g]) * R + EXT[g]

    # 3) Traslapes: se suman aparte, segun clase A/B y ubicacion permitida
    return L
```

### 7.3 Chequeos de coherencia que el motor debería reportar

1. `peso_total_kg` vs. `cuantía` — la cuantía de columnas debe caer entre **1 % y 6 %** del área bruta
   (E.060 21.6.3.1); fuera de ese rango, avisar.
2. Traslapes de columnas ubicados **fuera de la mitad central** → advertencia (E.060 21.6.3.2).
3. Traslapes de vigas dentro de **2·h** desde la cara del nudo → advertencia (E.060 21.5.2.3).
4. Barras > 1 3/8" con traslape → **error** (E.060 12.14.2.1).
5. Longitud desarrollada de una pieza > **12 m** (barra comercial máxima) sin traslape declarado → error.
6. Aligerado con `espaciamiento libre > 750 mm` o `losa superior < 50 mm` → error (E.060 8.11).
7. `Σ volumen columnas + vigas + losas` vs. `volumen bruto del nivel` → detectar solapes por mal uso de R5.

---

## 8. Estado de verificación — resumen ejecutivo

### 8.1 Verificado en fuente primaria (usar con confianza)

| Dato | Fuente |
|---|---|
| Pesos y áreas de las 10 barras comerciales peruanas (6 mm … 1 3/8") | Hoja técnica Aceros Arequipa (F4/F5/F6) |
| Ganchos estándar, gancho sísmico, diámetros mínimos de doblado | E.060 7.1, 7.2, 21.1 |
| Fórmulas de ld, ldg, ldc, empalmes A/B y restricciones sísmicas | E.060 cap. 12 y cap. 21 |
| Recubrimientos mínimos | E.060 7.7.1 |
| Todas las reglas de medición de concreto, encofrado, acero, albañilería y estructuras metálicas | Norma de Metrados RD 073-2010-VIVIENDA |
| Restricciones geométricas del aligerado | E.060 8.11 |
| Peso propio del aligerado (17/20/25/30 cm) | E.020 Anexo 1 |
| Pesos unitarios de materiales (acero 7 850, concreto armado 2 400 kg/m³…) | E.020 Anexo 1 |
| 8,33 ladrillos/m² y concreto 0,080 / 0,087 / 0,100 m³/m² | Aceros Arequipa, *Manual del Maestro Constructor* |
| Fórmula de unidades por m² y de mortero en albañilería | Aceros Arequipa, *Manual del Maestro Constructor* |
| Rendimientos de KK 18 huecos, KK 30 %, pandereta, tabicón, bloqueta | Fichas técnicas Pirámide v03, Lark, Maxx |
| Espesor de junta 10-15 mm, Tabla 1 y Tabla 4 | E.070 Art. 4.1.2, 3.1.2, 3.2.4 |
| Geometría de detallado de ganchos (Hook A, D, J) | INDOT 703-B-316d (ACI 318-14 + CRSI MSP) |
| Ángulos, canales U, tees, platinas, barras y tubos de Aceros Arequipa (kg/m) | Hojas técnicas del fabricante |
| Perfiles W, C y L de AISC (kg/m, área, dimensiones, perímetro de pintura PB) | AISC Shapes Database v15.0 |
| Masa de planchas estriadas LAC (kg/m²) | Hoja técnica Aceros Arequipa |
| Tamaño mínimo de filete de soldadura | E.090 Tabla 10.2.4 |
| Lista de aceros estructurales admitidos | E.090 §1.3.1a |

### 8.2 NO verificado — requiere cierre antes de producción

| # | Dato | Por qué falta | Riesgo |
|---|---|---|---|
| 1 | **Porcentajes de desperdicio de acero (CAPECO)** | La publicación de CAPECO no es de libre descarga; las copias en Scribd/Studocu/Academia no son fuentes admisibles | Medio — solo afecta al APU, no al metrado |
| 2 | **Pesos de la serie métrica Ø10, Ø16, Ø20, Ø25, Ø32** | Ningún fabricante peruano publica esa tabla (solo produce 6, 8 y 12 mm) | Bajo — la masa teórica es exacta y universal |
| 3 | **Concreto del aligerado h = 30 cm (0,1125 m³/m²)** | La tabla de Aceros Arequipa llega solo hasta h = 25 | Bajo — la fórmula que sí publica AA lo reproduce |
| 4 | **Aligerados h = 12/13/15 cm y h = 35 cm** | No hay tabla publicada; E.020 no norma su peso propio | Medio — h = 12 cm es geométricamente inviable con losa de 5 cm |
| 5 | **Bloques de concreto (39×19×…)** | Ningún fabricante peruano publica ficha accesible | **Alto** si el proyecto usa bloque de concreto |
| 6 | **Ladrillo sílico-calcáreo** | Sin fabricante peruano con ficha en línea | **Alto** — la Norma de Metrados sí tiene partidas para él |
| 7 | **Casetones de poliestireno** | Sin fabricante peruano con ficha | Medio |
| 8 | **“36 und/m²” de Lark** y **“46 und/m²”** de la web de Pirámide | No declaran junta / contradicen su propia ficha | Bajo — usar los valores calculados |
| 9 | **Trazabilidad del PDF de la Norma de Metrados** | Ambas copias llevan un pie de página añadido por un tercero | Bajo — el texto normativo coincide, pero conviene la copia del MVCS |
| 10 | **Consumo de electrodo por metro de cordón y eficiencias de deposición** | Soldexa redirige a ESAB (bloqueado); manual Oerlikon/EXSA no archivado | Medio si se presupuesta soldadura por ml |
| 11 | **% de desperdicio y de conexiones en estructura metálica (2-5 % / 5-10 %)** | Sin fuente primaria peruana ni AISC | Medio — parámetro configurable |
| 12 | **kg/m de conformados en frío C, Z, U (Tupemesa)** | El fabricante publica medidas y espesores, pero no pesos | Medio — calculable por ancho desarrollado |
| 13 | **Catálogo completo de SiderPerú/Gerdau Perú** | El sitio devuelve 403 a peticiones automatizadas | Medio |
| 14 | **Ángulos métricos A36 > 38×38 de Aceros Arequipa** | El PDF publicado se corta en 38×38×2,0 | Bajo |
| 15 | **Licencia de la AISC Shapes Database** | Es el archivo original de AISC obtenido de un espejo público | **Alto si se redistribuye comercialmente** — verificar términos |

### 8.3 Divergencias entre fuentes que el motor debe exponer, no ocultar

1. **E.060 vs. ACI 318 en ld para barras > 3/4"** — E.060 usa coeficiente 2,1 donde ACI usa 1,7:
   E.060 da ld ≈ 19 % menor. Exponer `norma: "E.060" | "ACI318"`.
2. **λ (concreto liviano)** — E.060: numerador, 1,0/1,3. ACI: denominador, 1,0/0,75. No intercambiables.
3. **Mínimo de ldg** — E.060 12.5.1 dice “el **menor** valor entre 8 db y 150 mm”; ACI dice “el mayor”.
   Es un error de redacción de E.060: **usar el mayor**.
4. **King Kong 18 huecos: 9×12,5×23 (fabricantes) vs. 9×13×24 (tabla de Aceros Arequipa)** —
   40 vs. 41,67 und/m² (+4 %). Mantener **dos entradas separadas**.
5. **Rendimientos “netos” (metrado) vs. “comerciales” (con 5-8 % de desperdicio)** — los fabricantes
   publican los segundos; la Norma de Metrados exige los primeros.
6. **1 3/8": db comercial 34,925 mm vs. db real 35,81 mm (ASTM #11)** — usar 35,81.
7. **Unidad de medida de la estructura metálica: Und. (norma) vs. kg (mercado)** — emitir ambas y
   declararlo en el reporte.
8. **ASTM A992 no está en E.090** pero sí se vende en el mercado peruano — marcarlo en la memoria de cálculo.
9. **Erratas detectadas en la ficha de tubos A500 de Aceros Arequipa** (§6.3.7) — el motor debe usar
   los valores corregidos y avisar al usuario.

---

## 9. Errores de fuente detectados (registrar en el motor)

| # | Fuente | Error | Corrección |
|---|---|---|---|
| E1 | **E.060 12.5.1** | Dice “no menor que **el menor** valor entre 8 db y 150 mm”; ACI 318 dice “el mayor” | Usar **máx(8 db; 150 mm)** |
| E2 | **E.060 Tabla 12.1** | Coeficiente **2,1** para barras > 3/4" aplica ψs = 0,8 a barras grandes, que ACI no permite (ACI usa 1,7) | Exponer opción `norma: E.060 \| ACI318` |
| E3 | **Aceros Arequipa, hoja técnica A615** | Denomina la barra grande “1 3/8"” (34,925 mm) pero publica el área y perímetro de la ASTM #11 (35,81 mm) | Usar db = 35,81 mm |
| E4 | **AA, ficha tubos A500** | 38 × 38 × 2,5 figura 3,787 kg/m (incoherente con la serie) | ≈ **2,787** |
| E5 | **AA, ficha tubos A500** | 50 × 50 × 1,8 figura 2,274 kg/m (transposición de dígitos) | ≈ **2,724** |
| E6 | **AA, ficha tubos A500 (redondos)** | Columnas de 2 mm y 2,5 mm corridas una fila desde 1 1/2"; dos números superpuestos en esa celda | Valores recalculados en §6.3.7 |
| E7 | **Web de Pirámide** | Publica 46 und/m² para el KK 18 Hércules, contradiciendo su propia ficha v03 | Usar la ficha PDF |
| E8 | **Ficha de Lark** | Publica 36 und/m² sin declarar el espesor de junta (equivale a ~20 mm, no conforme E.070) | Usar el valor calculado |
| E9 | **PDF del CIP de E.070** | Es la **propuesta**, con el artículo numerado 10.7 en vez de 4.1.2 | Citar la edición SENCICO |

---
</content>
</invoke>
