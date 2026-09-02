# 03 — Movimiento de tierras e instalaciones (sanitarias, eléctricas, mecánicas)

> Investigación para el motor de metrados de **metra-ai**.
> Fecha: 2026-09-02. Todo dato numérico lleva fuente con URL. Lo no confirmado va marcado
> explícitamente como **NO VERIFICADO** y en el JSON con `"verificado": false`.
>
> Archivo de datos para código: [`03-tablas-tierras-instalaciones.json`](./03-tablas-tierras-instalaciones.json)

---

## 0. Jerarquía de fuentes usada

| Nivel | Fuente | Uso |
|---|---|---|
| 1 — Norma de medición | **Norma Técnica Metrados para Obras de Edificación y Habilitaciones Urbanas**, RD 073-2010-VIVIENDA/VMCS-DNC | Define **qué** partida existe, su **unidad** y su **forma de medición**. Es la autoridad para el motor. |
| 2 — Norma de diseño (RNE) | OS.050, OS.070, IS.010, EM.010, G.050, E.050 | Define geometrías mínimas (recubrimientos, diámetros, pendientes, taludes) que alimentan el cálculo. |
| 3 — Código sectorial | CNE-Utilización 2006 (RM 037-2006-MEM/DM) | Reglas eléctricas cuantificadas (secciones mínimas, colas en cajas, resistencia de PAT). |
| 4 — Especificación de empresa prestadora | SEDAPAL CTPS-ET-002 y CTPS-ET-008 | Pruebas hidráulicas y montaje de redes. |
| 5 — Estándar internacional | ASTM D2321, EN 1610, OSHA 29 CFR 1926 Subpart P, SMACNA | Complemento donde el RNE no da tabla (p. ej. ancho de zanja por diámetro). |
| 6 — Catálogo de fabricante | Pavco Wavin, Nicoll, Tigre, Indeco/Nexans, Ceper | Diámetros comerciales, espesores, pesos. |

**Regla de oro del motor:** el RNE y la Norma de Metrados mandan sobre el catálogo; el catálogo
sólo aporta dimensiones físicas del producto.

---

# A. MOVIMIENTO DE TIERRAS

## A.1 Cómo manda medir la Norma de Metrados peruana

Fuente única de esta sección: **RD 073-2010-VIVIENDA**, capítulos OE.2.1 (Edificación) y HU.3.4
(Habilitaciones Urbanas).
PDF local: `docs/normas/RD-073-2010-Norma-Metrados-mirror.pdf` ·
Resolución oficial: <https://spij.minjus.gob.pe/> (RD 073-2010-VIVIENDA/VMCS-DNC).

### A.1.1 Edificación (OE.2.1)

| Código | Partida | Unidad | Forma de medición (texto normativo resumido) |
|---|---|---|---|
| OE.2.1.1.1 | Nivelación | m² | Área del terreno a nivelar; se indica altura promedio de corte y relleno y clase de material. Comprende sólo hasta **30 cm**. |
| OE.2.1.1.2 | Nivelado apisonado | m² | Igual; se indica **número de capas** por apisonar (para el APU). |
| OE.2.1.2.1 | Excavación masiva / simple | m³ | `largo × ancho × altura` (o la geometría que corresponda). Altura **desde el fondo de cimentación hasta el nivel de terreno**. Se **clasifica por profundidad** y se abre partida aparte si hay napa freática o terreno especial. |
| OE.2.1.3 | Cortes | m³ | Volumen **natural** del corte, **sin esponjamiento**, por el **método del promedio de áreas extremas × longitud entre ellas**, sustentado en secciones transversales. |
| OE.2.1.4.1/2 | Relleno con material propio / de préstamo | m³ | Volumen **compactado** = volumen geométrico del vacío. En cimentaciones: `V_relleno = V_excavación − V_concreto`. En zanjas: `V_relleno = V_excavación − V_elemento`. Rellenos masivos: promedio de áreas extremas. |
| OE.2.1.5 | Nivelación interior y apisonado | m² | Área efectiva entre elementos de fundación; se indica número de capas. |
| OE.2.1.6 | Eliminación de material excedente | m³ | `V_eliminar = (V_excavado − V_relleno_compactado_con_material_propio) × factor de esponjamiento` (tabla en A.3.1). |
| OE.2.1.7 | Tablaestacado / entibado | m² | **Área neta protegida** = altura necesaria del tablaestacado × longitud. |

> ⚠️ **Regla crítica para el motor:** el esponjamiento **NO** se aplica al corte ni a la excavación
> (se miden en banco), **sólo** a la eliminación (OE.2.1.6) y a la eliminación de demoliciones
> (OE.1.1.6.1).

### A.1.2 Habilitaciones urbanas — redes enterradas (HU.3.4)

Aquí la unidad cambia radicalmente y es la trampa más común del metrado peruano:

| Código | Partida | Unidad | Forma de medición |
|---|---|---|---|
| HU.3.4.1.1 | **Excavación de zanjas** | **m (metro lineal)** | Se mide la **longitud** de la zanja, sin incluir estructuras. Partidas independientes **por diámetro nominal, tipo de terreno y profundidad**. |
| HU.3.4.1.2 | Excavación para estructuras | m³ | Volumen del material *in situ* antes de excavar = área horizontal promedio × altura. |
| HU.3.4.1.3 | Cortes | m³ | Volumen por levantamiento topográfico, **neto sin esponjamiento**. |
| HU.3.4.2.1 | **Refine y nivelación de zanjas** | **m** | Longitud de zanja, por diámetro y tipo de terreno. |
| HU.3.4.2.2 | Refine y nivelación para estructuras | m² | Área de la sección horizontal. |
| HU.3.4.3.1 | **Relleno y compactación de zanjas** | **m** | Longitud de zanja **descontando cámaras y buzones**. Agrupar por rango de tuberías y profundidad. **Incluye la cama o lecho de tubería** y el material selecto/seleccionado. |
| HU.3.4.3.2 | Relleno y compactación para estructuras | m³ | Volumen compactado; `V = V_excavación − V_elemento`. |
| HU.3.4.3.3 | Material de préstamo para rellenos | m³ | `V_préstamo = V_relleno_compactado_necesario − V_material_disponible_compactado`. Los esponjamientos se consideran **en el análisis de precios**, no en el metrado. |
| HU.3.4.4.2 | **Eliminación de excedente de zanjas** | **m** | Longitud de zanja. El esponjamiento va **en el APU**. |
| HU.3.4.4.3 | Eliminación de excedente de estructuras | m³ | `V = V_excavado − V_relleno_compactado`; esponjamiento en el APU. |

> ⚠️ **Consecuencia de diseño para metra-ai:** el motor debe soportar **dos modos de metrado de
> zanja**: (a) modo *edificación* → m³; (b) modo *habilitación urbana / redes* → **m lineal
> clasificado por (diámetro, tipo de terreno, rango de profundidad)**. El volumen se calcula
> igual internamente, pero la partida se **reporta** en metros y el volumen sólo alimenta el APU.

### A.1.3 Redes eléctricas subterráneas (HU.4.2)

| Código | Partida | Unidad | Regla |
|---|---|---|---|
| HU.4.2.4 | Zanjas para redes eléctricas | m | Longitud total de recorrido por sección. **Incluye** trazado, excavación, refine, nivelado, relleno, cernido, apisonado, compactado y eliminación de desmonte (todo en una sola partida). |
| HU.4.2.5 | Cruzadas | m | Longitud × número de vías; ancho total de la calle. |

---

## A.2 Métodos de cálculo de volúmenes — fórmulas

**Fuente principal (gubernamental, texto abierto):** WYDOT (Wyoming DOT), *Survey Manual,
Appendix F "Volume"*, rev. julio 2024.
PDF local: `docs/normas/WYDOT-Survey-Manual-AppF-Volume.pdf` ·
URL: <https://www.dot.state.wy.us/files/live/sites/wydot/files/shared/Highway_Development/Surveys/Survey%20Manual/Appendix%20F%20-%20Volume.pdf>

**Fuentes de confirmación:** University of Anbar, *Surveying 2* (Dr. Khamis Naba Sayl) —
<https://www.uoanbar.edu.iq/eStoreImages/Bank/2548.pdf> ·
Leonardo Casanova M., *Elementos de Geometría*, cap. Movimiento de tierra —
<https://sjnavarro.wordpress.com/wp-content/uploads/2008/08/movimiento-de-tierra1.pdf> ·
University of Washington, CIVE 316 *Borrow-Pit Method* —
<https://courses.washington.edu/cive316/lectures/lecture7/tsld013.htm> ·
Caterpillar *Performance Handbook*, Ed. 29 —
<http://courses.washington.edu/esrm468/468%20Class%20material/PHB29.pdf>

### A.2.1 Prisma recto (L × A × H)

```
V = B · h            B = área de la base, h = altura
```
Caso de la excavación de cimentación (OE.2.1.2): `V = largo × ancho × altura`.
WYDOT F-1. Es la fórmula que la Norma de Metrados asigna a excavaciones y cortes de geometría
regular.

### A.2.2 Áreas medias / end-areas (el método que exige la Norma de Metrados)

```
V = ½ · (A1 + A2) · L
```
- `A1`, `A2` = áreas de las secciones transversales extremas; `L` = distancia entre ellas.
- WYDOT F-9 advierte: **«exact only if A1 = A2»** — es exacto sólo si ambas áreas son iguales;
  en el resto de casos **sobrestima** el volumen.
- Caso degenerado `A2 = 0` (pirámide): `V = ⅓ · A · L` (WYDOT F-9).
- **Éste es el método que la RD 073-2010 exige explícitamente** para cortes (OE.2.1.3) y rellenos
  masivos (OE.2.1.4.1): «por el método del promedio de las áreas extremas multiplicado por la
  longitud entre ellas».

Acumulación por tramos (perfil completo):
```
V_total = Σ_i  ½ · (A_i + A_{i+1}) · L_i
```

### A.2.3 Método de las secciones transversales

Es la aplicación práctica de A.2.2: se levantan secciones transversales a intervalos regulares
(o en cada quiebre), se calcula el área de corte y el área de relleno **por separado** en cada
sección, y se acumulan **dos volúmenes independientes** (corte y relleno) con áreas medias o
prismoidal. Nunca se compensan área de corte con área de relleno dentro de la misma sección.

Área de una sección trapecial de plataforma de ancho `b`, altura `h` y talud `m` (H:V):
```
A = h · (b + m·h)
```

### A.2.4 Fórmula prismoidal

```
V = (L / 6) · (A1 + 4·Am + A2)
```
WYDOT F-10.

> ⚠️ **El error más frecuente del mundo con esta fórmula.** WYDOT F-10, texto literal:
> «The midpoint area is determined from **averaging the corresponding linear heights and widths**
> of the two end-areas and **not by averaging their areas**.»
> Es decir: `Am` se calcula construyendo una sección con las **dimensiones lineales promediadas**
> (alturas y anchos), **no** como `(A1+A2)/2`.
> Casanova lo dice igual en español: «Sus dimensiones serán el promedio de las dimensiones de las
> secciones extremas **y no el promedio de áreas**.»
> Si se usara `Am = (A1+A2)/2`, la fórmula prismoidal colapsaría idénticamente en la de áreas
> medias y no habría diferencia entre ambos métodos.

La prismoidal normalmente da **menos** volumen que áreas medias (caso pirámide: `A·h/3` exacto vs
`A·h/2` de áreas medias).

### A.2.5 Corrección prismoidal

```
CP = L · (h1 − h2) · (w1 − w2) / 12
```
- `h1`, `h2` = alturas al centro de cada sección extrema; `w1`, `w2` = anchos de talud a talud.
- Se **resta** al volumen de áreas medias: `V_prismoidal ≈ V_áreas_medias − CP`.
- WYDOT F-10/F-11.

### A.2.6 Malla / cuadrícula (grid o *borrow pit*)

Se divide el área en celdas rectangulares de lados `a × b` y se mide la altura de corte/relleno
en cada nodo de la retícula.

```
V = (a · b / 4) · (Σh₁ + 2·Σh₂ + 3·Σh₃ + 4·Σh₄)
```

El coeficiente de cada altura es **el número de celdas completas que comparten ese nodo**:

| Coef. | Significado | Ubicación típica |
|---|---|---|
| **h₁** | el nodo pertenece a **1** celda | esquinas exteriores de la retícula |
| **h₂** | pertenece a **2** celdas | nodos del borde |
| **h₃** | pertenece a **3** celdas | vértices entrantes en contornos irregulares |
| **h₄** | pertenece a **4** celdas | nodos interiores |

Univ. of Anbar (pág. 8-9), literal: «the heights of AEFG occur **once**, whilst the heights of
abcd occur **twice** and he occurs **four times**; one still divides by four to get the mean».
UW CIVE 316: `V = Σ(h_ij · n) · A / 4` — «multiply each height by the number of complete squares
it is common».

> ⚠️ El coeficiente **3** no aparece escrito de forma explícita en las fuentes abiertas
> consultadas; se **deduce** del mismo criterio («número de celdas que comparten el vértice»).
> El principio de ponderación sí está verificado. Marcado `verificado: false` sólo para h₃.

### A.2.7 Curvas de nivel

```
V = Σ_i  Δh · (A_i + A_{i+1}) / 2
```
- `Δh` = intervalo entre curvas de nivel; `A_i` = área encerrada por la curva de nivel *i*.
- Univ. of Anbar, pág. 9: «the average area of the adjacent contours is obtained… and the volume
  obtained by multiplying by the contour spacing (i.e., contour interval)».

> ⚠️ **Simpson aplicado a curvas de nivel: NO VERIFICADO.** La misma fuente dice explícitamente
> que «Use of the prismoidal formula is **seldom, if ever, justified** in this type of
> computation». Usar la regla trapezoidal.

### A.2.8 Tronco de pirámide / prismatoide

```
V = (h / 3) · (B1 + B2 + √(B1 · B2))
```
`B1`, `B2` = áreas de las bases paralelas, `h` = altura entre ellas. WYDOT F-7.
Útil para zapatas troncopiramidales, montículos y acopios cónicos.

### A.2.9 Zanja con taludes

**Caterpillar Performance Handbook, Ed. 29, pág. 4-159** (literal, con A = ancho de fondo,
C = ancho superior, B = profundidad):
```
Trench volume (Bm³/m)     = ½ · (A + C) · B
Spoil pile volume (Lm³/m) = (Bm³/m) × (1,00 + %Swell)
```
Con talud `m` (H:V) se tiene `C = A + 2·m·B`, luego `½·(A + A + 2mB)·B = B·(A + m·B)`, es decir:

```
V = L · h · (b + m·h)
```

confirmando la fórmula de A.4.5. (La fórmula base es literal de Caterpillar; el paso algebraico
es derivación directa.)

### A.2.10 Tabla de decisión para el motor

| Situación de entrada | Método a usar | Base |
|---|---|---|
| Excavación de zapata / cimiento corrido / zanja con geometría regular | **Prisma** `L×A×H` | RD 073-2010 OE.2.1.2 |
| Corte o relleno masivo con secciones transversales del proyecto | **Áreas medias** | RD 073-2010 OE.2.1.3 y OE.2.1.4.1 (obligatorio) |
| Secciones muy desiguales y se busca precisión | **Prismoidal** o áreas medias − corrección prismoidal | WYDOT F-10 |
| Nivelación de plataforma con levantamiento por retícula | **Grid / borrow pit** | Univ. Anbar / UW CIVE 316 |
| Volumen de embalse, laguna, cantera o botadero con curvas de nivel | **Curvas de nivel (trapezoidal)** | Univ. Anbar |
| Zanja de tubería con paredes inclinadas | `V = L·h·(b + m·h)` | Caterpillar 4-159 |
| Acopio cónico / troncopiramidal | **Tronco de pirámide** | WYDOT F-7 |

---

## A.3 Esponjamiento y contracción

### A.3.1 Tabla oficial peruana (la que debe usar el motor por defecto)

Ésta es la **única tabla de esponjamiento con rango normativo en el Perú**: está publicada dentro
de la propia Norma Técnica de Metrados (OE.2.1.6, "Eliminación de material excedente").

**Fuente:** RD 073-2010-VIVIENDA, OE.2.1.6, pág. 27 del PDF.
La norma cita a su vez: *Características Físicas de los Suelos*, Raúl S. Escalante, Cátedra
Ingeniería de Dragado, Escuela de Graduados de Ingeniería Portuaria, Argentina, 2007.
Texto literal de la norma: «Los valores anteriores son referenciales. **Cualquier cambio debe
sustentarse técnicamente.**»

| Tipo de suelo | Factor de esponjamiento (banco → suelto) |
|---|---|
| Roca dura (volada) | 1,50 – 2,00 |
| Roca mediana (volada) | 1,40 – 1,80 |
| Roca blanda (volada) | 1,25 – 1,40 |
| Grava compacta | 1,35 |
| Grava suelta | 1,10 |
| Arena compacta | 1,25 – 1,35 |
| Arena mediana dura | 1,15 – 1,25 |
| Arena blanda | 1,05 – 1,15 |
| Limos, recién depositados | 1,00 – 1,10 |
| Limos, consolidados | 1,10 – 1,40 |
| Arcillas muy duras | 1,15 – 1,25 |
| Arcillas medianas a duras | 1,10 – 1,15 |
| Arcillas blandas | 1,00 – 1,10 |
| Mezcla de arena/grava/arcilla | 1,15 – 1,35 |

**Uso en el motor:** `V_suelto = V_banco × F_esponjamiento`. Por defecto tomar el **valor medio**
del rango y exponer el rango al usuario para que lo ajuste con sustento técnico.

### A.3.2 Definiciones y conversiones banco ↔ suelto ↔ compactado

Las tres condiciones de volumen:

| Condición | Símbolo usual | Significado |
|---|---|---|
| **Banco** (*bank*, BCY / Bm³) | `V_B` | material en su posición natural, sin remover |
| **Suelto** (*loose*, LCY / Lm³) | `V_L` | material excavado, cargado en tolva o en acopio |
| **Compactado** (*compacted*, CCY / Cm³) | `V_C` | material colocado y compactado en el relleno |

**Fuentes de las fórmulas:** Nunnally, *Construction Methods and Management*, Ec. 2-4 a 2-9,
reproducidas en apuntes abiertos KSU CE-417 cap. 2 —
<https://faculty.ksu.edu.sa/sites/default/files/2.ce417-note-ch2.pdf> ·
Caterpillar *Performance Handbook* Ed. 29, págs. 23-2 y 23-15 —
<http://courses.washington.edu/esrm468/468%20Class%20material/PHB29.pdf>

```
Esponjamiento:        Swell %  = ( γ_banco / γ_suelto − 1 ) × 100
Contracción:          Shrink % = ( 1 − γ_banco / γ_compactado ) × 100

Load factor (LF):     LF = γ_suelto / γ_banco = 1 / (1 + Swell)
                      V_banco = V_suelto × LF
                      V_suelto = V_banco × (1 + Swell)

Shrinkage factor (SF): SF = γ_banco / γ_compactado = 1 − Shrink
                      V_compactado = V_banco × SF
                      V_banco      = V_compactado / SF
```

> **Swell y shrinkage se calculan siempre desde la condición banco.** No son inversos entre sí ni
> se cancelan: un material puede tener 25 % de esponjamiento y 10 % de contracción a la vez.
>
> ⚠️ Ojo con la nomenclatura: el «factor de esponjamiento» de la **Norma de Metrados peruana**
> (tabla A.3.1) es el multiplicador banco→suelto, es decir `(1 + Swell)`, **no** el *load factor*
> de Caterpillar, que es su inverso. Un factor peruano de 1,25 equivale a swell 25 % y a
> LF = 0,80.

### A.3.3 Tabla Caterpillar — densidades y load factors

**Fuente:** Caterpillar *Performance Handbook*, Ed. 29, Sección 28 «Tables», pág. 28-4 —
<http://courses.washington.edu/esrm468/468%20Class%20material/PHB29.pdf>
Las densidades y el *load factor* son **literales del manual**; la columna «Swell % calc» se
deriva de `Swell = 1/LF − 1` (el manual no imprime el porcentaje).

| Material | Suelta kg/m³ | Banco kg/m³ | Load factor (publicado) | Swell % *calc* |
|---|---|---|---|---|
| Arena seca, suelta | 1420 | 1600 | 0,89 | 12,4 |
| Arena húmeda (*damp*) | 1690 | 1900 | 0,89 | 12,4 |
| Arena mojada (*wet*) | 1840 | 2080 | 0,89 | 12,4 |
| Arena y grava, seca | 1720 | 1930 | 0,89 | 12,4 |
| Arena y grava, mojada | 2020 | 2230 | 0,91 | 9,9 |
| Arena y arcilla, suelta | 1600 | 2020 | 0,79 | 26,6 |
| Grava *pit run* (banco) | 1930 | 2170 | 0,89 | 12,4 |
| Grava seca | 1510 | 1690 | 0,89 | 12,4 |
| Grava seca 6-50 mm | 1690 | 1900 | 0,89 | 12,4 |
| Grava mojada 6-50 mm | 2020 | 2260 | 0,89 | 12,4 |
| Arcilla, lecho natural | 1660 | 2020 | 0,82 | 22,0 |
| Arcilla seca | 1480 | 1840 | 0,81 | 23,5 |
| Arcilla húmeda | 1660 | 2080 | 0,80 | 25,0 |
| Arcilla y grava, seca | 1420 | 1660 | 0,85 | 17,6 |
| Arcilla y grava, húmeda | 1540 | 1840 | 0,85 | 17,6 |
| Tierra seca compacta (*dry packed*) | 1510 | 1900 | 0,80 | 25,0 |
| Tierra húmeda excavada | 1600 | 2020 | 0,79 | 26,6 |
| Tierra vegetal / *loam* | 1250 | 1540 | 0,81 | 23,5 |
| *Top soil* (capa vegetal) | 950 | 1370 | 0,70 | 42,9 |
| Caliche | 1250 | 2260 | 0,55 | 81,8 |
| Mixto 25 % roca + 75 % tierra | 1570 | 1960 | 0,80 | 25,0 |
| Mixto 50 % roca + 50 % tierra | 1720 | 2280 | 0,75 | 33,3 |
| Mixto 75 % roca + 25 % tierra | 1960 | 2790 | 0,70 | 42,9 |
| Piedra chancada (*stone crushed*) | 1600 | 2670 | 0,60 | 66,7 |
| Caliza fragmentada | 1540 | 2610 | 0,59 | 69,5 |
| Granito fragmentado | 1660 | 2730 | 0,61 | 63,9 |
| Basalto | 1960 | 2970 | 0,67 | 49,3 |
| *Traprock* fragmentada | 1750 | 2610 | 0,67 | 49,3 |
| Arenisca (*sandstone*) | 1510 | 2520 | 0,60 | 66,7 |
| Lutita / *shale* | 1250 | 1660 | 0,75 | 33,3 |
| Yeso fragmentado | 1810 | 3170 | 0,57 | 75,4 |
| Escoria (*slag*) fragmentada | 1750 | 2940 | 0,60 | 66,7 |

> ⚠️ **«Limo» no figura** en la tabla Caterpillar. Para limo usar la fila «tierra común /
> *common earth*» de A.3.4 o la fila «limos» de la tabla peruana (A.3.1).

### A.3.4 Tabla con contracción y shrinkage factor (lo que Caterpillar no trae)

**Fuente:** Nunnally, Table 2-5 «Typical soil weight and volume change characteristics»,
reproducida en KSU CE-417 cap. 2, lámina 33 —
<https://faculty.ksu.edu.sa/sites/default/files/2.ce417-note-ch2.pdf>

| Material | Suelta kg/m³ | Banco kg/m³ | Compactada kg/m³ | Swell % | Shrink % | Load Factor | Shrinkage Factor |
|---|---|---|---|---|---|---|---|
| Arcilla | 1370 | 1780 | 2225 | 30 | 20 | 0,77 | 0,80 |
| Tierra común (*common earth*) | 1471 | 1839 | 2047 | 25 | 10 | 0,80 | 0,90 |
| **Roca volada** (*blasted*) | 1815 | 2729 | 2106 | 50 | **−30** | 0,67 | **1,30** |
| Arena y grava | 1697 | 1899 | 2166 | 12 | 12 | 0,89 | 0,88 |

Notas literales de la tabla: «Exact values vary with grain size distribution, moisture,
compaction…» y **«Compacted rock is less dense than is in-place rock»**.

> ⚠️ **Caso especial de la roca: contracción negativa.** 1 m³ de roca en banco produce **1,30 m³
> compactados**, no menos. Un motor que asuma `SF < 1` siempre calculará mal cualquier relleno con
> material rocoso. `SF` debe poder ser > 1.

### A.3.5 Corroboración en español

Víctor Yepes (Universitat Politècnica de València), *Coeficiente de esponjamiento en movimiento de
tierras* — <https://victoryepes.blogs.upv.es/2019/03/01/coeficiente-de-esponjamiento-en-movimiento-de-tierras/>

Define `FW = V_B/V_L`, `SW = (V_L − V_B)/V_B × 100`, `FC = V_C/V_B` y publica (γ banco t/m³ / FW):
caliza 2,61 / 0,59 · arcilla natural 2,02 / 0,83 · arena seca 1,60 / 0,89 · grava natural 2,17 /
0,89 · granito fragmentado 2,73 / 0,61 · tierra vegetal 1,37 / 0,69 · yeso fragmentado 3,17 /
0,57 · tierra húmeda 2,02 / 0,79. **Coincide con Caterpillar salvo redondeos.**

> ⚠️ **NO VERIFICADO:** no existe fuente peruana oficial (CAPECO, EG-2013, Norma de Metrados,
> OSCE) que fije explícitamente «20-30 % de esponjamiento para material común» en APU. Se buscó
> en el EG-2013 completo (1282 pág.), el Manual de Suelos/Geología/Geotecnia/Pavimentos (305 pág.)
> y el DG-2018 (285 pág.): **la palabra «esponjamiento» no aparece en ninguno de los tres**.
> El respaldo del rango 20-30 % es internacional (Nunnally: *common earth* 25 %; Caterpillar:
> tierra seca compacta 25,0 %, tierra húmeda excavada 26,6 %, arcilla 22-25 %). **No atribuirlo a
> norma peruana.** La única tabla peruana con rango normativo es la de A.3.1.

---

## A.4 Reglas de medición de excavación de zanjas

### A.4.1 Recubrimiento mínimo sobre la clave del tubo — RNE

**Agua potable — Norma OS.050, numeral 4.9**
PDF local: `docs/normas/RNE-OS.050-redes-agua.pdf` ·
URL: <https://cdn.www.gob.pe/uploads/document/file/2365676/21%20OS.050%20REDES%20DE%20DISTRIBUCION%20DE%20AGUA%20PARA%20CONSUMO%20HUMANO%20DS%20N%C2%B0%20010-2009.pdf>

| Situación | Recubrimiento mínimo sobre clave |
|---|---|
| Vías vehiculares, tubería principal | **1,00 m** (menores deben justificarse) |
| Zonas sin acceso vehicular | **0,30 m** |
| Ramal distribuidor de agua | **0,30 m** |

Otras reglas geométricas de OS.050 que fijan el trazo (y por tanto la longitud de zanja):
- Calles ≤ 20 m de ancho: **una** tubería principal a un lado, mínimo **1,20 m** del límite de propiedad.
- Calles > 20 m: **una línea a cada lado** de la calzada.
- Ramal distribuidor en vereda, a **≤ 1,20 m** del límite de propiedad.
- Distancia mínima horizontal entre tubería principal de agua y de aguas residuales paralelas: **2,00 m**.
- Distancia libre horizontal mínima entre ramales (distribuidor/colector) o ramal-tubería principal: **0,20 m**.
- Válvulas de interrupción: aislan sectores **≤ 500 m**; se ubican **a 4 m de la esquina**.
- Hidrantes: separación **≤ 300 m**; derivan de tuberías **≥ 100 mm**.
- Diámetro mínimo tubería principal: **75 mm** (vivienda), **150 mm** (industrial); conexión predial **12,50 mm**.

**Aguas residuales — Norma OS.070, numerales 4.6 a 4.8**
PDF local: `docs/normas/RNE-OS.070-redes-aguas-residuales.pdf` ·
URL: <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo2/03_OS/RNE2009_OS_070.pdf>

| Situación | Valor |
|---|---|
| Recubrimiento mínimo en vías vehiculares | **1,00 m** |
| Recubrimiento mínimo en vías peatonales / zonas rocosas | **0,30 m** |
| Recubrimiento mínimo excepcional (ramal colector + suelo rocoso) | **0,20 m** |
| Distancia mínima línea de propiedad ↔ tubería principal | **1,50 m** |
| Distancia mínima agua ↔ desagüe paralelos | **2,00 m** |
| Cruce agua sobre desagüe, separación vertical mínima | **0,25 m** (si no, protección de concreto 3 m a cada lado) |
| Eje de ramal colector | sobre eje de vereda, o a **0,50 m** del límite de propiedad |
| Diámetro nominal mínimo | **100 mm**; tubería principal que recoge ramal colector: **160 mm**; conexión predial **100 mm** |
| Pendiente mínima de la conexión predial | **15 ‰** |

### A.4.2 Cámaras de inspección — determinan cuántas unidades y dónde corta la zanja

**OS.070, numeral 4.8:**
- **Cajas de inspección** (en ramales colectores): separación máxima **20 m**.
- **Buzonetas**: en vías peatonales con profundidad **< 1,00 m** sobre clave, sólo hasta **DN 200 mm**; diámetro **0,60 m**.
- **Buzones**: cuando la profundidad es **> 1,00 m** sobre la clave.
  - Ø interior **1,20 m** para tuberías hasta **800 mm**.
  - Ø interior **1,50 m** para tuberías hasta **1200 mm**.
  - Tapa de acceso **0,60 m** de diámetro.
  - Dispositivo de caída cuando la altura de descarga al fondo es **> 1,00 m**.
- Separación máxima entre cámaras de inspección (Tabla N° 1 de OS.070):

| DN de la tubería (mm) | Distancia máxima (m) |
|---|---|
| 100 – 150 | 60 |
| 200 | 80 |
| 250 – 300 | 100 |
| Diámetros mayores | 150 |

Ubicación obligatoria de buzones/buzonetas: inicio de todo colector, todos los empalmes, cambios
de dirección, de pendiente, de diámetro y de material.

> **Uso en el motor:** con la longitud de un tramo y su DN, el motor puede **estimar el número de
> buzones** = `techo(L / distancia_máxima) + 1` y descontar su longitud del relleno de zanja
> (regla HU.3.4.3.1).

### A.4.3 Cajas de registro interiores — IS.010

**Norma IS.010, numeral 6.2 k)**
PDF local: `docs/normas/RNE-IS.010-instalaciones-sanitarias.pdf` ·
URL: <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo3/03_IS/RNE2006_IS_010.pdf>

Se instalan cajas de registro en redes exteriores en **todo cambio de dirección, pendiente,
material o diámetro y cada 15 m como máximo** en tramos rectos.

| Dimensiones interiores (m) | Diámetro máximo (mm) | Profundidad máxima (m) |
|---|---|---|
| 0,25 × 0,50 (10" × 20") | 100 (4") | 0,60 |
| 0,30 × 0,60 (12" × 24") | 150 (6") | 0,80 |
| 0,45 × 0,60 (18" × 24") | 150 (6") | 1,00 |
| 0,60 × 0,60 (24" × 24") | 200 (8") | 1,20 |

Para profundidades mayores → cámaras de inspección según OS.070.

### A.4.4 Ancho mínimo de zanja

El **RNE no publica una tabla de ancho de zanja por diámetro** (verificado leyendo OS.050 y
OS.070 completas). La única tabla peruana oficial y descargable es la de la **OPS/CEPIS**:

#### A.4.4.a Tabla peruana — OPS/CEPIS/05.147 UNATSABAR (usar por defecto)

**Fuente:** OPS/CEPIS/05.147, *Guía para el diseño y construcción de redes de distribución con
tuberías de PVC*, UNATSABAR, Lima 2005, numeral 6.1.
PDF local: `docs/normas/OPS-CEPIS-05.147-construccion-redes-distribucion.pdf` ·
URL: <https://sswm.info/sites/default/files/reference_attachments/OPS%202005a.%20Construcci%C3%B3n%20de%20redes%20de%20distribuci%C3%B3n.pdf>

Regla base (texto literal): «Se dispondrán, como mínimo, **15 cm a cada lado de la tubería** para
poder realizar el montaje.» → `b = OD + 0,30 m`, redondeado a la tabla:

| Ø de la tubería (mm) | ≈ pulg | **Ancho de zanja (m)** |
|---|---|---|
| ≤ 63 | ≤ 2" | **0,35** |
| 90 | 3" | **0,35** |
| 110 | 4" | **0,40** |
| 160 | 6" | **0,40** |
| 200 | 8" | **0,50** |
| > 200 | > 8" | **NO VERIFICADO** — aplicar `OD + 0,30 m` o ASTM D2321 |

**Profundidad (numeral 6.5 c):** «El recubrimiento mínimo del relleno sobre la clave del tubo en
relación con el nivel del terreno será de **0,80 m**, salvo se tenga tránsito vehicular en cuyo
caso no deberá ser menor de **1,00 m**.» (Coincide con OS.050 para el caso vehicular.)

**Cruces con servicios existentes:** separación mínima **0,20 m** entre planos horizontales
tangentes.

#### A.4.4.b Cama de apoyo y relleno — OPS/CEPIS/05.147 numerales 6.3 y 6.4

| Concepto | Valor |
|---|---|
| **Cama de apoyo** — terreno normal y semirocoso | arena gruesa o gravilla, espesor **≥ 0,10 m** compactado, medido desde la parte baja del cuerpo del tubo |
| **Cama de apoyo** — terreno rocoso | mismo material, espesor **≥ 0,15 m** |
| Cama de apoyo — terreno inestable (arcillas expansivas, limo) | según recomendación del supervisor |
| Distancia mínima entre la pared exterior de la **unión** del tubo y el fondo de excavación | **0,05 m** |
| Cama especial (fundación no sólida) | gravilla de 25 mm con granulometría tabulada (1½"→100 %, 1"→90-100 %, ¾"→30-60 %, ½"→0-20 %, N°4→0-5 %) |
| **Primer relleno** (compactado) | desde la cama de apoyo **hasta 0,30 m por encima de la clave**, con **material selecto**, capas de **0,10 m** terminadas, pisón manual de **20 a 30 kg** |
| **Segundo relleno** (compactado) | del primer relleno hasta el nivel superior del terreno, con **material seleccionado**, capas **≤ 0,15 m**, pisón manual |
| Relleno de estructuras complementarias | capas horizontales de **0,15 a 0,30 m** |

**Sobre-excavación** (numeral 6.1 b): se distingue **autorizada** (material inapropiado en el
fondo: sin compactar, orgánico, basura, fangoso) de **no autorizada** (negligencia del
constructor). En **ambos casos** el constructor debe rellenar todo el espacio de la
sobre-excavación con material acomodado y/o compactado, con orden registrada en el cuaderno de
obra. → Para el motor: la sobre-excavación **no genera partida adicional de pago** por sí sola.

**Unidades de medida que fija esta guía** (coinciden con HU.3.4 de la Norma de Metrados):
excavación de zanjas → **m**; excavación para estructuras → **m³**; refine y nivelación → **m**;
cama de apoyo → **m**; relleno de tuberías → **m**; relleno de estructuras/cimientos → **m³**;
instalación de tuberías → **m**.

> ⚠️ **«Relleno lateral» como partida normada separada: NO VERIFICADO.** No aparece con ese nombre
> en ninguna fuente peruana oficial; queda absorbido en el *primer relleno*.

Complemento para alcantarillado: **OPS/CEPIS/05.169 UNATSABAR** —
`docs/normas/OPS-CEPIS-05.169-alcantarillado.pdf` ·
<https://sswm.info/sites/default/files/reference_attachments/CEPISO~1.PDF>
(profundidad máxima recomendada 5,0 m; distancia mínima a cables eléctricos 1,0 m).

#### A.4.4.c Estándares internacionales (para diámetros fuera de tabla)

**ASTM D2321** — *Standard Practice for Underground Installation of Thermoplastic Pipe for Sewers
and Other Gravity-Flow Applications*. Ancho mínimo de zanja, el **mayor** de:

```
b_min = OD + 0,406 m          (OD + 16 pulg)
b_min = 1,25 × OD + 0,305 m   (1,25·OD + 12 pulg)
```

Cama de apoyo (bedding): mínimo **0,10 m (4")** de material firme, estable y uniforme; si se
encuentra roca o material no cedente, mínimo **0,15 m (6")**.
Relleno inicial (zona del tubo) con material Clase I, II o III compactado al **90 % Proctor estándar**.

Fuentes secundarias que reproducen la regla (el estándar en sí es de pago):
- Northern Pipe, *PVC Sewer Pipe Installation Guide*: <https://northernpipe.com/wp-content/uploads/2024/04/PVC-Sewer-Pipe-Installation-Guide.pdf>
- Contech, *A2000 Standard Backfill (ASTM)*: <https://www.conteches.com/media/mf3htpv3/a2000-std-backfill-astm.pdf>
- Charlotte Pipe, *Burying Plastic Pipe in Underground DWV Applications*: <https://www.charlottepipe.com/articles/burying-plastic-pipe-in-underground-dwv-applications>

**EN 1610** — *Construction and testing of drains and sewers*. **NO VERIFICADO contra el texto
original** (norma de pago); valores tomados de resúmenes técnicos secundarios:

Tabla 1 — ancho mínimo en función del DN (ODh = diámetro exterior horizontal):

| DN | Ancho mínimo de zanja |
|---|---|
| ≤ 225 | ODh + 0,40 m |
| > 225 y ≤ 350 | ODh + 0,50 m |
| > 350 y ≤ 700 | ODh + 0,70 m |
| > 700 y ≤ 1200 | ODh + 0,85 m |
| > 1200 | ODh + 1,00 m |

Tabla 2 — ancho mínimo en función de la profundidad de zanja:

| Profundidad de zanja | Ancho mínimo |
|---|---|
| < 1,00 m | sin mínimo |
| ≥ 1,00 m y ≤ 1,75 m | 0,80 m |
| > 1,75 m y ≤ 4,00 m | 0,90 m |
| > 4,00 m | 1,00 m |

Fuentes secundarias: <https://www.unitracc.com/technical/books/rehabilitation-and-maintenance-of-drains-and-sewers/structure-and-limiting-conditions-of-sewer-systems-historical-outline/methods-of-construction-en/open-cut-methods-en/trench-width-en> ·
<https://civilweb-spreadsheets.com/drainage-design-spreadsheets/buried-pipe-design-spreadsheet/minimum-trench-width/> ·
Ficha del estándar: <https://standards.iteh.ai/catalog/standards/cen/8762de52-0030-4a8c-88ec-574bdec5f761/en-1610-2015>

**Anchos de zanja implícitos en el RNE G.050** (Anexo I.3, tablas de entibado): la norma peruana
tabula el diseño de apuntalamiento para anchos de zanja de **hasta 1,2 / 1,8 / 2,7 / 3,6 / 4,5 m**
y profundidades de **hasta 1,8 / 2,4 / 3,0 / 3,6 m**. No son mínimos por diámetro, pero sí son los
rangos que el motor debe usar al clasificar la partida de entibado.

### A.4.5 Volumen de zanja — fórmulas

Zanja de paredes verticales (caso normal en obra urbana con entibado):

```
V_zanja = L × b × H
```

Zanja con taludes (paredes inclinadas), talud `m` expresado como **H:V** (m horizontal por cada
1 vertical), ancho de fondo `b`:

```
Ancho superior:   B = b + 2·m·H
Área de sección:  A = H·(b + m·H)          [trapecio]
Volumen:          V = L · H · (b + m·H)
```

Volumen neto a rellenar (regla OE.2.1.4 / HU.3.4.3):

```
V_relleno = V_zanja − V_tubería − V_cama_de_apoyo
V_tubería = π/4 · OD² · L
V_cama    = L × b × e_cama
```

Volumen a eliminar (regla OE.2.1.6):

```
V_eliminar_banco  = V_excavado − V_relleno_con_material_propio
V_eliminar_suelto = V_eliminar_banco × F_esponjamiento
```

---

## A.5 Taludes

### A.5.1 Taludes admisibles — RNE G.050 Anexo I (obligatorio en Perú)

**Fuente:** Norma G.050 *Seguridad durante la Construcción*, Anexo I (informativo),
"Modelos para el diseño de taludes". La norma peruana adopta explícitamente la
**clasificación referencial de suelos Tipo A, B y C de la OSHA**.
PDF local: `docs/normas/RNE-G.050-seguridad-construccion.pdf` ·
URL: <https://cdn.www.gob.pe/uploads/document/file/2365155/05%20G.050%20SEGURIDAD%20DURANTE%20LA%20CONSTRUCCI%C3%93N%20DS%20N%C2%B0%20010-2009.pdf>

| Tipo de suelo (OSHA) | Talud máximo permitido (H:V) | Profundidad máxima | Ángulo aprox. |
|---|---|---|---|
| **A** — general | **¾ : 1** (0,75 H por 1 V) | hasta 6 m | ≈ 53° |
| **A** — corto plazo (abierto ≤ 24 h) | **½ : 1** | hasta 3,6 m | ≈ 63° |
| **B** | **1 : 1** | hasta 6 m | 45° |
| **C** | **1½ : 1** | hasta 6 m | ≈ 34° |

Variantes tabuladas en el mismo Anexo I:
- **Bancada simple / múltiple** (sólo suelos cohesivos): altura máxima de bancada **1,2 m**.
- **Porción inferior vertical sin soporte** (Tipo A): profundidad total ≤ **2,4 m**, lado vertical
  máximo **1,05 m**.
- **Porción inferior vertical con soporte**: el sistema de soporte debe extenderse al menos
  **46 cm (18")** sobre el lado vertical.
- **Capas mezcladas** (B sobre A, C sobre A, C sobre B, A sobre B, A sobre C, B sobre C): se
  aplica a cada capa el talud de su tipo, hasta 6 m de profundidad total.

> Para profundidades **> 6 m** la G.050 remite a diseño específico (no hay talud tabulado).

### A.5.2 Reglas de seguridad de G.050 que generan partidas de metrado

De la sección 23 de la G.050 (Excavaciones):

- Excavaciones donde el personal trabaje a **≥ 1,20 m** de profundidad: escalera de mano u otro
  acceso equivalente; **una escalera adicional por cada 7,60 m** de zanja; deben sobresalir
  **≥ 1,00 m** sobre el terreno.
- Material excavado: **no acumular a menos de 2 m** del borde de la zanja (en terrenos estables).
- Barreras de advertencia y protección: a **≥ 1,80 m** del borde; a **≥ 3,00 m** si hay
  vibraciones o tránsito de vehículos; y si la excavación supera **3 m** de profundidad,
  esa distancia se **aumenta 1 m por cada 2 m adicionales** de profundidad.
- Entibados/apuntalamientos/tablaestacados: obligatorios según análisis de trabajo (estudio de
  suelos). Se metran en **m²** de área neta protegida (OE.2.1.7).

### A.5.3 Taludes de corte y relleno en obras viales — MTC DG-2018

**Fuente:** MTC, *Manual de Carreteras: Diseño Geométrico DG-2018*.
PDF local: `docs/normas/MTC-Manual-Carreteras-DG-2018.pdf` ·
URL: <https://portal.mtc.gob.pe/transportes/caminos/normas_carreteras/documentos/manuales/Manual.de.Carreteras.DG-2018.pdf>

**Tabla 304.10 — Valores referenciales para taludes en corte (relación H:V)**, sección 304.10,
pág. 204 del manual:

| Altura de corte | Roca fija | Roca suelta | Grava | Limo arcilloso o arcilla | Arenas |
|---|---|---|---|---|---|
| < 5 m | 1:10 | 1:6 – 1:4 | 1:1 – 1:3 | 1:1 | 2:1 |
| 5 – 10 m | 1:10 | 1:4 – 1:2 | 1:1 | 1:1 | (*) |
| > 10 m | 1:8 | 1:2 | (*) | (*) | (*) |

(*) Requiere banquetas y/o estudio de estabilidad.
Notación **H:V** — «1:10» significa 1 horizontal por 10 verticales, es decir casi vertical.

**Tabla 304.11 — Taludes referenciales en zonas de relleno / terraplenes (relación V:H)**, pág. 208:

| Material | H < 5 m | 5 – 10 m | > 10 m |
|---|---|---|---|
| Gravas, limo arenoso y arcilla | 1:1,5 | 1:1,75 | 1:2 |
| Arena | 1:2 | 1:2,25 | 1:2,5 |
| Enrocado | 1:1 | 1:1,25 | 1:1,5 |

Reglas complementarias del mismo manual:
- **Banquetas obligatorias** en cortes de tierra **mayores a 7 m** de altura (Fig. 304.07, pág. 203);
  pendiente longitudinal máxima de banqueta **3 %**; banqueta siguiente **cada 10 m**.
- En transiciones corte > 4,00 m ↔ terraplén, los taludes se tienden a partir de que la altura se
  reduce a **2,00 m**, con alabeo **≥ 10,00 m** (pág. 208).

> ⚠️ **Atención al sentido de la relación:** la Tabla 304.10 usa **H:V** y la 304.11 usa **V:H**.
> El motor debe normalizar internamente a un único convenio (recomendado: `m = H/V`, el mismo de
> las fórmulas de A.2.9) y guardar el convenio de origen de cada dato.

### A.5.4 Sostenimiento según E.050

La Norma de Metrados (OE.2.2.5) remite a la **Norma E.050 Suelos y Cimentaciones** para los tipos
de sostenimiento temporal o definitivo de taludes de corte: pantallas ancladas, tablestacas,
pilotes continuos, muros diafragma, **calzaduras**, *nailings*. Se metran en m³ (concreto),
m² (encofrado) y kg (acero).

---

## A.6 Eliminación de material y viajes de volquete

### A.6.1 Volumen a eliminar

Regla de la Norma de Metrados (OE.2.1.6), ya citada en A.1.1:

```
V_eliminar_banco  = V_excavado − V_relleno_compactado_con_material_propio
V_eliminar_suelto = V_eliminar_banco × F_esponjamiento
```

donde `F_esponjamiento` sale de la tabla A.3.1 (`= 1 + Swell`).

Caterpillar pág. 4-159 lo escribe igual: `Spoil pile volume (Lm³/m) = (Bm³/m) × (1,00 + %Swell)`.

### A.6.2 Número de viajes de volquete

**Fuente con ejemplo resuelto:** Caterpillar *Performance Handbook* Ed. 29, pág. 23-3 —
<http://courses.washington.edu/esrm468/468%20Class%20material/PHB29.pdf>

Ejemplo literal del manual (construir 10 000 CCY con SF = 0,80, camión de 20 LCY colmado):
```
BCY          = CCY / SF = 10 000 / 0,80 = 12 500 BCY
Load (BCY)   = Capacity (LCY) × Load factor = 20 × 0,81 = 16,2 BCY/viaje
N° de viajes = 12 500 / 16,2 = 772 viajes
```

Expresado en volumen suelto, que es como trabaja un motor de metrados:

```
N_viajes = techo( V_suelto / (Cap_volquete_m3 × factor_llenado) )
V_suelto = V_banco × (1 + Swell)
```

**Factor de llenado** (*fill factor*), definición literal de Caterpillar, misma página:
«A fill factor of 87 % for a hauler body means that 13 % of the rated volume is not being used to
carry material. Buckets often have fill factors over 100 %.»

### A.6.3 Cómo se paga en el marco MTC (importante para no duplicar el esponjamiento)

**Fuente:** MTC, *Manual de Carreteras — Especificaciones Técnicas Generales para Construcción
EG-2013* (versión revisada julio 2013) —
<https://portal.mtc.gob.pe/transportes/caminos/normas_carreteras/documentos/manuales/MANUALES%20DE%20CARRETERAS%202019/MC-01-13%20Especificaciones%20Tecnicas%20Generales%20para%20Construcci%C3%B3n%20-%20EG-2013%20-%20(Versi%C3%B3n%20Revisada%20-%20JULIO%202013).pdf>

| Ítem | Texto literal | Ubicación |
|---|---|---|
| Medición de excavación | «La unidad de medida será el metro cúbico (m³) […] **de material excavado en su posición original**» → **se paga en banco, no suelto** | §202.21, pág. 162 |
| Préstamos | «solamente se medirán **en su posición original** los materiales aprovechables […] alternativamente […] en su posición final en la vía, **reduciéndolos a su posición original mediante relación de densidades**» | §202.21, pág. 162 |
| Transporte | «La unidad de pago de esta partida será el **metro cúbico-kilómetro (m³-km)** trasladado, o sea, el **volumen en su posición final de colocación**, por la distancia de transporte» | §700.05, pág. 1089 |
| Acarreo libre | Se descuenta la **distancia de acarreo libre de 120 m** en el criterio de centro de gravedad | §700.05, pág. 1089 |

> ⚠️ **Consecuencia para el motor:** en el marco MTC el esponjamiento **no se paga como
> sobre-volumen de excavación**; se absorbe en el rendimiento del equipo dentro del APU y en el
> criterio de transporte. Coincide con la Norma de Metrados (HU.3.4.4.3: «el factor por
> esponjamiento es considerado en el Análisis del Costo de la Partida»).
> **El esponjamiento debe aparecer una sola vez** en todo el presupuesto: o en el metrado de
> eliminación (edificación, OE.2.1.6) **o** en el APU (habilitaciones urbanas y obras viales),
> nunca en ambos.

> ⚠️ **NO VERIFICADO:** capacidades típicas de volquete en Perú (6 / 10 / 15 / 20 m³) con fuente
> oficial citable. Son cifras de catálogo comercial. La vía correcta para respaldarlas es el
> **Reglamento Nacional de Vehículos, D.S. 058-2003-MTC** (pesos máximos por configuración
> C2/C3/C4), que limita la carga útil y de ahí el volumen útil según la densidad suelta.

---

# B. INSTALACIONES SANITARIAS

## B.1 Partidas y unidades — Norma de Metrados OE.4

Fuente: RD 073-2010-VIVIENDA, capítulo OE.4 "Instalaciones Sanitarias".

| Código | Partida | Unidad | Forma de medición |
|---|---|---|---|
| OE.4.1.1 / .2 | Suministro de aparatos sanitarios / accesorios | **Und** | Conteo, en partidas distintas por tipo, material, características y grifería. |
| OE.4.1.3 / .4 | Instalación de aparatos / accesorios | **Und** | Conteo (sólo mano de obra), agrupando por dificultad de instalación. |
| OE.4.2.1 | **Salida de agua fría** | **Punto (Pto)** | **Se cuenta el número de puntos de salida.** Incluye tubería, accesorios, picado y resane de albañilería y mano de obra desde el ramal de distribución hasta el punto. |
| OE.4.2.2 | Redes de distribución | **m** | Metro lineal **sin descontar la longitud de los accesorios**. Partidas independientes por material y diámetro. Incluye canaletas en albañilería y excavación/relleno de zanjas. |
| OE.4.2.3 | Redes de alimentación | **m** | Igual que .2.2, desde la conexión domiciliaria o el almacenamiento hasta las redes de distribución. |
| OE.4.2.4 | Accesorios de redes de agua | **Und** | Conteo, agrupado por tipo de material y diámetro. |
| OE.4.2.5 | Válvulas | **Und** | Conteo, agrupado por tipo de material y diámetro. |
| OE.4.2.6 | Almacenamiento de agua (tanques prefabricados) | **Glb** | Por forma, capacidad y material. **No incluye obras civiles**; cisternas y reservorios van como estructuras. |
| OE.4.3.1 | **Salida de agua caliente** | **Punto (Pto)** | Conteo de puntos. |
| OE.4.3.2 | Redes de distribución de agua caliente | **m** | Sin descontar accesorios. |
| OE.4.3.3 / .4 | Accesorios / válvulas de agua caliente | **Und** | Conteo por material y diámetro. |
| OE.4.3.5 | Equipos de producción de agua caliente | **Und** | Conteo por tipo y capacidad. |
| OE.4.4.1 | Sistema contra incendio — redes de alimentación | **m** | Sin descontar accesorios. Incluye tubería enterrada (con su zanja) y aérea/adosada. |
| OE.4.4.2 / .5 / .6 | Accesorios / válvulas / instalaciones especiales (rociadores, soportes, acoples) | **Und** | Conteo por tipo y dimensión. |
| OE.4.4.3 | Gabinetes contra incendio (tipo A o B) | **Und** | Conteo por tipo. Incluye caja, válvula, manguera y accesorios. |
| OE.4.4.4 | Junta antisísmica | **Und** | Conteo por dimensión. |
| OE.4.5.1 | Drenaje pluvial — red de recolección (tuberías o canaletas) | **m** | Metro lineal sin descontar accesorios. |
| OE.4.5.2 | Accesorios de drenaje pluvial | **Und** | Conteo por material y diámetro. |
| OE.4.6.1 | **Salidas de desagüe** | **Punto (Pto)** | **Se cuenta el número de puntos de entrada** de desagüe. |
| OE.4.6.2 | Redes de derivación (incluye montantes/bajantes, desagüe y ventilación) | **m** | Sin descontar accesorios; partidas independientes por material y diámetro. |
| OE.4.6.3 | Redes colectoras | **m** | Desde derivaciones/montantes hasta la conexión domiciliaria. |
| OE.4.6.4 | Accesorios de redes colectoras | **Und** | Conteo por material y diámetro. |
| OE.4.6.5.1 | **Cajas de registro** | **Und** | Conteo. |
| OE.4.6.5.2 | **Buzones** | **Und** | Conteo, agrupado **por rango de profundidad promedio y tipo de material**. |
| OE.4.6.6 | Instalaciones especiales (trampa de grasa, cámara de rejas, retención de sólidos) | **Und** o **Glb** | Conteo agrupado por dimensiones. |

**Redes exteriores en habilitación urbana (HU.3.5 a HU.3.9):**

| Código | Partida | Unidad | Regla |
|---|---|---|---|
| HU.3.5.1 | Suministro de tuberías | m | Longitud efectiva; **no incluye** la longitud de accesorios, cámaras ni buzones. Desperdicio va al APU. |
| HU.3.5.2 | Instalación de tuberías | m | Igual. |
| HU.3.6.1 / .2 | Suministro / instalación de accesorios | Und | Conteo por diámetro, tipo y clase. |
| HU.3.6.3 | Anclajes y dados de concreto para accesorios | Und (diseño típico) o m³/m²/kg (diseño especial) | Conteo por diámetro/tipo/clase. |
| HU.3.7 | Válvulas, grifos, medidores de caudal | Und o Glb | Suministro, componentes hidráulicos y montaje en partidas separadas. |
| HU.3.7.5 | Elementos de conexión domiciliaria (agua: corporation, batería de control; desagüe: cachimba/codo block) | Und | Conteo por conexión domiciliaria, diámetro y tipo. |
| HU.3.8.1 | Cámaras para válvulas | Und (diseño típico) | **Incluye el movimiento de tierras** necesario. |
| HU.3.9 | Buzones, buzonetas, cajas, cámaras de reunión | Und (diseño típico) | **Incluye el movimiento de tierras**. Agrupar por tipo, rango de profundidades y clasificación de terreno. |

> ⚠️ **Doble conteo a evitar en el motor:** las cámaras y buzones de HU.3.8/HU.3.9 **ya incluyen su
> movimiento de tierras**; por eso HU.3.4.3.1 obliga a **descontar buzones y cámaras** de la
> longitud de relleno de zanja.

## B.2 Criterios de diseño IS.010 que alimentan el metrado

Fuente: **Norma IS.010 Instalaciones Sanitarias para Edificaciones** (El Peruano, 11-06-2006).
PDF local: `docs/normas/RNE-IS.010-instalaciones-sanitarias.pdf`

### B.2.1 Pendientes mínimas de desagüe (numeral 6.2 c)

| Diámetro | Pendiente mínima **normativa** | Pendiente usual en ET de obra |
|---|---|---|
| 2" (50 mm) | **1,5 %** | 2,0 % |
| 3" (75 mm) | **1,5 %** | 1,5 % |
| **≥ 4" (100 mm)** | **1,0 %** | 1,0 % |

Texto normativo: «La pendiente de los colectores y de los ramales de desagüe interiores será
uniforme y no menor de 1 % para diámetros de 100 mm (4") y mayores; y no menor de 1,5 % para
diámetros de 75 mm (3") o inferiores.»

> ⚠️ **Corrección a un supuesto muy extendido:** el clásico «2" = 2 %» **no está en la IS.010**.
> Es práctica de especificaciones técnicas de obra (p. ej. ET Sanitarias en
> <https://cdn.www.gob.pe/uploads/document/file/4578538/3.2%20ET%20SANITARIAS%20440198.pdf>).
> El motor debe usar **1,5 %** como mínimo normativo para 2" y ofrecer 2 % como valor de proyecto.

### B.2.2 Diámetros mínimos y unidades de descarga (Anexo N° 6 de IS.010)

| Aparato | Ø mínimo de la trampa (mm) | Unidades de descarga |
|---|---|---|
| Inodoro con tanque | 75 (3") | 4 |
| Inodoro con tanque de descarga reducida | 75 (3") | 2 |
| Inodoro con válvula automática/semiautomática | 75 (3") | 8 |
| Inodoro con válvula de descarga reducida | 75 (3") | 4 |
| Bidé | 40 (1½") | 3 |
| Lavatorio | 32 – 40 (1¼" – 1½") | 1 – 2 |
| Lavadero de cocina | 50 (2") | 2 |
| Lavadero con trituradora | 50 (2") | 3 |
| Lavadero de ropa | 40 (1½") | 2 |
| Ducha privada | 50 (2") | 2 |
| Ducha pública | 50 (2") | 3 |
| Tina | 40 – 50 (1½" – 2") | 2 – 3 |
| Urinario de pared | 40 (1½") | 4 |
| Urinario de válvula automática/semiautomática | 75 (3") | 8 |
| Urinario de válvula de descarga reducida | 75 (3") | 4 |
| Urinario corrido | 75 (3") | 4 |
| Bebedero | 25 (1") | 1 – 2 |
| **Sumidero** | 50 (2") | 2 |

**Regla adicional (6.2 d):** «El diámetro mínimo que reciba la descarga de un inodoro será de
**100 mm (4")**.»

### B.2.3 Unidades de gasto (Hunter) — Anexos N° 1 y N° 2 de IS.010

**Aparatos de uso privado:**

| Aparato | Tipo | UG total | UG agua fría | UG agua caliente |
|---|---|---|---|---|
| Inodoro | con tanque, descarga reducida | 1,5 | 1,5 | — |
| Inodoro | con tanque | 3 | 3 | — |
| Inodoro | con válvula semiautomática/automática | 6 | 6 | — |
| Inodoro | con válvula de descarga reducida | 3 | 3 | — |
| Bidé | — | 1 | 0,75 | 0,75 |
| Lavatorio | — | 1 | 0,75 | 0,75 |
| Lavadero | — | 3 | 2 | 2 |
| Ducha | — | 2 | 1,5 | 1,5 |
| Tina | — | 2 | 1,5 | 1,5 |
| Urinario | con tanque | 3 | 3 | — |
| Urinario | con válvula semiautomática/automática | 5 | 5 | — |
| Urinario | con válvula de descarga reducida | 2,5 | 2,5 | — |
| Urinario | múltiple (por m) | 3 | 3 | — |

**Aparatos de uso público:**

| Aparato | Tipo | UG total | UG agua fría | UG agua caliente |
|---|---|---|---|---|
| Inodoro | con tanque, descarga reducida | 2,5 | 2,5 | — |
| Inodoro | con tanque | 5 | 5 | — |
| Inodoro | con válvula semiautomática/automática | 8 | 8 | — |
| Inodoro | con válvula de descarga reducida | 4 | 4 | — |
| Lavatorio | corriente | 2 | 1,5 | 1,5 |
| Lavatorio | múltiple | 2 por salida | 1,5 | 1,5 |
| Lavadero | hotel / restaurante | 4 | 3 | 3 |
| Lavadero | — | 3 | 2 | 2 |
| Ducha | — | 4 | 3 | 3 |
| Tina | — | 6 | 3 | 3 |
| Urinario | con tanque | 3 | 3 | — |
| Urinario | con válvula semiautomática/automática | 5 | 5 | — |
| Urinario | con válvula de descarga reducida | 2,5 | 2,5 | — |
| Urinario | múltiple (por ml) | 3 | 3 | — |
| Bebedero | simple | 1 | 1 | — |
| Bebedero | múltiple | 1 por salida | 1 por salida | — |

> El Anexo N° 3 de IS.010 contiene la tabla completa de **gastos probables (método de Hunter)**
> desde 3 hasta 4000 unidades, con columnas separadas para sistemas de tanque y de válvula.
> Está en el PDF local; es un dato de diseño más que de metrado, por lo que no se replica aquí
> completa. Se recomienda cargarla como tabla auxiliar si el motor va a dimensionar diámetros.

### B.2.4 Otras reglas de IS.010 con impacto en metrado

- **Registros de limpieza** (6.2 j-k): del diámetro de la tubería que sirven; si la tubería es
  > 100 mm (4"), registro mínimo de 100 mm. Se colocan: al comienzo de cada ramal horizontal o
  colector, **cada 15 m** en conductos horizontales, al pie de cada montante (salvo que descargue
  a caja/buzón a ≤ 10 m), **cada dos cambios de dirección** y en la parte superior de cada trampa
  «U». → El motor puede **estimar el número de registros** = `techo(L/15) + cambios_de_dirección/2 + 1`.
- **Separación agua/desagüe enterrados** (numeral 3): mínimo **0,50 m** horizontal y la tubería de
  agua nunca menos de **0,15 m por encima** del desagüe. En un mismo ducto: separación mínima
  **0,20 m** entre generatrices más próximas.
- **Sello de agua** de trampas: entre **0,05 m** y **0,10 m**.
- **Espaciamiento máximo entre soportes** (Anexo N° 4):

| Ø | ½" (15) | ¾" (20) | 1" (25) | 1¼"–2" (32–50) | 2½"–4" (65–100) | > 4" (>100) |
|---|---|---|---|---|---|---|
| Acero | 2,00 | 2,50 | 3,00 | 3,50 | 4,00 | 4,50 |
| Cobre | 1,80 | 2,40 | 2,40 | 3,00 | 3,60 | 4,00 |
| **PVC y similares** | **1,50** | **2,00** | **2,00** | **2,50** | **3,00** | **3,50** |

  (valores en metros) → permite metrar **número de abrazaderas/soportes** = `techo(L / espaciamiento)`.
- **Sistema contra incendio** (4.3): almacenamiento mínimo **25 m³**; alimentadores para dos
  mangueras simultáneas con presión mínima **45 m**; **Ø mínimo 100 mm (4")**; manguera de
  **30 m** y **40 mm (1½")** de diámetro.
- **Tubos de ventilación**: montante prolongada al exterior sin reducir diámetro; **1,80 m** sobre
  piso si termina en terraza accesible, **0,15 m** si es techo inaccesible; **0,60 m** por encima
  de una entrada de aire si está a menos de 3 m horizontales.
- **Diámetro de la tubería de impulsión** en función del gasto de bombeo (Anexo N° 5):

| Gasto de bombeo (L/s) | Ø impulsión |
|---|---|
| hasta 0,50 | 20 mm (¾") |
| hasta 1,00 | 25 mm (1") |
| hasta 1,60 | 32 mm (1¼") |
| hasta 3,00 | 40 mm (1½") |
| hasta 5,00 | 50 mm (2") |
| hasta 8,00 | 65 mm (2½") |
| hasta 15,00 | 75 mm (3") |
| hasta 25,00 | 100 mm (4") |

## B.3 Pruebas hidráulicas — SEDAPAL CTPS-ET-002

**Fuente:** SEDAPAL, *Especificación Técnica CTPS-ET-002 — Pruebas hidráulicas de redes de agua
potable y alcantarillado y de estructuras de almacenamiento*, Rev. 00, aprobada 2015-07-31.
PDF local: `docs/normas/SEDAPAL-CTPS-ET-002-pruebas-hidraulicas.pdf` ·
URL: <https://www.sedapal.com.pe/storage/objects/ctps-et-002-pruebas-hidraulicas-de-redes-de-ap-y-alcant.pdf>
(copia en gob.pe: <https://cdn.www.gob.pe/uploads/document/file/5976676/5295689-ctps-et-002-pruebas-en-redes-y-en-estructuras-de-almacenamiento-del-sistema-de-agua-potable-y-alcantarillado.pdf>)

> Nota: la especificación **no usa** el clásico "100 lb/pulg² durante 15 minutos" de los pliegos
> antiguos; define la presión de prueba como **múltiplo de la presión nominal / de trabajo**.
> El motor debe calcularla, no fijarla.

### B.3.1 Agua potable

| Concepto | Valor |
|---|---|
| Pérdida de agua admisible | **Ninguna** («No se admitirá ningún tipo de pérdida de agua en el circuito») |
| Presión de prueba — líneas de conducción/impulsión, DN ≤ 150 mm | **2 × presión nominal** |
| Presión de prueba — DN > 150 mm, presión de trabajo ≤ 10 bar | **1,5 × presión de trabajo** |
| Presión de prueba — DN > 150 mm, presión de trabajo > 10 bar | **presión de trabajo + 5 bar** |
| Presión de prueba — redes secundarias y líneas de aducción | **1,5 × presión nominal** |
| Presión de prueba — conexiones domiciliarias | **1 × presión nominal** |
| Presión de prueba — redes + conexiones en una sola prueba | **1,5 × presión nominal** |
| Duración mínima — redes secundarias | **30 minutos** |
| Duración mínima — redes primarias | **1 hora** |
| Pérdida admisible en PEAD (preparación previa) | **≤ 0,25 bar (4 psi)**, sin fugas visibles |
| Manómetros | mínimo **2**, con glicerina, certificados |
| Equivalencia declarada | **1 bar = 10 mca = 14,50 lb/pulg²** |
| Desinfección | **50 ppm** de cloro, contacto mínimo **24 h**, cloro residual **≥ 5 ppm**; luego purga hasta **0,5 ppm** |

Etapas: (a) prueba **a zanja abierta** (uniones descubiertas, primer relleno compactado ejecutado)
y (b) prueba **a zanja tapada con relleno compactado** + desinfección. → **Son dos partidas de
metrado distintas** si el presupuesto las separa.

### B.3.2 Alcantarillado

| Prueba | Criterio |
|---|---|
| Filtración (terreno seco) | Llenar el tramo desde el buzón aguas arriba; permanece con agua **≥ 24 h antes** de la prueba; duración mínima **10 minutos**; **no se admiten pérdidas** en PVC o PEAD. A zanja abierta la tubería queda descubierta en su **¼ superior** con relleno lateral compactado y uniones descubiertas. |
| Infiltración (con napa freática) | Verificar ausencia de agua en los buzones del tramo. |
| Humo | Sólo reemplaza a la hidráulica en líneas **> 800 mm (32")**. Presión **≥ 0,07 kg/cm²**, soplador **≥ 500 L/s**, **≥ 15 minutos**. |
| Nivelación y alineamiento | Pendiente **> 10 ‰**: error máximo **± 10 mm** (suma algebraica entre 2 o más puntos). Pendiente **< 10 ‰**: error máximo **± el valor de la pendiente**. |
| **Deflexión** (tubería flexible) | A los **30 días** de instalada. Ovalización **≤ 5 %** del diámetro interno. Se verifica con bola o **mandril** (cilindro de 0,50 m de largo) de diámetro igual al **95 %** del diámetro interno. |

Las pruebas de alcantarillado se hacen **tramo por tramo, entre buzones consecutivos**.
La prueba de nivelación y la hidráulica a zanja abierta se realizan **simultáneamente**; el rechazo
de una invalida la otra.

### B.3.3 Estructuras de almacenamiento

- Prueba de impermeabilidad: llenar hasta nivel máximo, **≥ 24 h**, antes del enlucido interior.
- Enlucido: **2 capas** — 1ª de **1 cm** con mortero 1:3 + impermeabilizante; 2ª con mortero 1:1.
- Desinfección: solución de cloro al **0,1 %** en toda la superficie interior; luego **50 ppm**
  hasta **0,30 m** de altura por **24 h**; luego llenado con **25 ppm** por **24 h**;
  cloro residual final **≥ 5 ppm**.

## B.4 Diámetros comerciales PVC

> ⚠️ **Lo primero que debe saber el motor:** en Perú **conviven dos series incompatibles** de
> tubería de agua a presión y sus diámetros exteriores **no coinciden**:
> 2" = 60,0 mm (serie pulgadas) vs 63 mm (serie métrica); 4" = 114,0 vs 110; 6" = 168,0 vs 160;
> 8" = 219,0 vs 200. Confundirlas invalida el metrado de accesorios.

### B.4.1 Agua a presión, serie pulgadas — NTP 399.002 (simple presión)

Tubo de **5,00 m**, campana en un extremo.
Clases: C-5 = 5 bar (72 psi) · C-7.5 = 7,5 bar (108 psi) · C-10 = 10 bar (145 psi) · C-15 = 15 bar (215 psi).
SDR: C-5 → 41 · C-7.5 → 27,7 · C-10 → 21 · C-15 → 14,3.

| Ø nominal | DE real (mm) | Long. útil (m) | e C-5 (mm) | e C-7.5 | e C-10 | e C-15 |
|---|---|---|---|---|---|---|
| 1/2" | 21,0 | 4,97 | — | — | 1,8 | 1,8 |
| 3/4" | 26,5 | 4,96 | — | — | 1,8 | 1,8 |
| 1" | 33,0 | 4,96 | — | — | 1,8 | 2,3 |
| 1 1/4" | 42,0 | 4,96 | — | 1,8 | 2,0 | 2,9 |
| 1 1/2" | 48,0 | 4,96 | — | 1,8 | 2,3 | 3,3 |
| 2" | 60,0 | 4,95 | 1,8 | 2,2 | 2,9 | 4,2 |
| 2 1/2" | 73,0 | 4,94 | 1,8 | 2,6 | 3,5 | 5,1 |
| 3" | 88,5 | 4,93 | 2,2 | 3,2 | 4,2 | 6,2 |
| 4" | 114,0 | 4,90 | 2,8 | 4,1 | 5,4 | 8,0 |
| 6" | 168,0 | 4,86 | 4,1 | 6,1 | 8,0 | 11,7 |
| 8" | 219,0 | 4,83 | 5,3 | 7,9 | 10,4 | 15,3 |

Fuentes (triple verificación Pavco / Tigre / Nicoll):
Pavco Wavin, *Ficha técnica agua fría* — <https://mediahub.wavin.com/m/41c952d855656fc6/original/FICHA-TECNICA-AGUA-FRIA-PAVCO-WAVIN.pdf> ·
Tigre Perú, *Catálogo de Productos*, p. 11 — <https://tigresite.s3.amazonaws.com/2022/01/Catalogo-de-Productos-Tigre-Peru-Compras.pdf>
PDFs locales: `docs/normas/Pavco-Wavin-FT-agua-fria.pdf`, `docs/normas/Tigre-Peru-Catalogo-Productos.pdf`

> ⚠️ **Trampa de cálculo:** el SDR **no se cumple** en diámetros pequeños porque rige un espesor
> mínimo de fabricación de **1,8 mm**. 4" C-10 → 114/5,4 = 21,1 ✓; pero 1" C-10 → 33/1,8 = 18,3 ✗.
> **Nunca derivar el espesor dividiendo DE/SDR en Ø ≤ 1"** — usar la tabla.

### B.4.2 Agua a presión, serie pulgadas roscada — NTP 399.166

Sólo **Clase 10**, tubo de 5,00 m.

| Ø nominal | DE (mm) | e (mm) | Hilos | Rosca útil (mm) | kg/tubo |
|---|---|---|---|---|---|
| 1/2" | 21,0 | 2,9 | 14 | 17,2 | 1,27 |
| 3/4" | 26,5 | 2,9 | 14 | 17,5 | 1,66 |
| 1" | 33,0 | 3,4 | 11½ | 21,8 | 2,44 |
| 1 1/4" | 42,0 | 3,6 | 11½ | 22,4 | 3,35 |
| 1 1/2" | 48,0 | 3,7 | 11½ | 22,8 | 3,97 |
| 2" | 60,0 | 3,9 | 11½ | 23,7 | 5,30 |

Fuente: Pavco Wavin, ficha citada, p. 1 (confirmado en Tigre p. 12).

### B.4.3 Agua a presión, serie métrica — NTP-ISO 1452-2

Tubo de **6,00 m**, unión flexible, **DE = DN**. Espesores en mm.

| DN = DE (mm) | Long. útil (m) | PN5 (SDR41) | PN7.5 (SDR28) | PN10 (SDR21) | PN15 (SDR14,2) |
|---|---|---|---|---|---|
| 63 | 5,88 | 1,60 | 2,30 | 3,00 | 4,40 |
| 75 | 5,87 | 1,90 | 2,80 | 3,60 | 5,30 |
| 90 | 5,86 | 2,20 | 3,30 | 4,30 | 6,30 |
| 110 | 5,85 | 2,70 | 4,00 | 5,30 | 7,70 |
| 140 | 5,83 | 3,50 | 5,10 | 6,70 | 9,80 |
| 160 | 5,82 | 4,00 | 5,80 | 7,70 | 11,20 |
| 200 | 5,80 | 4,90 | 7,30 | 9,60 | 14,00 |
| 250 | 5,76 | 6,20 | 9,10 | 11,90 | 17,50 |
| 315 | 5,74 | 7,70 | 11,40 | 15,00 | 22,00 |
| 355 | 5,72 | 8,70 | 12,90 | 16,90 | 24,80 |
| 400 | 5,70 | 9,80 | 14,50 | 19,10 | 28,00 |
| 450 | 5,73 | 11,00 | 16,30 | 21,50 | 31,40 |
| 500 | 5,71 | 12,30 | 18,10 | 23,90 | 34,90 |
| 630 | 5,70 | 15,40 | 22,80 | 30,00 | no se fabrica |

Fuentes: Tigre, *Catálogo Infraestructura*, p. 4-5 y 10 — <https://regiontumbes.gob.pe/piloto/documentos/Obras%20con%20Cambios/PEC-01-2022-OBRA%20CERCADO%20DE%20TUMBES/747__CD__1._Exp.Tec._Calles_Cercado_de_Tumbes_ARCC_6078_20220922_131059_744/Catalogo_Infraestructura.pdf> ·
Pavco Wavin grandes diámetros — <https://mediahub.wavin.com/m/b81b05984b218cd1/original/Ficha_Tecnica_Grandes_Diametros_Pavco_Wavin-pdf.pdf>

### B.4.4 Desagüe — NTP 399.003

**SAL** = Standard Americano **Liviano** (Clase Liviana) · **SAP** = Standard Americano **Pesado**
(Clase Pesada). Terminología oficial: ficha MEF de familias de tubos PVC —
<https://www.mef.gob.pe/contenidos/doc_siga/catalogo/ctlogo_familias_tubos_PVC.pdf> (p. 3).

> ⚠️ **Colisión de siglas:** «SAP» también designa el **tubo eléctrico pesado** de la NTP 399.006.
> Son productos distintos; el motor debe desambiguarlos por familia (sanitaria vs eléctrica).

| Ø nominal | DE real (mm) | Long. total (m) | Long. útil (m) | e Liviana (SAL) | e Pesada (SAP) |
|---|---|---|---|---|---|
| 1 1/2" | 41 | 3,00 | 2,97 | 1,3 | no se fabrica |
| 2" | 54 | 3,00 | 2,96 | 1,3 | **1,7 (Pavco) / 2,0 (Nicoll)** ⚠ |
| 3" | 80 | 3,00 | 2,94 | 1,4 | 2,0 |
| 4" | 105 | 3,00 | 2,92 | 1,7 | 2,6 |
| 6" | 168 | 5,00 | 4,87 | 2,8 | 4,1 |
| 8" | 219 | 5,00 | 4,84 | 3,5 (sólo Nicoll) | no se fabrica |

> ⚠️ **Error clásico de metrado:** el tubo de desagüe **hasta 4" viene en barras de 3 m**, no de 5 m.
> Afecta directamente el cálculo de número de tubos y de uniones.

Fuentes: Pavco Wavin desagüe — <https://mediahub.wavin.com/m/34795a652669b131/original/Ficha-Tecnica-Desague-PavcoWavin.pdf> ·
Nicoll (único con 8") — <https://grupoaliaxis.s3.us-east-2.amazonaws.com/nicoll-peru/Ficha+tecnica/Edificaci%C3%B3n/Ficha+T%C3%A9cnica+Tubos+para+Instalaciones+Sanitarias+NTP+399.003+Nicoll.pdf> ·
Tigre p. 13.
PDFs locales: `docs/normas/Pavco-Wavin-FT-desague.pdf`, `docs/normas/Nicoll-FT-desague-NTP-399.003.pdf`

### B.4.5 Alcantarillado — NTP-ISO 4435

Tubo de **6,00 m**, unión flexible. Espesor (mm) por clase de rigidez:

| DN (mm) | SN2 | SN4 | SN8 |
|---|---|---|---|
| 110 | — | 3,2 | — |
| 160 | 3,2 | 4,0 | 4,7 |
| 200 | 3,9 | 4,9 | 5,9 |
| 250 | 4,9 | 6,2 | 7,3 |
| 315 | 6,2 | 7,7 | 9,2 |
| 400 | 7,9 | 9,8 | 11,7 |
| 500 | 9,8 | 12,3 | 14,6 |
| 630 | 12,3 | 15,4 | 18,4 |

Fuente: Tigre Perú, catálogos citados.

---

# C. INSTALACIONES ELÉCTRICAS

## C.1 Partidas y unidades — Norma de Metrados OE.5

Fuente: RD 073-2010-VIVIENDA, capítulo OE.5 "Instalaciones Eléctricas y Mecánicas".

La norma exige descomponer **toda** instalación de utilización en tres (o cuatro) subpartidas:

- **Circuitos derivados** → Salidas · Canalizaciones/tuberías · Conductores en tuberías.
- **Alimentadores y subalimentadores** → Salidas (cajas de derivación o paso) · Canalizaciones ·
  Conductores en tuberías · **Cruzadas con ductos de concreto**.
- **Señales débiles** → Salidas · Canalizaciones · Conductores · Sistemas de conductos.

| Código | Partida | Unidad | Forma de medición |
|---|---|---|---|
| OE.5.1 | Conexión a la red externa de medidores | **Glb** | Cifra total por la instalación del suministro. |
| OE.5.2.1 | **Salida** | **Und** | **Cantidad de unidades de salida**, agrupables en: salida para alumbrado, para tomacorrientes, para interruptores, para dimers, para pulsadores, para intercomunicadores, de señales débiles (data/comunicaciones), **cajas de derivación**, **cajas de paso**. Incluye el suministro de la caja, sus accesorios y la mano de obra. |
| OE.5.2.2 | Canalizaciones, conductos o tuberías | **m** | Longitud de conductos/tuberías, agrupada por tipo y características. Incluye accesorios y mano de obra. |
| OE.5.2.3 | **Conductores y cables de energía en tuberías** | **m** | **«Cuando los conductores colocados en las tuberías son del mismo tipo y características, su longitud se determina multiplicando los metros de conductos o tubería por el número de conductores.»** Incluye empalmes, derivaciones, puntas muertas, terminaciones y conectores. |
| OE.5.2.4.1 / .2 | Sistemas de conductos: buzones / conductos | **Und** / **m** | Longitud de la cruzada; separable por cantidad de vías y material. |
| OE.5.2.5 | Instalaciones expuestas | **Und** | Dispositivos de sujeción o soporte para conductores. |
| OE.5.2.6 / .7 | Tableros principales / de distribución | **Und** | Conteo, indicando características generales; incluye todos los elementos que lo integran. |
| OE.5.2.8.1–.4 | Dispositivos de maniobra y protección: unipolares / bipolares / tripolares / tetrapolares | **Und** | Conteo por polaridad, tipo y características. |
| OE.5.3 | Instalación de pararrayos | **Und** | Incluye captor, barra de sostén, fijación, puesta a tierra, conductor de bajada, accesorios y **pruebas previas**. |
| OE.5.4 | **Sistema de puesta a tierra** | **Und** (pozo) / **Und** (malla) | Conteo de pozos ejecutados. Para malla: metrado **global** por cantidad total de pozos y longitud de conductores. Incluye **medición de resistividad del terreno y de resistencia de puesta a tierra**. |
| OE.5.5.1 / .2 | Lámparas / reflectores | **Und** | Conteo por tipo, indicando características. |
| OE.5.6.1–.18 | Equipos eléctricos y mecánicos (bombas, grupos electrógenos, ascensores, **campanas extractoras**, sistemas de **vapor**, **aire comprimido**, **oxígeno**, **ventilación mecánica**, **vacío**, **aire acondicionado**…) | **Und** | «Para el cómputo total se considerará el equipo instalado.» |
| OE.6.1 | Cableado estructurado — **punto de red** | **Punto (Pto)** | Comprende todos los materiales y obras para la conexión de datos desde que el conductor penetra en los conductos hasta su salida. |
| OE.6.1.1 / OE.6.4 | Cables/conductores de comunicaciones en tuberías | **m** | Longitud total agrupada por tipo. |
| OE.6.5 / .6 | Patch panel / rack de comunicaciones | **Und** | Conteo. |

> **Fórmula normativa del conductor (OE.5.2.3):**
> `L_conductor = L_tubería × n_conductores_por_tubo`
> La Norma de Metrados **no añade** longitud de "colas" al metrado de edificación: los empalmes,
> derivaciones, puntas muertas y terminaciones se declaran **incluidos en la partida**, es decir
> se cargan al **análisis de precios unitarios**, no al metrado. Ver C.3 para el respaldo
> normativo de cuánta cola dejar.

### C.1.1 Redes eléctricas exteriores (HU.4) — aquí sí hay reserva normada

Fuente: RD 073-2010-VIVIENDA, HU.4.2.6–.8 (redes subterráneas) y HU.4.3.1 (redes aéreas):

> «El cómputo de cables de energía o cables será en longitud por cada sección y por tipo de
> cables, según el proyecto y se obtendrá de considerar el **recorrido total indicado más 10 m de
> cable en el interior de las subestaciones y más el 5 % del total para retaceo y desperdicios**.»

```
L_cable = (L_recorrido + 10 m por subestación) × 1,05
```

Y aclara: «**Si se toma en cuenta el desperdicio en el metrado ya no se considerará en el análisis
de precios**» (evita el doble conteo).

| Código | Partida | Unidad |
|---|---|---|
| HU.4.2.1 | Empalmes para cables | Und |
| HU.4.2.2 | Buzones o cámaras | Und |
| HU.4.2.3 | Ensayos y pruebas de control en laboratorio | Und |
| HU.4.2.4 | Zanjas | m |
| HU.4.2.5 | Cruzadas | m |
| HU.4.2.6/.7/.8 | Cables de energía MT / BT distribución secundaria / BT alumbrado público | m |
| HU.4.3.2 | Estructura de soporte (postes) | Und |

## C.2 Norma EM.010 — qué aporta y qué no

**Fuente:** RNE **EM.010 Instalaciones Eléctricas Interiores** (El Peruano, 11-06-2006).
PDF local: `docs/normas/RNE-EM.010-instalaciones-electricas.pdf` ·
URL: <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo3/04_EM/RNE2006_EM_010.pdf>

EM.010 **remite todo el contenido técnico al Código Nacional de Electricidad**
(«siendo obligatorio el cumplimiento de todas sus prescripciones»). Sí aporta:

- **Tabla de iluminancias mínimas en lux por ambiente** (Art. 3°) — útil para estimar el número de
  luminarias antes de tener planos. Ejemplos: pasillos y baños 100 lux; escaleras 150 lux;
  oficinas generales y salas de cómputo 500 lux; salones de clase/laboratorios/talleres 500 lux;
  dormitorio general 50 lux; cocina general 300 lux y áreas de trabajo 500 lux; sala de
  operaciones (general) 1000 lux y mesa de operaciones 100 000 lux.
- **Escalas de plano** (Art. 5°): planos generales **1:50**; planos de conjunto 1:100, 1:200 ó
  1:500; detalles 1:20 ó 1:25. → Relevante para el lector de planos de metra-ai.
- **Componentes** de la instalación: acometida, alimentadores, subalimentadores, tableros y
  subtableros, circuitos derivados, protección y control, medición y registro, puesta a tierra.

## C.3 Código Nacional de Electricidad — Utilización (CNE-U 2006)

**Fuente:** RM 037-2006-MEM/DM, *Código Nacional de Electricidad – Utilización*.
PDF local: `docs/normas/CNE-Utilizacion-2006-RM-037-2006-MEM.pdf` ·
URL oficial (SPIJ/MINJUS): <https://spij.minjus.gob.pe/Graficos/Peru/2006/Enero/30/RM-037-2006.pdf> ·
Ficha en gob.pe: <https://www.gob.pe/institucion/minem/normas-legales/108855-0037-2006-mem>

| Regla | Contenido | Valor |
|---|---|---|
| **030-002** | Sección mínima de conductores | **2,5 mm²** para circuitos derivados de fuerza y alumbrado; **1,5 mm²** para circuitos de control de alumbrado. Todos de cobre. |
| **030-012** | Sección mínima de cordones flexibles | **0,75 mm²** (0,5 mm² en dispositivos específicos) |
| **050-106 (9)** | Sección mínima en vivienda unifamiliar | **4 mm²** para acometidas; **2,5 mm²** para alimentadores. Corrientes mínimas: 15 A hasta 3000 W; 25 A de 3000 a 5000 W; 40 A de 5000 a 8000 W monofásico (15 A si es trifásico 380/220 V). |
| **050-108** | Espacio en tablero (vivienda unifamiliar) | Espacio para al menos **4 interruptores automáticos bipolares** + **2 dispositivos adicionales** de reserva. |
| **060-712** | **Resistencia de electrodos de puesta a tierra** | **≤ 25 Ω**. Si un electrodo simple supera 25 Ω, se instala **un electrodo adicional a ≥ 2 m** (o a una distancia igual a la longitud del electrodo). → **Regla de metrado: un pozo puede convertirse en dos.** |
| **070-3000 (1)** | Máximo de salidas por circuito | **≤ 12 salidas** por circuito derivado de 2 conductores. |
| **070-3000 (2)** | Consumo por salida | **≥ 1 A** por salida. |
| **070-3000 (4)** | Configuraciones fijas multisalida | Cada **1,5 m** (o fracción) cuenta como **una salida**; en usos intensivos, cada **300 mm** cuenta como una salida. |
| **070-3002 (1)** | Caja obligatoria | Una caja (o dispositivo equivalente) **en cada punto de salida, interruptor, tomacorriente o unión** de tuberías/canalizaciones/cables. |
| **070-3002 (4)** | **Cola / conductor libre en cajas** | **«En cada caja se debe dejar por lo menos 150 mm de conductor libre»** para empalmes o conexiones a artefactos. |
| 070-1714 / 070-1806 | Ocupación de canalizaciones | Suma de secciones de conductores + aislamiento **≤ 40 %** del área interior de la canalización. |
| 070-2104 | Canalizaciones (*wireways*) | **≤ 20 %** del área para conductores de potencia; **≤ 40 %** si sólo son señal y control. |

> ### Reserva de conductor: la regla defendible
> El CNE-U 070-3002(4) es el **único respaldo normativo cuantificado** para las "colas":
> **0,15 m de conductor libre por caja**. Si el motor quiere ofrecer un modo "metrado con colas"
> (además del normativo de la Norma de Metrados), la fórmula correcta y sustentable es:
>
> ```
> L_conductor = L_tubería × n_conductores + 0,15 m × n_cajas × n_conductores_que_llegan_a_la_caja
> ```
>
> Cualquier valor mayor (0,20 / 0,30 m por caja) es **práctica de obra sin respaldo normativo** →
> debe ir en el APU como desperdicio, no en el metrado, y marcarse `"verificado": false`.

## C.4 Tuberías eléctricas PVC comerciales

Norma: **NTP 399.006:2015 (revisada 2020)** — «Tubos de PVC de paredes lisas para canalizaciones
eléctricas». Clasifica en **SEL** (Clase Liviana) y **SAP** (Clase Pesada). Ambos en color gris.

**Fuente:** Pavco Wavin, *Ficha Técnica Sistema Eléctrico*, edición setiembre 2024 — verificada
directamente contra el PDF.
PDF local: `docs/normas/Pavco-Wavin-FT-sistema-electrico.pdf` ·
URL: <https://mediahub.wavin.com/asset/b5982f36-1a66-4c58-a441-cbbb7c9b1619/Ficha-Tecnica-Sistema-Electrico-Pavco-Wavin.pdf>
Ø exterior y espesores son **idénticos en Pavco, Nicoll, Tigre e Inyectoplast** — son dato de
norma, no de fabricante.

> ⚠️ **La NTP 399.166 NO es de tubería eléctrica** — es de tubos PVC para fluidos a presión con
> unión roscada (agua fría). Confirmado en la clasificación oficial del MEF/SIGA.

### C.4.1 PVC-SEL (Clase Liviana) — tubo de 3,00 m

| Designación | Ø nominal (mm) | Ø exterior (mm) | Espesor (mm) | Ø interior (mm) | Long. útil (m) | kg/tubo |
|---|---|---|---|---|---|---|
| 1/2" | 11 | 12,7 | 1,1 | — | 2,99 | 0,191 |
| **5/8"** | 13 | 15,9 | 1,1 | 13,7 | 2,99 | 0,243 |
| 3/4" | 15 | 19,1 | 1,2 | 16,7 | 2,98 | 0,321 |
| 1" | 20 | 25,4 | 1,3 | 22,8 | 2,98 | 0,467 |
| 1 1/4" | 25 | 31,8 | 1,3 | 29,2 | 2,97 | 0,602 |
| 1 1/2" | 30 (ver nota) | 38,1 | 1,6 | 34,9 | 2,97 | 0,871 |
| 2" | 40 | 50,8 | 1,7 | 47,4 | 2,96 | 1,245 |

SEL **no se fabrica** en 2 1/2", 3" ni 4".

### C.4.2 PVC-SAP (Clase Pesada) — tubo de 3,00 m

| Designación | Ø nominal (mm) | Ø exterior (mm) | Espesor (mm) | Ø interior (mm) | Long. útil (m) | kg/tubo |
|---|---|---|---|---|---|---|
| 1/2" | 15 | 21,0 | 1,8 | 17,4 | 2,98 | 0,516 |
| 3/4" | 20 | 26,5 | 1,8 | 22,9 | 2,98 | 0,663 |
| 1" | 25 | 33,0 | 1,8 | 29,4 | 2,97 | 0,838 |
| 1 1/4" | 35 | 42,0 | 2,0 | 38,0 | 2,97 | 1,193 |
| 1 1/2" | 40 | 48,0 | 2,3 | 43,4 | 2,96 | 1,567 |
| 2" | 50 | 60,0 | 2,8 | 54,4 | 2,96 | 2,389 |
| 2 1/2" | 65 | 73,0 | 3,5 | 66,0 | 2,95 | 3,627 |
| 3" | 80 | 88,5 | 3,8 | 80,9 | 2,94 | 4,798 |
| 4" | 100 | 114,0 | 4,0 | 106,0 | 2,93 | 6,558 |

SAP **no se fabrica** en 5/8".

> ⚠️ **Colisión de siglas:** «SAP» eléctrico (NTP 399.006) ≠ «SAP» sanitario (Clase Pesada de
> desagüe, NTP 399.003). El motor debe desambiguar por familia.

> ⚠️ **Tensión normativa a validar con el proyectista.** El CNE-U **070-1004** exige que no se usen
> conductos con diámetro interno menor que el tamaño comercial de **15 mm de diámetro nominal**;
> según la Tabla 9 del CNE eso equivale a Ø interno 15,8 mm. El **SEL de 5/8" tiene Ø nominal
> 13 mm y Ø interno 13,7 mm** — queda por debajo de la letra de la regla, pese a ser el estándar
> de facto en vivienda peruana. La Tabla 9 está declarada para tubería **metálica**, lo que deja
> la lectura abierta. **Esto es una lectura de los dos textos, no una interpretación oficial:
> marcarlo como punto a validar.** Nota práctica: los APU de obra pública revisados usan **20 mm**,
> no 5/8".

### C.4.3 Reglas de canalización del CNE-U

| Regla | Contenido | Valor |
|---|---|---|
| **070-1004** | Diámetro mínimo de conducto | **15 mm nominal** (excepción: flexible de 13 mm en tramos ≤ 1,5 m) |
| **070-1406** | Tubería metálica: Ø interior | no menor al de tubería de 15 mm nominal |
| **070-1100(1)** | Tubería rígida de PVC y HFT | se instala «de acuerdo a las reglas aplicables a conductos metálicos rígidos» |
| **070-942** | Máximo de curvas entre cajas | **4 curvas de 90°** entre cajas o puntos de derivación |
| **070-1010** | Separación de soportes de conducto | 1,5 m (Ø 15-20 mm) · 2 m (Ø 25-35 mm) · 3 m (Ø ≥ 40 mm) |
| **070-1014** / Tabla 8 | Máximo % de llenado | 1 conductor **53 %** · 2 conductores **31 %** · 3 o más **40 %** |
| **040-302(6)** | Reserva en caja de toma | conductores de alimentador se prolongan **60 cm** en la caja de conexión |
| Tabla 53 (regla 070-012) | Profundidad de enterrado | **600 mm** mínimo para ≤ 600 V |

**Tabla 9 del CNE-U** (áreas y Ø interno; nota del propio código: «Las dimensiones mostradas son
típicas de conductos y tuberías **metálicas**»):

| Ø nom. mm | Ø nom. pulg | Ø interno mm | Área 100 % mm² | Área 40 % mm² |
|---|---|---|---|---|
| 15 | 1/2" | 15,8 | 196 | 78 |
| 20 | 3/4" | 20,9 | 344 | 138 |
| 25 | 1" | 26,6 | 558 | 223 |
| 35 | 1 1/4" | 35,1 | 965 | 386 |
| 40 | 1 1/2" | 40,9 | 1 313 | 525 |
| 50 | 2" | 52,5 | 2 165 | 866 |
| 65 | 2 1/2" | 62,7 | 3 089 | 1 236 |
| 80 | 3" | 77,9 | 4 770 | 1 908 |
| 100 | 4" | 102,3 | 8 213 | 3 285 |

### C.4.4 Accesorios Pavco — peso por pieza (para metrado de suministro)

| Accesorio | Pesos (kg/pieza) |
|---|---|
| Curva SEL 90° | 5/8" 0,010 · 3/4" 0,018 · 1" 0,030 · 1 1/4" 0,060 · 1 1/2" 0,100 · 2" 0,150 |
| Curva SAP 90° | 1/2" 0,037 · 3/4" 0,057 · 1" 0,084 · 1 1/4" 0,132 · 1 1/2" 0,185 · 2" 0,338 · 2 1/2" 0,600 · 3" 1,225 · 4" 1,700 |
| Unión SEL | 5/8" 0,003 · 3/4" 0,005 · 1" 0,008 · 1 1/2" 0,025 |
| Conector SEL (tubo→caja) | 5/8" 0,002 · 3/4" 0,003 · 1" 0,005 · 1 1/2" 0,015 |
| Caja rectangular 4"×2"×1 1/2" | 0,050 |
| Caja octogonal 3 1/2"×3 1/2"×1 1/2" | 0,050 |

### C.4.5 Erratas detectadas en catálogos (no copiarlas al motor)

| Errata | Detalle |
|---|---|
| Peso SEL 2" (Pavco) | La ficha técnica dice **1,245 kg**; el catálogo comercial dice 0,245 kg. **Usar 1,245** (0,245 sería menos que el 1 1/2"). |
| Espesor SAP (Nicoll) | Imprime «2» en las 9 filas. Es falso: sus propios Ø dan de 1,8 a 4,0 mm. **No usar esa columna.** |
| Curva SAP 2 1/2" (Nicoll) | Dice 1,600 kg; Pavco dice 0,600 kg. Rompe la monotonía de la serie → correcto **0,600**. |
| Conector SEL 1 1/4" (Pavco y Nicoll) | Ambos 0,001 kg entre valores de 0,005 y 0,015. Typo. |
| Ø nominal SEL 1 1/2" | Ficha Pavco 2024: 30 mm. Nicoll, Tigre y catálogo comercial Pavco: 35 mm. El Ø exterior real (38,1 mm) coincide en todos → afecta la designación, no la pieza. |

## C.5 Conductores

### C.5.1 Equivalencia AWG ↔ mm²

Fórmula ASTM B258: `d = 0,005 in × 92^((36−n)/39)`.

| AWG | Sección real (mm²) | mm² comercial más cercano |
|---|---|---|
| 14 | 2,081 | 2,5 |
| 12 | 3,309 | 4 |
| 10 | 5,261 | 6 |
| 8 | 8,366 | 10 |
| 6 | 13,302 | 16 |
| 4 | 21,151 | 25 |
| 2 | 33,631 | 35 |
| 1/0 | 53,475 | 50 |
| 2/0 | 67,431 | 70 |
| 3/0 | 85,029 | 95 |
| 4/0 | 107,219 | 120 |

> ⚠️ El texto de **ASTM B258 es de pago**: la atribución normativa queda **NO VERIFICADA** en
> fuente primaria, aunque el cálculo es reproducible.
> ⚠️ **La columna de equivalencia comercial es conveniencia de obra, no equivalencia normativa.**
> Son productos distintos: THW-90 6 AWG → Ø ext. 7,5 mm y 163 kg/km; THW-90 16 mm² → 7,9 mm y
> 182 kg/km.

Respaldo peruano de las secciones métricas: **CNE-U Tabla 10 Parte A** (pág. 577), que lista
1,5 / 2,5 / 4 / 6 / 10 / 16 / 25 / 35 / 50 / 70 / 95 / 120 / 150 / 185 / 240 mm² con sus diámetros
exteriores, citando la NTP 370.252.

### C.5.2 INDECO (Nexans Perú) THW-90 — línea AWG

PDF local: `docs/normas/INDECO-THW-90-AWG-hasta-8.pdf` ·
<https://www.nexans.pe/.rest/catalog/v1/family/pdf/21802/THW-90-AWG>

| Calibre | Hilos | Ø conductor (mm) | Espesor aisl. (mm) | Ø exterior (mm) | **kg/km** | R máx (Ω/km) | A al aire | A en ducto |
|---|---|---|---|---|---|---|---|---|
| 14 AWG | 7 | 1,7 | 0,76 | 3,4 | **27** | 8,97 | 35 | 25 |
| 12 AWG | 7 | 2,2 | 0,76 | 3,9 | **38** | 5,65 | 40 | 30 |
| 10 AWG | 7 | 2,8 | 0,76 | 4,4 | **57** | 3,547 | 56 | 40 |
| 8 AWG | 7 | 3,3 | 1,14 | 5,7 | **98** | 2,231 | 80 | 56 |

PDF local: `docs/normas/INDECO-THW-90-AWG-kcmil.pdf` ·
<https://www.nexans.pe/.rest/catalog/v1/family/pdf/21811/THW-90-AWG>

| Calibre | Hilos | Ø cond. (mm) | Ø ext. (mm) | kg/km | R (Ω/km) | A aire | A ducto |
|---|---|---|---|---|---|---|---|
| 6 AWG | 7 | 4,2 | 7,5 | 163 | 1,375 | 105 | 75 |
| 4 AWG | 7 | 5,3 | 8,6 | 242 | 0,8651 | 140 | 95 |
| 1/0 | 19 | 8,6 | 12,8 | 577 | 0,3421 | 260 | 170 |
| 2/0 | 19 | 9,6 | 13,9 | 710 | 0,2713 | 300 | 195 |
| 4/0 | 19 | 12,2 | 17,2 | 1118 | 0,1706 | 405 | 260 |
| 250 kcmil | 37 | 13,3 | 18,3 | 1299 | 0,1444 | 455 | 290 |
| 500 kcmil | 37 | 18,7 | 24,5 | 2524 | 0,07222 | 700 | 430 |

> **INDECO no fabrica THW-90 en 2 AWG ni 3/0 AWG.** El catálogo salta de 4 AWG a 1/0 y de 2/0 a 4/0.

### C.5.3 INDECO THW-90 — línea métrica

PDF local: `docs/normas/INDECO-THW-90-metrico.pdf` ·
<https://www.nexans.pe/.rest/catalog/v1/family/pdf/21807/THW-90>

| mm² | Hilos | Ø cond. (mm) | Ø ext. (mm) | kg/km | R (Ω/km) | A aire | A ducto |
|---|---|---|---|---|---|---|---|
| 16 | 7 | 4,6 | 7,9 | 182 | 1,15 | 117 | 72 |
| 25 | 7 | 5,8 | 9,1 | 272 | 0,727 | 155 | 95 |
| 35 | 7 | 6,8 | 10,1 | 362 | 0,524 | 192 | 117 |
| 50 | 19 | 7,9 | 12,2 | 502 | 0,387 | 233 | 141 |
| 70 | 19 | 9,5 | 13,8 | 700 | 0,268 | 298 | 179 |
| 95 | 19 | 11,2 | 15,5 | 942 | 0,193 | 361 | 216 |
| 120 | 37 | 12,8 | 17,8 | 1204 | 0,153 | 418 | 249 |
| 150 | 37 | 14,2 | 19,2 | 1458 | 0,124 | 482 | 285 |
| 185 | 37 | 15,8 | 20,8 | 1804 | 0,0991 | 549 | 324 |
| 240 | 37 | 18,0 | 23,0 | 2327 | 0,0754 | 648 | 381 |

Secciones ≤ 10 mm² (familia de conductor de tierra, amarillo/verde) —
<https://www.nexans.pe/.rest/catalog/v1/family/pdf/36255/THW-90>:
2,5 mm² → Ø 3,5 mm / **31 kg/km** · 4 → Ø 4,0 / **46** · 6 → Ø 4,6 / **65** · 10 → Ø 6,1 / **112**

> ⚠️ **No mezclar las dos líneas en un mismo cálculo.** La línea AWG da 6 AWG (13,3 mm²) = 75 A en
> ducto y la métrica da 16 mm² = 72 A: la sección **mayor** tiene **menos** amperaje porque una
> sigue base NEC y la otra IEC.

### C.5.4 INDECO NH-80 / NHX-90 (libre de halógenos)

PDF local: `docs/normas/INDECO-NH-80-Freetox.pdf` ·
<https://www.nexans.pe/.rest/catalog/v1/family/pdf/21922/FREETOX-NH>

| mm² | Hilos | Ø cond. (mm) | Espesor (mm) | Ø ext. (mm) | kg/km | R (Ω/km) | A aire | A ducto |
|---|---|---|---|---|---|---|---|---|
| 1,5 | 7 | 1,5 | 0,7 | 3,0 | **21** | 12,1 | 19 | 15 |
| 2,5 | 7 | 1,9 | 0,8 | 3,6 | **33** | 7,41 | 26 | 20 |
| 4 | 7 | 2,4 | 0,8 | 4,1 | **48** | 4,61 | 36 | 26 |
| 6 | 7 | 3,0 | 0,8 | 4,6 | **68** | 3,08 | 47 | 34 |
| 10 | 7 | 3,7 | 1,0 | 5,8 | **111** | 1,83 | 66 | 46 |

**El NH-80 de INDECO termina en 10 mm².** Por encima el producto libre de halógenos es
**NHX-90 / LSOHX-90** — PDF local `docs/normas/INDECO-NHX-90-Freetox.pdf` ·
<https://www.nexans.pe/.rest/catalog/v1/family/pdf/21927/FREETOX-NH>:
16 mm² → 169 kg/km · 25 → 256 · 35 → 344 · 50 → 469 · 70 → 665 · 95 → 903 · 120 → 1153 ·
150 → 1403 · 185 → 1745 · 240 → 2261 · 300 → 2842

Patrón de URL reutilizable para cualquier familia Nexans:
`https://www.nexans.pe/.rest/catalog/v1/family/pdf/{id}/{slug}`

> ⚠️ **CEPER Cables: NO VERIFICADO.** `ceper.com.pe` es hoy una página *placeholder* (logo y
> correo genérico), `/productos` da 404 y no hay catálogo descargable. Los datos que circulan en
> espejos no oficiales (LS0H-80 con 22/33/48/68/112 kg/km) coinciden casi exactamente con INDECO
> —el peso lo domina el cobre— pero **no deben usarse como dato de catálogo**. Construir el motor
> con INDECO, que sí tiene fichas oficiales vigentes.

## C.6 Cuánto conductor por punto — evidencia de obra real

**Fuente:** APU oficial de obra pública, I.E. N° 093 Efraín Arcaya Zevallos, Zarumilla–Tumbes,
15/12/2022 —
<https://regiontumbes.gob.pe/piloto/documentos/Obras%20con%20Cambios/EFRAIN%20ARCAYA%20ZEVALLOS/4.-%20INFORMACION%20ACTUALIZADA%20EFRAIN%20ARCAYA%20ZEVALLOS/2.%20PRESUPUESTOS/05%20-%20ELECTRICAS/analisissubpresupuesto2varios.pdf>

| Partida | Rend. | Tubería | Cable | Cajas | Otros |
|---|---|---|---|---|---|
| **Salida centro de luz, 1 punto** | 15 pto/día | 2,52 tubos PVC-P 20 mm × 3 m = **7,56 m** | **15,10 m** NH 2,5 mm² | 1 rectangular + 1 octogonal | 2 curvas, 0,2 rollo cinta |
| **Salida tomacorriente h = 0,40 m** | 15 pto/día | 2,00 tubos × 3 m = **6,00 m** | **12,30 m** NH 4,0 mm² + **6,15 m** NH 2,5 (tierra) | 1 rectangular | 2 curvas, 0,2 rollo cinta |

**Lectura de las cifras:**
- Centro de luz: 7,56 m × 2 conductores = 15,12 ≈ **15,10 m** → aplican la regla OE.5.2.3 pura,
  **sin desperdicio**.
- Tomacorriente: 6,00 m de tubo pero **6,15 m por conductor** → **0,15 m de holgura por
  conductor**, que coincide **exactamente** con los 150 mm del CNE-U 070-3002(4).
- Alimentador por metro (N2XOH): el insumo es **1,00 ml por ml — cero desperdicio**.
- Mano de obra: cuadrilla 0,5 operario + 1 oficial + 1 peón, rendimiento 15 pto/día,
  herramientas 3 % de MO.

> **Conclusión operativa:** los **0,15 m por caja tienen base normativa y evidencia de obra**.
> Los **0,20 – 0,30 m por caja y cualquier % de desperdicio de conductor son criterio de práctica
> del proyectista, sin norma que los respalde**. Ni la RD 073-2010 ni el CNE-U fijan porcentaje
> alguno. Si metra-ai los ofrece, deben ser **parámetro configurable y etiquetado como criterio**,
> nunca presentado como norma.

## C.7 Pozo a tierra

### C.7.1 Lo que sí está normado — CNE-U

| Concepto | Dato | Regla |
|---|---|---|
| **Resistencia máxima** | **≤ 25 Ω**. Si un electrodo simple la supera, «es necesario instalar un electrodo adicional a una distancia de por lo menos **2 m**» | **060-712** |
| **Varilla: diámetro** | **≥ 16 mm (5/8")** acero-cobre · **≥ 13 mm (1/2")** cobre puro | 060-702(3)(a) |
| **Varilla: longitud** | **≥ 2,0 m** | 060-702(3)(b) |
| **Profundidad alcanzada** | **≥ 2,5 m**, cualquiera sea el número de varillas | 060-702(3)(d) |
| Superficie del electrodo | limpia, sin pintura ni esmalte | 060-702(3)(c) |
| Separación entre electrodos | **≥ 2 m** (o al menos su longitud) | 060-702(6) |
| Enlace entre electrodos | conductor de cobre **≥ 16 mm²** | 060-700(3) |
| Electrodo de placa | ≥ 0,2 m² de contacto, ≥ 6 mm si es acero, enterrado ≥ 600 mm | 060-702(4) |
| Electrodo en concreto | conductor de cobre desnudo ≥ 6 m, sección según Tabla 43 (25 a 95 mm²) | 060-702(2) |
| Sección del conductor de tierra | Tabla 17: 10 mm² (≤ 100 A) hasta 95 mm² (> 475 A) | 060-812 |

### C.7.2 Lo que NO está normado

> ⚠️ **Las dimensiones «0,80 – 1,00 m de diámetro × 2,40 – 3,00 m de profundidad» NO están en el
> CNE-U.** El código sólo exige que la varilla alcance **≥ 2,5 m de profundidad** y mida
> **≥ 2,0 m**; **nunca menciona el diámetro de la excavación**. Esas medidas provienen de empresas
> instaladoras y blogs comerciales que citan la **NTP 370.016** (documento INACAL de pago, **no
> leído → NO VERIFICADO**). Tratarlas como práctica de obra, no como norma.

### C.7.3 Metrado (RD 073-2010, OE.5.4)

Unidad **Und** por pozo. La partida comprende «pozo de puesta a tierra o sistema de malla,
uniones, conexiones, soldaduras, accesorios y el conductor de puesta a tierra desde el electrodo
hasta la barra del tablero general, este último incluye también los ductos», más «las pruebas
previas a la puesta en servicio y la medición de la resistividad del terreno y la resistencia de
puesta a tierra». En **malla**, el metrado es **global** por cantidad total de pozos y longitud de
conductores.

> **Regla derivada para el motor:** por 060-712, un pozo que no alcance los 25 Ω **obliga a un
> segundo electrodo**. El metrado debe permitir declarar `n_electrodos ≥ 1` por pozo y no asumir 1.

## C.8 Alturas de salidas — qué es norma y qué es costumbre

**El CNE-U no fija alturas de montaje de tomacorrientes ni interruptores** (búsqueda exhaustiva en
las 836 páginas). Lo único normativo es accesibilidad, en la **Norma A.120** del RNE
(RM 075-2023-VIVIENDA):

| Elemento | Altura | Fuente |
|---|---|---|
| Interruptores y timbres de llamada | **≤ 1,35 m** | A.120, Art. 11 inciso f) |
| Tomacorriente, interruptores y control de temperatura (hospedaje) | **entre 0,40 m y 1,20 m** | A.120, Art. 27 inciso e) |

> ⚠️ Las alturas clásicas de obra (tomacorriente 0,40 m; interruptor 1,20–1,40 m; tomacorriente de
> cocina sobre mesada 1,10 m) son **criterio de proyecto, no norma**. Respaldo de la práctica: el
> APU público de C.6 titula la partida literalmente «SALIDA DE CENTRO DE TOMACORRIENTE **h=0.40m**».

## C.9 Nota sobre la unidad de las salidas eléctricas

La RD 073-2010 dice **Und** para las salidas eléctricas (OE.5.2.1). La unidad **«Punto (Pto.)»**
sólo aparece formalmente en **OE.6.1** (cableado estructurado, «punto de red») y en el capítulo
**sanitario** (OE.4.2.1, OE.4.3.1, OE.4.6.1). En la práctica los presupuestos S10 peruanos usan
«PTO» para salidas eléctricas.
→ **Recomendación para metra-ai:** emitir `und` como unidad canónica normativa y permitir alias
de presentación `pto`, dejando trazabilidad de cuál se usó.

---

# D. INSTALACIONES MECÁNICAS / HVAC

## D.1 Lo que dice la Norma de Metrados

La RD 073-2010 **no desarrolla partidas de ductos de HVAC**. Todo lo mecánico se agrupa en
**OE.5.6 Equipos Eléctricos y Mecánicos**, medido en **Und** por equipo instalado:

- OE.5.6.12 Campanas extractoras — **Und**
- OE.5.6.13 Sistema de vapor — **Und**
- OE.5.6.14 Sistema de aire comprimido — **Und**
- OE.5.6.15 Sistema de oxígeno — **Und**
- OE.5.6.16 Sistema de ventilación mecánica — **Und**
- OE.5.6.17 Sistema de vacío — **Und**
- OE.5.6.18 **Sistema de aire acondicionado** — **Und**

> ⚠️ **Vacío normativo.** Para desagregar HVAC (ductos en kg, aislamiento en m², rejillas y
> difusores en Und) **no hay norma peruana de metrado**; se aplica la práctica internacional
> (SMACNA) y la analogía con OE.5.6 «En la unidad o en la suma global de los diferentes equipos se
> incluyen todos los trabajos y materiales necesarios para su instalación hasta dejarlos en
> funcionamiento». El motor debe permitir ambos modos: **global por equipo** (normativo) y
> **desagregado** (ingeniería de detalle).

Referencia adicional del RNE: **EM.030 Instalaciones de Ventilación** y **EM.070** (según la
edición vigente del Título III.4) — no descargadas en esta iteración.

## D.2 Ductos: fórmulas de metrado

Para un ducto rectangular de lados `a` y `b` (m) y longitud `L` (m):

```
Perímetro       P = 2 · (a + b)
Área de plancha A = P · L                       [m² de plancha desarrollada]
Peso            W = A · w_calibre · (1 + d)     [kg]
```

Para un ducto circular de diámetro `D`:

```
P = π · D
A = π · D · L
```

donde `w_calibre` = peso por m² de la plancha galvanizada según su calibre (tabla en D.3) y
`d` = porcentaje adicional por **refuerzos, bridas, traslapes y desperdicio**.

Aislamiento térmico:

```
A_aislamiento = P_exterior · L   [m²]
```
Se metra en **m²**, clasificado por espesor y tipo (lana de vidrio, elastomérico, etc.).

Rejillas, difusores, compuertas cortafuego y ventiladores: **Und**, agrupados por tipo y dimensión.

## D.3 Calibres de plancha y pesos

**Hallazgo clave:** el texto **completo y gratuito** de **SMACNA, *HVAC Duct Construction
Standards — Metal and Flexible*, 2ª ed. 1995** está publicado por public.resource.org por estar
incorporado por referencia en el CFR de EE.UU.
Copia local: `docs/normas/SMACNA-HVAC-Duct-Construction-Standards-1995.html` ·
URL: <https://law.resource.org/pub/us/cfr/ibr/005/smacna.duct.1995.html>

> ⚠️ Es la edición de **1995**. La vigente es la **4ª (2020)**, de pago. **NO VERIFICADO** si sus
> tablas cambiaron.

### D.3.1 Galvanized Sheet Gauge (incluye el recubrimiento de zinc) — Apéndice A de SMACNA

Base: ASTM A653 / A924. **Los kg/m² son los publicados por SMACNA, no calculados.**

| Calibre (ga) | Espesor nom. (in) | **Espesor nom. (mm)** | lb/ft² | **kg/m²** | Espesor mín-máx (mm) |
|---|---|---|---|---|---|
| 28 | 0,0187 | **0,4750** | 0,781 | **3,81** | 0,395 – 0,555 |
| 26 | 0,0217 | **0,5512** | 0,906 | **4,42** | 0,471 – 0,631 |
| 24 | 0,0276 | **0,7010** | 1,156 | **5,64** | 0,601 – 0,801 |
| 22 | 0,0336 | **0,8534** | 1,406 | **6,86** | 0,753 – 0,953 |
| 20 | 0,0396 | **1,0060** | 1,656 | **8,08** | 0,906 – 1,106 |
| 18 | 0,0516 | **1,3110** | 2,156 | **10,52** | 1,181 – 1,441 |
| 16 | 0,0635 | **1,6130** | 2,656 | **12,96** | 1,463 – 1,763 |
| 14 | 0,0785 | **1,9940** | 3,281 | **16,01** | 1,784 – 2,204 |

### D.3.2 Manufacturers' Standard Gauge (acero negro, sin zinc) — para comparación

| Calibre (ga) | Espesor (in) | Espesor (mm) | lb/ft² | kg/m² |
|---|---|---|---|---|
| 28 | 0,0149 | 0,38 | 0,625 | 3,05 |
| 26 | 0,0179 | 0,45 | 0,750 | 3,66 |
| 24 | 0,0239 | 0,61 | 1,000 | 4,88 |
| 22 | 0,0299 | 0,76 | 1,250 | 6,10 |
| 20 | 0,0359 | 0,91 | 1,500 | 7,32 |
| 18 | 0,0478 | 1,21 | 2,000 | 9,77 |
| 16 | 0,0598 | 1,52 | 2,500 | 12,21 |
| 14 | 0,0747 | 1,90 | 3,125 | 15,26 |

Fuentes: <https://roofobservations.com/sheet-steel-weight/> (base declarada 41,82 lb/ft² por
pulgada) · espesores corroborados en <https://www.bestmaterials.com/PDF_Files/sheet-metal-gauge-chart.pdf>
· pesos ASTM A653/A924 en <https://greenseamind.com/wp-content/uploads/2020/04/MetalSpecifications.pdf>

### D.3.3 La diferencia galvanizado − negro es constante

| | Delta galvanizado − negro |
|---|---|
| Espesor | **+0,0037 a 0,0038 in (≈ +0,095 mm)** en todos los calibres |
| Peso | **+0,156 lb/ft² exacto = +0,762 kg/m²** en todos |

En calibre 26 eso representa **+20,8 %**; en calibre 14, sólo **+5,0 %**.

> ⚠️ **Usar la tabla de acero negro para metrar ducto galvanizado subestima el peso**, sobre todo
> en calibres delgados. Usar siempre D.3.1.
>
> ⚠️ **No multiplicar espesor × 7 850 kg/m³ para metrar ducto.** La densidad del acero es
> 7 850 kg/m³ (ASTM A36, confirmado en <https://amesweb.info/Materials/Density_of_Steel.aspx> y en
> la nota de SMACNA de 40,8 lb/ft²/in ≡ 7 843 kg/m³), pero las tablas de calibre llevan la
> convención MSG de **41,82 lb/ft² por pulgada** (≡ 8 039 kg/m³, +2,4 %) **más el zinc**. El
> cálculo directo da menos peso que la tabla oficial. **Usar la columna kg/m².**

## D.4 Espesor requerido según SMACNA

### D.4.1 Regla base (texto literal)

> «**The greater duct dimension determines the gage for all sides.**»
>
> «Unless otherwise specified steel sheet and strip used for duct and connectors shall be G-60
> coated galvanized steel of lockforming grade conforming to ASTM A653 and A924 standards.
> **Minimum yield strength for steel sheet and reinforcements is 30 000 psi.**»
>
> Accesorios: «Fittings shall be reinforced like sections of straight duct. On size change
> fittings, **the greater fitting dimension determines the duct gage**.»

### D.4.2 Calibre mínimo SIN refuerzo (columna 2 de las Tablas 1-3 a 1-9)

Entrada: **dimensión mayor del ducto** × **presión estática (wg = pulgadas de columna de agua)**.

| Dim. mayor | ½" wg | 1" wg | 2" wg | 3" wg | 4" wg | 6" wg | 10" wg |
|---|---|---|---|---|---|---|---|
| ≤ 8" | 26 | 26 | 26 | 24 | 24 | 24 | 22 |
| 9-10" | 26 | 26 | 26 | 24 | 22 | 20 | 18 |
| 11-12" | 26 | 26 | 24 | 22 | 20 | 18 | 16 |
| 13-14" | 26 | 24 | 22 | 20 | 18 | 18 | REF |
| 15-16" | 26 | 22 | 20 | 18 | 18 | 16 | REF |
| 17-18" | 26 | 22 | 20 | 18 | 16 | REF | REF |
| 19-20" | 24 | 20 | 18 | 16 | REF | REF | REF |
| 21-22" | 22 | 18 | 16 | 16 | REF | REF | REF |
| 23-24" | 22 | 18 | 16 | 16 | REF | REF | REF |
| 25-26" | 20 | 18 | REF | REF | REF | REF | REF |
| 27-30" | 18 | 16 | REF | REF | REF | REF | REF |
| 31-36" | 16 | REF | REF | REF | REF | REF | REF |
| ≥ 37" | REF | REF | REF | REF | REF | REF | REF |

**REF** = refuerzo obligatorio, no existe opción sin reforzar.

**Espaciamientos de refuerzo:** cada tabla ofrece 8 columnas — **10' / 8' / 6' / 5' / 4' / 3' /
2½' / 2'** (3,0 / 2,4 / 1,8 / 1,5 / 1,2 / 0,90 / 0,75 / 0,60 m). Cada celda trae
`LETRA-CALIBRE`: la letra es el grado mínimo de refuerzo (A…L) y el número el calibre mínimo.
**A menor espaciamiento, menor calibre admisible.** Ejemplo literal (Tabla 1-5, 2" wg, ducto
31-36"): `G-16 | G-18 | F-20 | F-22 | E-24 | E-26 | D-26 | D-26` → con refuerzos cada 10' se
necesita calibre 16 grado G; cada 3', basta calibre 26 grado E.

> ⚠️ Los perfiles físicos de los grados A-L (Tabla 1-10) están como **imágenes** en la fuente
> abierta → **NO VERIFICADO / no transcrito**.

**Crossbreaking** (afecta mano de obra), literal:
> «Duct sides that are 19" (483 mm) and over and are 20 gage (1.00 mm) or less, with more than
> 10 square feet (0,93 m²) of unbraced panel area, shall be crossbroken or beaded… unless they are
> lined or externally insulated.»

### D.4.3 Ducto redondo (SMACNA Tabla 3-2A, sin refuerzo, presión positiva)

Formato `espiral / longitudinal`:

| Ø máx | +2" wg | +4" wg | +10" wg |
|---|---|---|---|
| 12" | 28/26 | 28/26 | 26/24 |
| 16" | 26/24 | 26/24 | 24/22 |
| 27-36" | 24/22 | 22/20 | 22/20 |
| 37-50" | 22/20 | 20/20 | 20/20 |
| 51-60" | 20/18 | 18/18 | 18/18 |
| 61-84" | 18/16 | 18/16 | 18/16 |

## D.5 Porcentaje de desperdicio en ductos

> ⚠️ **NO EXISTE EN NINGUNA NORMA.** Se buscó en el texto íntegro de SMACNA los términos *waste*,
> *scrap*, *allowance* y *estimating*: **cero resultados sobre desperdicio**. SMACNA es una norma
> de **construcción**, no de metrado — no fija ningún porcentaje. La afirmación circulante de que
> «SMACNA usa 15 %» es **NO VERIFICADA**.

Lo citable es un **criterio de práctica de estimación**, no una norma:
D'Amelio, Joseph — *Mechanical Estimating Manual: Sheet Metal, Piping and Plumbing*.
PDF local: `docs/normas/DAmelio-Mechanical-Estimating-Manual.pdf` ·
URL: <https://www.iqytechnicalcollege.com/BAE%20690-Mechanical%20Estimating.pdf>

| Concepto | % | Pág. |
|---|---|---|
| **Ducto galvanizado (rectangular y redondo)** | **20 %** | 114, 118, 122 |
| Forro acústico / aislamiento interior | **15 %** | 192 |
| Carcasas (*housings*) de plancha | 30 % | 192 |
| Ducto de aluminio | 20 % | 173 |

Cita literal (p. 114):
> «…then multiplied by the weight per sq ft of metal for that gauge, and finally a **20 % allowance
> is added for waste, hangers, cleats, seams, etc.**»

y p. 193: «If the poundage figures already have the **standard 20 % waste** in them…»

> ⚠️ **Dos advertencias sobre ese 20 %:**
> 1. **No es sólo desperdicio** — cubre «waste, hangers, cleats, seams, hardware». Si el motor
>    metra soportes en partida aparte, estaría **duplicando**.
> 2. Los valores de **10 %, 25 % y 30 % que circulan son NO VERIFICADOS** — sólo aparecen en blogs,
>    sin fuente primaria. RSMeans es de pago y no fue accesible.

### D.5.1 Tabla de estimación rápida por semiperímetro

D'Amelio p. 118, *«Weight of Galvanized Ductwork Per Linear Foot With 20 % Allowance»*:

| Semiperímetro (ancho + alto) | 0-12" | 13-30" | 31-54" | 55-84" | 85"+ |
|---|---|---|---|---|---|
| **Calibre asignado** | 26 | 24 | 22 | 20 | 18 |
| lb/ft² sin margen | 0,91 | 1,16 | 1,41 | 1,66 | 2,16 |
| **lb/ft² con 20 %** | **1,10** | **1,40** | **1,70** | **2,00** | **2,60** |
| **kg/m² con 20 %** | **5,37** | **6,83** | **8,30** | **9,76** | **12,69** |

> ⚠️ **Esta asignación de calibre por semiperímetro es criterio de estimación, más laxa que
> SMACNA.** Ejemplo: ducto 40"×14" (semiperímetro 54") → esta tabla dice calibre 22; SMACNA a
> 2" wg con dimensión mayor 40" exige refuerzo obligatorio y hasta calibre 16 según espaciamiento.
> **Para presupuestar sirve; para especificar, manda SMACNA.**
>
> Los rangos «hasta 12" / 13-30" / 31-54" / 55-84" / 85+» que suelen atribuirse a SMACNA **son de
> esta tabla de estimación por semiperímetro**, no de SMACNA. SMACNA usa la **dimensión mayor**
> con rangos mucho más finos (D.4.2). Confundirlos da resultados muy distintos.

## D.6 Aislamiento térmico de ductos

**Unidad de medida: m²** (ft² en fuentes estadounidenses). Todas las fuentes metran y precian por
superficie.

**Fuente:** NAIMA / Insulation Institute, *A Guide to Insulated HVAC Duct Systems* (AH121).
PDF local: `docs/normas/NAIMA-AH121-guide-insulated-HVAC-ducts.pdf` ·
URL: <https://insulationinstitute.org/wp-content/uploads/2015/11/AH121.pdf>

| Producto | Espesores comerciales | Norma ASTM |
|---|---|---|
| **Duct liner** (forro interior) | **½" a 2"** (13 – 51 mm) | ASTM C1071 |
| **Duct wrap** (manta exterior) | **1½" a 4"** (38 – 102 mm) | ASTM C1290 |
| **Insulation board** (placa exterior) | **1" a 4"** (25 – 102 mm), incrementos de ½" | ASTM C612 |

**El ½" existe sólo en duct liner.** El duct wrap comercial arranca en 1½".

Valores R (ASTM C518 a 75 °F): placa 1" = R4,0-4,5 · 2" = R8,0-9,0 · 4" = R16-18.
Manta 1" = R3,1-3,6 · 2" = R5,6-8,3 · 4" = R11,2-16,6.

**Regla de instalación:** la manta **no debe comprimirse a menos del 75 % de su espesor nominal**
→ hay que calcular el *stretch-out*.

Densidades verificadas (D'Amelio p. 193, duct liner): **1½ lb/ft³ = 24 kg/m³** (referencia base) ·
2 lb/ft³ = 32 kg/m³ (½") · 3 lb/ft³ = 48 kg/m³.

> ⚠️ **NO VERIFICADO:** densidades de duct wrap exterior (se citan 0,75 / 1,0 / 1,5 pcf sin fuente
> primaria; los PDF de CertainTeed devolvieron 403).
>
> **SMACNA no fija espesores ni densidades de aislamiento** — literal: «specify the material,
> thickness, density, and performance characteristics desired»; lo delega al proyectista.

**Impacto del forro interior sobre el metrado de plancha** — D'Amelio p. 193: «increase a
20 × 10 duct to 22 × 12 for 1" thick lining» → el peso de plancha sube **≈ 12 % con forro de 1"** y
**≈ 6 % con ½"**. El motor debe agrandar la sección **antes** de calcular el perímetro.

## D.7 Rejillas, difusores y ventiladores

**Unidad: Und.** Normativamente confirmado para Perú en la RD 073-2010, OE.5.6: todos los equipos
electromecánicos se miden por unidad instalada (OE.5.6.12 campanas extractoras, OE.5.6.16 sistema
de ventilación mecánica, OE.5.6.18 sistema de aire acondicionado), con la forma de medición
literal «Para el cómputo total se considerará el equipo instalado».

> ⚠️ **NO VERIFICADO que exista norma peruana que mande metrar ducto HVAC en kg.** La RD 073-2010
> **no tiene partida específica de «ducto de plancha galvanizada» ni de «rejilla/difusor» por
> separado** — los engloba en el sistema (Und/Glb). Si se necesita metrar ducto en kg, esa
> desagregación es **criterio de proyecto**, apoyado en SMACNA para el espesor y en D'Amelio para
> el desperdicio.

---

# E. Archivos normativos descargados

Todos en `C:\Users\ingvi\Proyectos\metra-ai\docs\normas\`:

| Archivo | Documento | URL de origen |
|---|---|---|
| `RD-073-2010-Norma-Metrados-mirror.pdf` · `RD-073-2010-VIVIENDA-VMCS-DNC-SPIJ.pdf` | Norma Técnica Metrados para Obras de Edificación y Habilitaciones Urbanas (RD 073-2010-VIVIENDA/VMCS-DNC). Movimiento de tierras en OE.2.1 y HU.3.4; sanitarias en OE.4 (pág. 79-87); eléctricas y mecánicas en OE.5 (pág. 90-98) | Oficial SPIJ-MINJUS, 154 pág. con texto seleccionable: <https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf> |
| `RNE-OS.050-redes-agua.pdf` | OS.050 Redes de Distribución de Agua para Consumo Humano (DS 010-2009) | <https://cdn.www.gob.pe/uploads/document/file/2365676/21%20OS.050%20REDES%20DE%20DISTRIBUCION%20DE%20AGUA%20PARA%20CONSUMO%20HUMANO%20DS%20N%C2%B0%20010-2009.pdf> |
| `RNE-OS.050-capeco.pdf` | OS.050 (edición ICG/CAPECO) | <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo2/03_OS/RNE2009_OS_050.pdf> |
| `RNE-OS.070-redes-aguas-residuales.pdf` | OS.070 Redes de Aguas Residuales | <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo2/03_OS/RNE2009_OS_070.pdf> |
| `RNE-IS.010-instalaciones-sanitarias.pdf` | IS.010 Instalaciones Sanitarias para Edificaciones (+ IS.020 Tanques Sépticos) | <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo3/03_IS/RNE2006_IS_010.pdf> |
| `RNE-EM.010-instalaciones-electricas.pdf` | EM.010 Instalaciones Eléctricas Interiores (+ EM.020) | <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo3/04_EM/RNE2006_EM_010.pdf> |
| `RNE-G.050-seguridad-construccion.pdf` | G.050 Seguridad durante la Construcción (DS 010-2009), con Anexo I de taludes y entibados | <https://cdn.www.gob.pe/uploads/document/file/2365155/05%20G.050%20SEGURIDAD%20DURANTE%20LA%20CONSTRUCCI%C3%93N%20DS%20N%C2%B0%20010-2009.pdf> |
| `CNE-Utilizacion-2006-RM-037-2006-MEM.pdf` | Código Nacional de Electricidad – Utilización (836 pág.) | <https://spij.minjus.gob.pe/Graficos/Peru/2006/Enero/30/RM-037-2006.pdf> |
| `SEDAPAL-CTPS-ET-002-pruebas-hidraulicas.pdf` | SEDAPAL CTPS-ET-002 Pruebas hidráulicas de redes de AP y alcantarillado | <https://www.sedapal.com.pe/storage/objects/ctps-et-002-pruebas-hidraulicas-de-redes-de-ap-y-alcant.pdf> |
| `SEDAPAL-ctps-et-008-revision-02.pdf` | SEDAPAL CTPS-ET-008 Instalación, rehabilitación y/o reposición de líneas de AP y alcantarillado (Rev. 02, 2021) | <https://www.sedapal.com.pe/storage/objects/ctps-et-008-revision-02.pdf> |
| `RM-192-2018-VIVIENDA-saneamiento-rural.pdf` | Norma Técnica de Diseño: Opciones Tecnológicas para Sistemas de Saneamiento en el Ámbito Rural (189 pág.) | <https://cdn.www.gob.pe/uploads/document/file/1743222/ANEXO%20RM%20192-2018-VIVIENDA%20B.pdf.pdf> |
| `RNE-EM.030-instalaciones-ventilacion.pdf` | EM.030 Instalaciones de Ventilación | <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo3/04_EM/RNE2006_EM_030.pdf> |
| `RNE-EM.020-instalaciones-comunicaciones.pdf` | EM.020 Instalaciones de Comunicaciones | <https://cdn-web.construccion.org/normas/rne2012/rne2006/files/titulo3/04_EM/RNE2006_EM_020.pdf> |
| `IS.010-DIGESA-MINSA.pdf` | IS.010 (edición DIGESA-MINSA; **es la única cuya tabla de cajas de registro es texto y no imagen**) | <https://www.digesa.minsa.gob.pe/NormasLegales/Normas/IS.010.pdf> |
| `OPS-CEPIS-05.147-construccion-redes-distribucion.pdf` | OPS/CEPIS/05.147 UNATSABAR — **ancho de zanja, cama de apoyo, relleno** | <https://sswm.info/sites/default/files/reference_attachments/OPS%202005a.%20Construcci%C3%B3n%20de%20redes%20de%20distribuci%C3%B3n.pdf> |
| `OPS-CEPIS-05.169-alcantarillado.pdf` | OPS/CEPIS/05.169 UNATSABAR — alcantarillado | <https://sswm.info/sites/default/files/reference_attachments/CEPISO~1.PDF> |
| `Pavco-Wavin-FT-agua-fria.pdf` | Ficha técnica PVC agua fría (NTP 399.002 y 399.166) | <https://mediahub.wavin.com/m/41c952d855656fc6/original/FICHA-TECNICA-AGUA-FRIA-PAVCO-WAVIN.pdf> |
| `Pavco-Wavin-FT-desague.pdf` | Ficha técnica PVC desagüe (NTP 399.003) | <https://mediahub.wavin.com/m/34795a652669b131/original/Ficha-Tecnica-Desague-PavcoWavin.pdf> |
| `Pavco-Wavin-FT-grandes-diametros-ISO1452.pdf` | Ficha técnica grandes diámetros ISO 1452 | <https://mediahub.wavin.com/m/b81b05984b218cd1/original/Ficha_Tecnica_Grandes_Diametros_Pavco_Wavin-pdf.pdf> |
| `Tigre-Peru-Catalogo-Productos.pdf` | Tigre Perú — catálogo más completo (399.002 ½"–12", 399.166, 399.003, ISO 1452, ISO 4435) | <https://tigresite.s3.amazonaws.com/2022/01/Catalogo-de-Productos-Tigre-Peru-Compras.pdf> |
| `Nicoll-FT-desague-NTP-399.003.pdf` | Nicoll — desagüe NTP 399.003 (**único fabricante con 8"**) | <https://grupoaliaxis.s3.us-east-2.amazonaws.com/nicoll-peru/Ficha+tecnica/Edificaci%C3%B3n/Ficha+T%C3%A9cnica+Tubos+para+Instalaciones+Sanitarias+NTP+399.003+Nicoll.pdf> |
| `MEF-catalogo-familias-tubos-PVC.pdf` | MEF/SIGA — catálogo de familias de tubos PVC (terminología SAL/SAP) | <https://www.mef.gob.pe/contenidos/doc_siga/catalogo/ctlogo_familias_tubos_PVC.pdf> |
| `MTC-Manual-Carreteras-DG-2018.pdf` | MTC — Manual de Carreteras: Diseño Geométrico DG-2018 (**Tablas 304.10 y 304.11 de taludes**) | <https://portal.mtc.gob.pe/transportes/caminos/normas_carreteras/documentos/manuales/Manual.de.Carreteras.DG-2018.pdf> |
| `WYDOT-Survey-Manual-AppF-Volume.pdf` | WYDOT Survey Manual, Appendix F «Volume» (**fórmulas de áreas medias, prismoidal, corrección prismoidal, tronco de pirámide**) | <https://www.dot.state.wy.us/files/live/sites/wydot/files/shared/Highway_Development/Surveys/Survey%20Manual/Appendix%20F%20-%20Volume.pdf> |
| `Pavco-Wavin-FT-sistema-electrico.pdf` | Pavco Wavin — tubos PVC-SEL y PVC-SAP eléctricos (NTP 399.006), ed. set. 2024 | <https://mediahub.wavin.com/asset/b5982f36-1a66-4c58-a441-cbbb7c9b1619/Ficha-Tecnica-Sistema-Electrico-Pavco-Wavin.pdf> |
| `INDECO-THW-90-AWG-hasta-8.pdf` | INDECO/Nexans — THW-90 línea AWG hasta 8 AWG (pesos kg/km) | <https://www.nexans.pe/.rest/catalog/v1/family/pdf/21802/THW-90-AWG> |
| `INDECO-THW-90-AWG-kcmil.pdf` | INDECO/Nexans — THW-90 desde 6 AWG hasta 500 kcmil | <https://www.nexans.pe/.rest/catalog/v1/family/pdf/21811/THW-90-AWG> |
| `INDECO-THW-90-metrico.pdf` | INDECO/Nexans — THW-90 línea métrica desde 16 mm² | <https://www.nexans.pe/.rest/catalog/v1/family/pdf/21807/THW-90> |
| `INDECO-NH-80-Freetox.pdf` | INDECO/Nexans — NH-80 libre de halógenos, 1,5 a 10 mm² | <https://www.nexans.pe/.rest/catalog/v1/family/pdf/21922/FREETOX-NH> |
| `INDECO-NHX-90-Freetox.pdf` | INDECO/Nexans — NHX-90/LSOHX-90 desde 16 mm² | <https://www.nexans.pe/.rest/catalog/v1/family/pdf/21927/FREETOX-NH> |
| `SMACNA-HVAC-Duct-Construction-Standards-1995.html` | **SMACNA HVAC Duct Construction Standards, 2ª ed. 1995, texto completo gratuito** (incorporado por referencia en el CFR de EE.UU.) | <https://law.resource.org/pub/us/cfr/ibr/005/smacna.duct.1995.html> |
| `DAmelio-Mechanical-Estimating-Manual.pdf` | D'Amelio, *Mechanical Estimating Manual* (**% de desperdicio de ductos**) | <https://www.iqytechnicalcollege.com/BAE%20690-Mechanical%20Estimating.pdf> |
| `NAIMA-AH121-guide-insulated-HVAC-ducts.pdf` | NAIMA / Insulation Institute — *A Guide to Insulated HVAC Duct Systems* | <https://insulationinstitute.org/wp-content/uploads/2015/11/AH121.pdf> |

**Fuentes consultadas pero NO descargadas al repositorio** (por tamaño o por licencia):

| Documento | URL | Motivo |
|---|---|---|
| Caterpillar *Performance Handbook*, Ed. 29 (1014 pág.) | <http://courses.washington.edu/esrm468/468%20Class%20material/PHB29.pdf> | Manual comercial alojado por una universidad para uso docente; se cita, no se redistribuye |
| MTC EG-2013 Especificaciones Técnicas Generales (1282 pág.) | <https://portal.mtc.gob.pe/transportes/caminos/normas_carreteras/documentos/manuales/MANUALES%20DE%20CARRETERAS%202019/MC-01-13%20Especificaciones%20Tecnicas%20Generales%20para%20Construcci%C3%B3n%20-%20EG-2013%20-%20(Versi%C3%B3n%20Revisada%20-%20JULIO%202013).pdf> | Tamaño |
| KSU CE-417 cap. 2 (Nunnally, Ec. 2-4 a 2-9 y Table 2-5) | <https://faculty.ksu.edu.sa/sites/default/files/2.ce417-note-ch2.pdf> | Apuntes docentes |
| OSHA 29 CFR 1926 Subpart P, Apéndices A y B | <https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926SubpartPAppB> | Recurso web, no PDF |
| APU obra pública Tumbes 2022 (evidencia de conductor por punto) | <https://regiontumbes.gob.pe/piloto/documentos/Obras%20con%20Cambios/EFRAIN%20ARCAYA%20ZEVALLOS/4.-%20INFORMACION%20ACTUALIZADA%20EFRAIN%20ARCAYA%20ZEVALLOS/2.%20PRESUPUESTOS/05%20-%20ELECTRICAS/analisissubpresupuesto2varios.pdf> | Documento de obra, no norma |

> ⚠️ `RM-192-2018-VIVIENDA-saneamiento-rural.pdf` es **PDF escaneado sin capa de texto**
> (0 caracteres extraíbles). Requiere OCR si se quiere explotar automáticamente.
>
> ⚠️ Varios enlaces de `cdn.www.gob.pe` devuelven **403 a peticiones automatizadas**; se descargan
> con un User-Agent de navegador (`Invoke-WebRequest -UserAgent "Mozilla/5.0 ..."` o
> `curl -A "..."`), que es lo que se usó aquí.
>
> ⚠️ El PDF local de SEDAPAL CTPS-ET-002 es la **Rev. 00 (2015-07-31)**. Existe una
> **Rev. 02 (2023)** publicada en gob.pe:
> <https://cdn.www.gob.pe/uploads/document/file/5976676/5295689-ctps-et-002-pruebas-en-redes-y-en-estructuras-de-almacenamiento-del-sistema-de-agua-potable-y-alcantarillado.pdf>
> — los valores de presión y duración de prueba **coinciden** entre ambas revisiones.

---

# F. Correcciones a supuestos frecuentes

Estos son errores que circulan como si fueran norma. El motor **no debe** reproducirlos:

| Supuesto extendido | Realidad verificada |
|---|---|
| «Instalaciones sanitarias es el capítulo OE.3 de la Norma de Metrados» | Es **OE.4**. OE.3 es Arquitectura. |
| «La IS.010 exige prueba de agua a 100 lb/pulg² durante 15 min» | **La IS.010 vigente no regula pruebas hidráulicas.** El valor viene de Especificaciones Técnicas de obra (allí aparece como **150 lb/pulg²**, 15 min). Para redes públicas manda SEDAPAL CTPS-ET-002 con presión = múltiplo de la presión nominal. |
| «IS.010: pendiente mínima de 2" es 2 %» | La IS.010 sólo fija **1 % para ≥ 100 mm** y **1,5 % para ≤ 75 mm**. El 2 % es práctica de ET. |
| «OS.050 / OS.070 traen la tabla de ancho de zanja» | **No la traen** (verificado leyendo ambas completas). La tabla peruana citable es la de OPS/CEPIS/05.147 (A.4.4.a). |
| «El diámetro mínimo de red de agua es 63 mm» | El mínimo general de **tubería principal es 75 mm** (OS.050 4.6). Los 63 mm son el mínimo del **empalme del ramal distribuidor** (OS.050 4.12). |
| «La EM.010 define diámetros de tubería, alturas de salida y secciones de conductor» | **No contiene ninguno de esos datos.** Remite todo al CNE-U. Sólo aporta iluminancias, evaluación de demanda, escalas de plano y componentes del proyecto. |
| «El CNE-U fija la altura de tomacorrientes en 0,40 m» | **El CNE-U no fija alturas de montaje.** Lo único normativo es accesibilidad (Norma A.120: interruptores ≤ 1,35 m; tomacorrientes 0,40 – 1,20 m en hospedaje). |
| «Se asignan 0,20 – 0,30 m de cola de conductor por caja» | El único valor con base normativa es **0,15 m (150 mm)** — CNE-U **070-3002(4)**, y coincide con el APU de obra pública revisado. Lo demás es criterio del proyectista. |
| «El pozo a tierra normado es de 0,80-1,00 m de Ø × 2,40-3,00 m» | **El CNE-U no menciona el diámetro de la excavación.** Sólo exige varilla ≥ 2,0 m y profundidad alcanzada ≥ 2,5 m (060-702). |
| «La NTP 399.166 es de tubería eléctrica» | Es de **tubos PVC para fluidos a presión con unión roscada** (agua fría). La eléctrica es la **NTP 399.006**. |
| «SMACNA fija 15 % de desperdicio en ductos» | **SMACNA no fija ningún porcentaje de desperdicio** (búsqueda en el texto íntegro). Lo citable es el **20 %** de D'Amelio, y cubre también soportes y costuras. |
| «Los rangos de calibre de ducto 0-12 / 13-30 / 31-54 / 55-84 / 85+ son de SMACNA» | Son de la **tabla de estimación por semiperímetro** de D'Amelio. SMACNA usa la **dimensión mayor** con rangos mucho más finos. |
| «G.050 exige entibado a partir de 1,50 m de profundidad» | **No aparece en el texto de la norma.** G.050 remite el entibado al análisis de trabajo / estudio de suelos. Los umbrales numéricos que sí existen son otros: escalera a partir de 1,20 m, material a ≥ 2 m del borde, barreras a ≥ 1,80 m. |
| «Se paga la excavación en volumen esponjado» | Se paga **en banco**. MTC EG-2013 §202.21: «material excavado **en su posición original**». El esponjamiento va al APU o (sólo en edificación) a la partida de eliminación — **nunca en ambos**. |
| «El factor de esponjamiento de la Norma de Metrados es el *load factor*» | Es su **inverso**. El factor peruano es `1 + Swell` (banco→suelto); el *load factor* de Caterpillar es `1/(1+Swell)` (suelto→banco). |

# G. Pendientes y datos NO verificados

## G.1 Movimiento de tierras

1. **Tabla de ancho de zanja con norma peruana de rango superior.** El RNE no la publica. La
   especificación SEDAPAL **CTPS-ET-006 «Movimiento de Tierras»** no se pudo descargar: los
   patrones de URL probados devolvieron 404 y la página índice de SEDAPAL devuelve 404/418.
   **Acción manual:** <https://www.sedapal.com.pe/especificaciones-tecnicas>. Mientras tanto se usa
   la tabla OPS/CEPIS (A.4.4.a), que sí es peruana y descargable.
2. **Ancho de zanja para DN > 200 mm**: ninguna fuente peruana oficial descargable lo tabula.
   Aplicar `OD + 0,30 m` (regla base OPS/CEPIS) o ASTM D2321.
3. **EN 1610 Tablas 1 y 2**: valores tomados de resúmenes secundarios, no del texto original
   (norma de pago).
4. **RM 192-2018-VIVIENDA**: PDF escaneado sin capa de texto. Podría contener tabla de ancho de
   zanja y cama de apoyo para saneamiento rural. Requiere OCR.
5. **Coeficiente 3 (h₃) del método de cuadrícula**: no aparece escrito explícitamente en las
   fuentes abiertas consultadas; se deduce del criterio «número de celdas que comparten el
   vértice». El principio de ponderación sí está verificado.
6. **Simpson aplicado a curvas de nivel**: sin fuente citable; la fuente consultada recomienda
   explícitamente la regla trapezoidal.
7. **Fuente peruana para «20-30 % de esponjamiento de material común» en APU**: no existe. La
   palabra «esponjamiento» no aparece en EG-2013, DG-2018 ni el Manual de Suelos del MTC.
8. **Capacidades típicas de volquete en Perú (6/10/15/20 m³)** con fuente oficial: no encontrada.
   Vía correcta: Reglamento Nacional de Vehículos D.S. 058-2003-MTC.
9. **«Relleno lateral» como partida normada independiente**: no aparece con ese nombre en fuentes
   peruanas verificadas; queda absorbido en el *primer relleno*.

## G.2 Instalaciones sanitarias

10. **Espesores exactos de ASTM D2241**: ningún catálogo peruano cita esa norma para la serie en
    pulgadas; citan NTP 399.002 y NTP 399.166.
11. **Eurotubo** (todos los espesores): su único catálogo es PDF escaneado sin capa de texto.
12. **Vinilit / Amanco Perú**: sin fuentes; no aparecen como fabricantes activos en Perú.
13. **Espesores Pavco ISO 1452 en 63-400 mm**: su ficha no tiene capa de texto.
14. **DE real de 10" y 12" (NTP 399.002)**: Tigre da espesores, ninguna fuente da el DE.
15. **Espesor Pavco C-15 en 6"**: vende el código pero deja la celda en blanco.
16. **Espesor SAP 2" de desagüe**: Pavco dice 1,7 mm y Nicoll 2,0 mm. Discrepancia real entre
    fabricantes, no errata.

## G.3 Instalaciones eléctricas

17. **Texto de ASTM B258** (AWG): de pago. La fórmula es reproducible pero la atribución
    normativa no se verificó en fuente primaria.
18. **Textos de NTP 399.006, NTP 370.252, NTP 370.016 e IEC 60228**: de pago (INACAL/IEC). Los
    datos provienen de catálogos que las citan.
19. **CEPER Cables**: sin web funcional ni catálogo oficial descargable. Usar INDECO.
20. **Tensión SEL 5/8" vs CNE-U 070-1004**: la lectura de que el SEL de 5/8" queda por debajo del
    mínimo de 15 mm nominal es una **interpretación de dos textos, no una posición oficial**.
    Validar con proyectista eléctrico colegiado.
21. **Especificaciones técnicas de PRONIED**: el servidor estuvo caído durante la investigación.
    Habría sido la mejor fuente peruana de alturas de salidas y APU de referencia.

## G.4 Instalaciones mecánicas / HVAC

22. **SMACNA 4ª edición (2020)**: de pago. **No verificado** si sus tablas difieren de la de 1995
    usada aquí.
23. **Grados de refuerzo A-L de SMACNA (Tabla 1-10)**: son imágenes en la fuente abierta; no
    transcritos.
24. **Desperdicios de 10 %, 25 % y 30 % para ducto**: sólo en blogs, sin fuente primaria.
    RSMeans es de pago e inaccesible.
25. **Densidades comerciales de duct wrap exterior** (0,75 / 1,0 / 1,5 pcf): sin fuente primaria.
26. **Norma peruana que mande metrar ducto HVAC en kg**: no existe. La RD 073-2010 sólo tiene
    Und/Glb para sistemas de ventilación y aire acondicionado.
27. **EM.040 / EM.050 y ediciones vigentes de EM.030**: no revisadas en detalle.
</content>
</invoke>
