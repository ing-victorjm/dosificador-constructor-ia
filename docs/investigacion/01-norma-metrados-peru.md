# Norma Técnica de Metrados para Obras de Edificación y Habilitaciones Urbanas (Perú)

> Investigación de base para el catálogo de partidas del motor de metrados de **metra-ai**.
> Fecha de la investigación: **2026-09-02**.

---

## 1. Fuente

| Dato | Valor |
|---|---|
| Documento | Norma Técnica **"Metrados para Obras de Edificación y Habilitaciones Urbanas"** |
| Norma que la aprueba | **R.D. N° 073-2010-VIVIENDA/VMCS-DNC** |
| Emisor | Ministerio de Vivienda, Construcción y Saneamiento (MVCS) — Viceministerio de Construcción y Saneamiento, **Dirección Nacional de Construcción (DNC)** |
| PDF oficial descargado | <https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf> (SPIJ — Sistema Peruano de Información Jurídica, MINJUS) |
| Copia local | `C:\Users\ingvi\Proyectos\metra-ai\docs\normas\RD-073-2010-VIVIENDA-VMCS-DNC-SPIJ.pdf` (1 187 020 bytes, 154 páginas, PDF 1.6 con capa de texto) |
| Espejo secundario | `RD-073-2010-Norma-Metrados-mirror.pdf` (11,5 MB, 156 páginas, **escaneado sin capa de texto** — solo respaldo visual). Origen: <https://waltervillavicencio.com/wp-content/uploads/2021/09/RD-073-2010-VIVIENDA-VMCS-DNC-Norma-Tecnica-Metrados-para-Obras-de-Edificacion-y-Habilitaciones-Urbanas.pdf> |
| Metadatos del PDF oficial | `title: RD_2010_073_DNC.pdf`, `author: jalzamora`, `creationDate: 2010-05-24`, `modDate: 2011-12-13` |

### Nota de publicación (literal, página 1 del PDF)

> "(Esta Norma Técnica no ha sido publicada en el Diario Oficial 'El Peruano', se descargó de la
> página web del Ministerio de Vivienda, Construcción y Saneamiento, con fecha 12 de diciembre de 2011.)"

Es decir: el texto íntegro de la Norma Técnica **no se publicó en El Peruano**; circula como anexo
descargable del MVCS y está replicado en el repositorio jurídico oficial SPIJ del MINJUS, que es la
fuente que se usó aquí.

### Vigencia y campo de aplicación

Texto literal del **Título I, numeral 3**:

> "La Norma Técnica 'Metrados para Obras de Edificación y Habilitaciones Urbanas' es de aplicación
> **obligatoria** en la elaboración de los Expedientes Técnicos para Obras de Edificación y para
> Habilitaciones Urbanas **en todo el territorio nacional**."

Objetivo (Título I, numeral 2): *"Establecer criterios mínimos actualizados para cuantificar las
partidas que intervienen en un presupuesto para Obras de Edificación (OE) y Habilitaciones Urbanas (HU)."*

**Antecedentes que reemplaza / referencias normativas** (Título I, numeral 4, literal):

- Reglamento de Metrados para Obras de Edificación — D.S. N° 013-79-VC (1979-04-26)
- Reglamento de Metrados para Habilitaciones Urbanas — D.S. N° 028-79-VC (1979-09-27)
- Reglamento de Metrados y Presupuestos. Infraestructura Sanitaria para Poblaciones Urbanas — D.S. N° 09-94-TCC (1994-04-28)
- Reglamento Nacional de Edificaciones — D.S. 011-2006-VIVIENDA (2006-05-08)
- Reglamento de Elaboración de Proyectos de Agua Potable y Alcantarillado para Habilitaciones Urbanas de Lima Metropolitana y Callao — D.S. N° 09-94-TCC
- Ley de Contrataciones del Estado (D. Leg. 1017) y su Reglamento (D.S. 184-2008-EF)

> ⚠️ **No verificado (`verificado: false`)**: la fecha exacta de emisión de la R.D. N° 073-2010 y su
> estado de vigencia/derogación a 2026 no se pudieron confirmar contra una fuente primaria en esta
> sesión (se agotó el presupuesto de búsquedas web). El único indicio duro es la fecha de creación
> del PDF oficial: **2010-05-24**. La Ley de Contrataciones citada (D. Leg. 1017) fue reemplazada
> posteriormente por la Ley 30225 y luego por la Ley 32069, pero **eso no deroga la norma de metrados**:
> la remisión es solo conceptual (definiciones de "metrado", "contratista", "bases").
> Antes de dar el catálogo por definitivo conviene contrastar con el portal del MVCS.

---

## 2. Estructura del documento

```
TÍTULO I — GENERALIDADES
  1. Prefacio   2. Objetivo   3. Campo de aplicación
  4. Referencias normativas   5. Glosario (5.1 a 5.14)

TÍTULO II — METRADOS PARA OBRAS DE EDIFICACIÓN  (prefijo OE)
  OE.1  Obras provisionales, trabajos preliminares, seguridad y salud
  OE.2  Estructuras
  OE.3  Arquitectura
  OE.4  Instalaciones sanitarias
  OE.5  Instalaciones eléctricas y mecánicas
  OE.6  Instalaciones de comunicaciones
  OE.7  Instalaciones de gas

TÍTULO III — METRADOS PARA HABILITACIONES URBANAS  (prefijo HU)
  HU.1  Obras provisionales, trabajos preliminares, seguridad y salud
  HU.2  Pistas y veredas
  HU.3  Infraestructura sanitaria
  HU.4  Infraestructura eléctrica
  HU.5  Infraestructura de comunicaciones
  HU.6  Infraestructura de gas
```

Cada capítulo se organiza en un índice enumerado (`OE.2.3.9.2`, hasta 5–6 niveles) y luego un cuerpo
donde cada partida trae, en este orden:

1. **Título** (código + descripción en mayúsculas)
2. **Descripción / Extensión de trabajo** — el alcance de lo que comprende la partida
3. **Unidad de Medida** — a veces una tabla `Descripción | Unidad de medida` con subpartidas
4. **Forma de medición** — la regla literal de cómputo

> El campo `alcance` del JSON captura el punto 2 y `regla_medicion` el punto 4.

### Jerarquía de partidas según el propio glosario (5.11)

| Orden | Nombre en la norma | Uso |
|---|---|---|
| 1er orden | Partidas Título | Agrupan partidas de características similares |
| 2do orden | Partidas Sub-título / Básicas | Labor en general, sin detalle |
| 3er orden | Partidas Básicas | Partidas específicas, mayor precisión de trabajo |
| 4to orden | — | Casos excepcionales, mayor especificidad |

Esto justifica el campo `nivel` del JSON (1 = capítulo OE.x, 2 = grupo, 3+ = partida ejecutable).
**Para el motor de metrados, las partidas presupuestables son las de nivel ≥ 3** (y algunas de nivel 2
que sí traen unidad y forma de medición propias).

### Definiciones operativas del glosario (Título I, 5)

- **5.7 Forma de Medición**: *"Es la manera en que el encargado de metrar debe de medir los productos o servicios que componen una obra de edificación o habilitación urbana."*
- **5.9 Metrado**: *"el cálculo o la cuantificación por partidas de la cantidad de obra a ejecutar."*
- **5.11 Partida**: *"Cada uno de los productos o servicios que conforman el presupuesto de una Obra."*
- **5.14 Unidad de Medida**: *"Es una cantidad estandarizada de una determinada magnitud física."*

---

## 3. Unidades de medida que realmente usa la norma

Extraídas leyendo **todas** las etiquetas "Unidad de Medida" del PDF:

| Código | Literal en la norma | Frecuencia aprox. (partidas del JSON) |
|---|---|---|
| `m2` | Metro cuadrado (m2) | 239 |
| `und` | Unidad (Und.) | 213 |
| `m` | Metro (m) / Metro lineal (m) | 121 |
| `m3` | Metro cúbico (m3) | 99 |
| `glb` | Global (Glb.) | 34 |
| `kg` | Kilogramo (kg) | 28 |
| `pto` | **Punto (Pto.)** / Punto de red (Pto.) | 8 |
| `h` | **Hora (h)** | 2 |
| `km` | **Kilómetro (km)** | como unidad alternativa (HU.1, redes) |

> ⚠️ **Discrepancia con el encargo.** El encargo pedía usar `m, m2, m3, kg, und, glb, p2, pza`.
> Las unidades **`p2` (pie cuadrado) y `pza` (pieza) NO aparecen en esta norma**: son unidades del
> catálogo comercial S10/CAPECO, no de la R.D. 073-2010. En cambio la norma sí usa **`pto`, `h` y `km`**,
> que no estaban en la lista. El JSON respeta la norma, no la lista: no se inventó ninguna unidad.
> Si el catálogo de la app necesita `p2`/`pza`, deben venir de otra fuente (p. ej. carpintería de
> madera en pies cuadrados es práctica de mercado, no norma).

**Regla práctica m2 vs m3 vs und según la norma:**

- **m3** → todo lo que tiene volumen real de material: movimiento de tierras (excavación, corte,
  relleno, eliminación), concreto simple y armado en todos los elementos (cimientos, zapatas, vigas,
  columnas, losas, muros).
- **m2** → superficies: encofrado y desencofrado, muros y tabiques de albañilería, tarrajeos, revoques,
  cielorrasos, pisos, contrapisos, zócalos, coberturas, pintura, vidrios, nivelaciones de terreno.
- **m** → longitudes: contrazócalos, bruñas, juntas, tuberías (redes de distribución/alimentación,
  desagüe, gas), zanjas, cables, canaletas.
- **kg** → exclusivamente armadura de acero y estructuras metálicas (peso).
- **und** → conteo de piezas: puertas, ventanas, aparatos sanitarios, tableros, artefactos, válvulas,
  cámaras, buzones, arcos, cerrajería.
- **pto** → "punto" de instalación: salida de agua fría/caliente, salida de desagüe, salida eléctrica,
  salida/punto de red de comunicaciones.
- **glb** → lo no cuantificable geométricamente: seguridad y salud (PSST, EPC, señalización,
  capacitación, recursos de emergencia), conexión a red externa de medidores.

---

## 4. Reglas de medición clave (citas literales de la norma)

### 4.1 Descuento de vanos — la regla que más se equivoca

| Partida | Regla literal | Efecto |
|---|---|---|
| **OE.3.1 Muros y tabiques de albañilería** (m2) | *"Las áreas son netas, por lo tanto, se descontarán en la medición las áreas de los vanos de puertas, ventanas, mamparas y algunos otros vacíos si los hubiera."* | **Sí descuenta vanos, sin umbral mínimo** |
| **OE.2.3.6.2 Muros de concreto, tabiques y placas** (m3) | *"El volumen … se obtendrá multiplicando el área de la sección transversal horizontal por la altura. … **Se descontarán los vanos de puertas y ventanas.** El área de encofrado (y desencofrado) de ambas caras corresponde al área efectiva del contacto con el concreto."* | **Sí descuenta vanos** |
| **OE.3.2.1 Tarrajeo rayado primario** (m2) — y por remisión OE.3.2.2 a OE.3.2.4 | *"Se computarán todas las áreas netas a vestir o revocar. Por consiguiente **se descontarán los vanos o aberturas** y otros elementos distintos al revoque, como molduras, cornisas y demás salientes que deberán considerarse en partidas independientes."* | **Sí descuenta vanos**; molduras/cornisas van en partida aparte |
| **OE.3.3.1 Cielorraso con yeso** (m2) | *"Se medirá el área neta comprendida entre las caras laterales sin revestir de las paredes o vigas que limitan, **no se deducirán las áreas de columnas, ni huecos menores de 0,25 cm2**."* | **No descuenta** bajo umbral (ver nota de errata) |
| **OE.3.4.1 Contrapisos** y **OE.3.4.2 Pisos** (m2) | *"Para ambientes cerrados se medirá el área comprendida entre los muros sin revestir. … En todos los casos **no se descontarán las áreas de columnas, huecos, rejillas, etc., inferiores a 0,25 m2**."* | Umbral **0,25 m2** |
| **OE.3.4.3 Pisos de concreto** (m2) | *"…no se descontarán las áreas de columnas, huecos, rejillas, etc., inferiores a 0,25 m2."* | Umbral **0,25 m2** |
| **OE.3.6 Coberturas** (arquitectura, m2) | *"Se medirá el área neta ejecutada **sin descontar luces o huecos de áreas menores de 0,50 m2**."* | Umbral **0,50 m2** |
| **OE.2.5.5 Coberturas** (estructura de madera, m2) | *"Se medirá el área efectivamente cubierta **descontándose vacíos de un metro cuadrado y más**."* | Umbral **1,00 m2** |
| **OE.2.4.6.1 Coberturas con planchas corrugadas galvanizadas** (m2) | *"En el cómputo se considera la superficie geométrica realmente ejecutada, sin desarrollo de ondulaciones, juntas, etc. En todos los casos se descontará la superficie ocupada por cajones de ventilación, chimeneas, aberturas vidriadas, etc. **Iguales o mayores de 1,00 m2**."* | Umbral **1,00 m2** |
| **OE.3.5.2 Contrazócalos** (m) | *"…se mide el perímetro total, **se descuenta la medida de umbrales de puertas o de otros vanos pero se agrega la parte de contrazócalo que va en los derrames** de 5 a 10 cm. por derrame en la mayoría de los casos."* | Descuenta umbrales, **suma derrames** |
| **OE.4.2.2 Redes de distribución** / **OE.4.3.2 agua caliente** (m) | *"El cómputo se ejecutará por metro lineal **sin descontar la longitud de los accesorios**."* | **No descuenta** accesorios |

> **Errata de la norma detectada:** OE.3.3.1 dice literalmente *"huecos menores de 0,25 cm2"*.
> Es evidentemente un error de tipeo por **0,25 m2** (coherente con OE.3.4.1/OE.3.4.2/OE.3.4.3).
> El JSON conserva el texto literal; el motor debe usar 0,25 m2. Documentar la decisión.

**Resumen para implementar en el motor:**

```
umbral_descuento(partida) =
  0.00 m2 → muros y tabiques de albañilería (OE.3.1.x), tarrajeos/revoques (OE.3.2.x),
            muros de concreto (OE.2.3.6.x)            # descuenta TODO vano
  0.25 m2 → cielorrasos (OE.3.3.x), contrapisos y pisos (OE.3.4.1 – OE.3.4.3)
  0.50 m2 → coberturas de arquitectura (OE.3.6.x)
  1.00 m2 → coberturas de estructuras (OE.2.4.6.x, OE.2.5.5.x)
  n/a     → longitudes de tubería (no se descuentan accesorios)
```

### 4.2 Movimiento de tierras — esponjamiento

- **OE.2.1.3 Cortes** (m3): *"Se medirá el volumen natural del corte, **sin tener en cuenta el volumen de esponjamiento**."*
- **OE.2.1.4.1 Relleno con material propio** (m3): *"…calculando el volumen geométrico del vacío correspondiente a rellenar. … **El volumen de relleno en cimentaciones será igual al volumen de excavación, menos el volumen de concreto**…"*
- **OE.2.1.6 Eliminación de material excedente** (m3): *"…será igual a la diferencia entre el volumen excavado, menos el volumen del material necesario para el relleno compactado con material propio. **Esta diferencia será afectada por el esponjamiento**…"*

**Tabla de factores de esponjamiento (literal de la norma, OE.2.1.6 y HU.2.1.4):**

| Tipo de suelo | Factor |
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

*Nota de la propia norma: "Los valores anteriores son referenciales. Cualquier cambio debe sustentarse
técnicamente. Fuente: Características Físicas de los Suelos. Raúl S. Escalante. Cátedra Ingeniería de
Dragado — Escuela de Graduados de Ingeniería Portuaria. Argentina. 2007."*

**Criterio general de HU.3 (literal):** *"el cómputo de metrado de las partidas será neto, sin tener en
cuenta el volumen de esponjamiento (movimiento de tierras, materiales agregados, etc.), ni desperdicios
(acero estructural, materiales agregados, etc.), los mismos que irán como parte integrante del Análisis
de Precios de las Partidas correspondientes. Para el caso de eliminación de material excedente el
metrado final será afectado por el factor de esponjamiento de cada material."*

> **Regla de oro del motor:** el metrado es **neto y geométrico**. Desperdicios y esponjamiento van en
> el análisis de precios unitarios (APU), **no** en la cantidad — con la única excepción de la
> eliminación de material excedente.

### 4.3 Concreto armado — la tríada concreto / encofrado / acero

La norma **descompone toda partida de concreto armado en tres subpartidas** con unidades distintas:

```
OE.2.3.x.1  PARA EL CONCRETO                     → m3
OE.2.3.x.2  PARA EL ENCOFRADO Y DESENCOFRADO     → m2
OE.2.3.x.3  PARA LA ARMADURA DE ACERO            → kg
```

Aplica a: OE.2.3.1 cimientos reforzados, OE.2.3.2 zapatas, OE.2.3.3 vigas de cimentación,
OE.2.3.4 losas de cimentación, OE.2.3.5 sobrecimientos reforzados, OE.2.3.6 muros reforzados,
OE.2.3.7 columnas, OE.2.3.8 vigas, OE.2.3.9 losas, etc.

Reglas literales relevantes:

- **Encofrado (m2)**: *"El área de encofrado … será igual al **área efectiva de contacto con el concreto**."*
- **Zapatas (OE.2.3.2)**: *"El cómputo del peso de la armadura **no incluirá los arranques o anclajes de las columnas**. En el caso de zapatas conectadas, no incluirá dentro de ninguno de los cómputos las vigas de cimentación."*
- **Cimientos reforzados (OE.2.3.1)**: *"El cómputo del peso de la armadura **no incluirá vástagos ni arranques** para las columnas u otros elementos que vayan empotradas en los cimientos reforzados."*
- **Vigas (OE.2.3.8)**: *"En el cómputo del peso de la armadura, **se incluirá la longitud de las barras que van empotradas en los apoyos** de cada viga."*
- **Columnas (OE.2.3.7)**: *"Cuando las columnas van endentadas con los muros (columnas portantes o de amarre) **se considerará el volumen adicional de concreto que penetra en los muros**."*
- **Losas aligeradas (OE.2.3.9.2)**: *"El volumen de concreto … se obtendrá calculando el volumen total de la losa como si fuera maciza y **restándole el volumen ocupado por los ladrillos huecos**. El área de encofrado … se calculará **como si fueran losas macizas**, a pesar que no se encofra totalmente la losa sino la zona de las viguetas únicamente."*
- **Losas nervadas (OE.2.3.9.4)**: *"…volumen total como si fuera maciza y luego **descontando el volumen de los vacíos que quedan entre las nervaduras**. El área de encofrado se obtendrá calculando el área de su **proyección horizontal** como si fuese una losa plana."*
- **Losas macizas (OE.2.3.9.1)**: *"En caso de existir frisos, estos deben considerarse (encofrado del borde de la losa)."*
- **Cimientos corridos (OE.2.2.1, concreto simple, m3)**: *"El cómputo total de concreto se obtiene sumando el volumen de cada uno de sus tramos. **En tramos que se cruzan se medirá la intersección una sola vez.**"*

### 4.4 Arquitectura — acabados

- **OE.3.4.2 Pisos** (m2): *"Para ambientes cerrados se medirá el área comprendida entre los **muros sin revestir**. Para ambientes libres se medirá la superficie señalada en los planos."* Cada tipo de piso (calidad, tamaño, mortero de base) va en **partida independiente**.
- **OE.3.4.1 Contrapisos** (m2): *"El área del contrapiso será **la misma que la del piso al que sirve de base**."*
- **OE.3.5.1 Zócalos** (m2): *"…se tomará el **área realmente ejecutada y cubierta por las piezas planas**, por consiguiente **agregando el área de derrames** y sin incluir la superficie de las piezas especiales de remate. … las piezas especiales, como son los contrazócalos, molduras, remates, medias cañas, etc., deben figurar en **partidas independientes en metros lineales (m)**."*
- **OE.3.10 Vidrios, cristales y similares** (m2): *"Se obtiene el área de cada sector a cubrir ya sea en ventana o mampara. Se deberá diferenciar en partidas independientes según **espesor y calidad** de vidrio o cristal."*
- **OE.3.11.1 Pintura de cielos rasos, vigas, columnas y paredes** (m2): *"Se medirán las **áreas netas a pintarse**, las que deberán estar concordante con revoque y enlucidos y estarán diferenciadas **por el tipo de pintura**."*
- **OE.3.1.15 Barandas y parapetos** (m2 **o** m): *"El cómputo … se obtendrá sumando las áreas parciales de los tramos. **Si las alturas se mantienen constantes puede efectuarse el cómputo en metros.**"* → caso de unidad dual, ver `unidades_alternativas`.
- **OE.3.7.1 Puertas / OE.3.7.2 Ventanas** (und): *"Para el cómputo debe contarse **la cantidad de piezas iguales en espesor de hojas, dimensiones y demás características**, que irán en partidas separadas."*
- **OE.3.8.8 Cortinas enrollables de fierro** (m2): *"…calculando la superficie del vano a cubrir multiplicando el ancho por la altura. Cuando se trata de puertas la altura es la distancia entre el **piso y el dintel**; y en el caso de ventanas entre el **alfeizar y el dintel**."*

### 4.5 Instalaciones

- **OE.4.2.1 Salida de agua fría** (**pto**): *"Se contará el número de puntos de salida."* Comprende tuberías, accesorios, espacios libres dejados en la albañilería y su posterior relleno con concreto.
- **OE.4.2 Sistema de agua fría** (nota general): *"Como norma general, **el metrado no incluye la conexión domiciliaria de agua**. En casos de excepción, se considera el número de conexiones y diámetro de cada una."*
- **OE.5.2.1 Salida** (und): *"Se medirá en base a la cantidad de unidades de salidas, pudiendo agruparse en subpartidas diferentes de acuerdo a sus tipos: salida para alumbrado, tomacorrientes, interruptores, dimers…"*
- **OE.5.1 Conexión a la red externa de medidores** (glb): *"El cómputo global significa que se pondrá una cifra total por la instalación del suministro eléctrico."*
- **OE.6.1 Cableado estructurado en interiores** (**pto**, "punto de red"): comprende todos los materiales y obras necesarias para la conexión de datos desde el ingreso del conductor en los conductos hasta su salida.
- **OE.6.4 Conductores de comunicaciones** (m): *"Se medirá la longitud total de conductores … agrupándose en partidas diferentes de acuerdo a sus tipos y características."*
- **OE.7.1 Tuberías (gas)** (m): *"El cómputo será midiendo la **longitud efectiva** de las tuberías a instalarse agrupándose en partidas independientes según su **diámetro, tipo, clase y tipo de montaje**."*

### 4.6 Seguridad y salud (OE.1.2) — todo global

La norma dedica OE.1.2 al **Plan de Seguridad y Salud en el Trabajo (PSST)** y mide casi todo en **Glb.**:

| Código | Partida | Unidad |
|---|---|---|
| OE.1.2.1.1 | Equipos de protección individual | **Und.** (de acuerdo al número de trabajadores) |
| OE.1.2.1.2 | Equipos de protección colectiva | Glb. |
| OE.1.2.1.3 | Señalización temporal de seguridad | Glb. |
| OE.1.2.1.4 | Capacitación en seguridad y salud | Glb. |
| OE.1.2.2 | Recursos para respuestas ante emergencias | Glb. |

Forma de medición común: *"Cumplir lo requerido en el Expediente Técnico de Obra … en conformidad con
el Plan de Seguridad y Salud en el Trabajo (PSST) y el planeamiento de obra."*

### 4.7 Habilitaciones urbanas (Título III)

- **HU.1** remite expresamente a OE.1: *"Comprende la partida OE.1 Obras Provisionales, Trabajos Preliminares, Seguridad y Salud, descrita en Metrados para Obras de Edificación."* Forma de medición: *"Varía de acuerdo al tamaño de la habilitación urbana"* — unidades admitidas: **m, m2, km, Glb.**
- **HU.2.1 Movimiento de tierra** (m3): *"Para el cálculo de volúmenes de terraplenes se usará el **método del promedio de áreas extremas**, en base a la determinación de las áreas en secciones transversales consecutivas, su promedio multiplicado por la longitud entre las secciones a lo largo de la línea del eje de la vía."*
- **HU.2.2 Sub-base y base** (m2): *"El área de la sub-base se obtiene multiplicando la longitud del tramo por el ancho de la vía, **indicando los espesores** de acuerdo al diseño."*
- **HU.3.1 Obras provisionales** remite igualmente al Título II (*"conforme a la descripción, unidad de medida y forma de medición indicado en el Capítulo II Obras en Edificación"*).
- **HU.3.4.3.1 Relleno y compactación para zanjas** (m): *"…midiendo la longitud de la zanja … **descontando las cámaras o buzones**. Se agruparán por rango de tuberías y profundidad."*
- **HU.3.6.3 / HU.3.7.4 Anclajes y dados de concreto** (und): típicos y repetitivos se cuentan por unidad; los que requieren tratamiento independiente se descomponen en concreto (m3) + encofrado (m2) + acero (kg).
- **HU.4.3 Redes aéreas** (m): *"…se tendrá que considerar el recorrido total indicado **más 10 m de cable en el interior de las subestaciones y más el 5 % del total para retaceo y desperdicios**."* — excepción explícita a la regla de "metrado neto".

---

## 5. El dataset generado

**Archivo:** `docs/investigacion/01-partidas-peru.json` — array JSON, 774 objetos, ~900 KB, UTF-8.

### Esquema

```json
{
  "codigo": "OE.2.3.9.2",
  "descripcion": "LOSAS ALIGERADAS CONVENCIONALES",
  "unidad": "m3",
  "especialidad": "OE.2 Estructuras",
  "regla_medicion": "El volumen de concreto de las losas aligeradas se obtendrá…",
  "fuente": "R.D. N° 073-2010-VIVIENDA/VMCS-DNC — Norma Técnica «Metrados…»",
  "url_fuente": "https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf",
  "nivel": 4,
  "partida_padre": "OE.2.3.9",
  "unidades_alternativas": ["m2"],
  "unidad_literal_norma": "Metro cúbico (m3)",
  "alcance": "…texto de la sección Descripción / Extensión de trabajo…",
  "origen_unidad": "propia",
  "origen_regla": "propia",
  "verificado": true
}
```

| Campo | Significado |
|---|---|
| `codigo` | Código jerárquico literal de la norma (`OE.x…` / `HU.x…`) |
| `descripcion` | Nombre de la partida tal como aparece en el índice oficial |
| `unidad` | Unidad normalizada: `m`, `m2`, `m3`, `kg`, `und`, `glb`, `pto`, `h`, `km` |
| `unidades_alternativas` | Cuando la norma admite dos (*"Metro cuadrado (m2) o Metro (m)"*) |
| `unidad_literal_norma` | Cadena literal del PDF, para auditar |
| `especialidad` | Capítulo (OE.1…OE.7, HU.1…HU.6) |
| `nivel` / `partida_padre` | Para reconstruir el árbol |
| `alcance` | Texto de "Descripción"/"Extensión de trabajo": qué comprende la partida |
| `regla_medicion` | Texto literal de "Forma de medición" |
| `origen_unidad` / `origen_regla` | **Trazabilidad**: `propia` \| `subpartidas` \| `heredada de <código>` \| `referencia expresa a <código>` \| `referencia cruzada en el texto de la partida` \| `no declarada en la norma` |
| `verificado` | `true` **solo si** la unidad y la regla se leyeron literalmente en el bloque de esa misma partida |

### Cifras

| Métrica | Valor |
|---|---|
| Partidas totales | **774** |
| Con unidad de medida | 744 (96 %) |
| Con regla de medición | 665 (86 %) |
| `verificado: true` (unidad **y** regla propias, literales) | **338** |
| Niveles | 1: 13 · 2: 87 · 3: 359 · 4: 248 · 5: 65 · 6: 2 |

Distribución por capítulo:

| Capítulo | Partidas |
|---|---|
| OE.3 Arquitectura | 192 |
| OE.2 Estructuras | 183 |
| HU.3 Infraestructura sanitaria | 148 |
| HU.2 Pistas y veredas | 47 |
| OE.1 Obras provisionales / seguridad y salud | 46 |
| OE.5 Instalaciones eléctricas y mecánicas | 41 |
| OE.4 Instalaciones sanitarias | 40 |
| HU.5 Infraestructura de comunicaciones | 20 |
| HU.4 Infraestructura eléctrica | 19 |
| OE.7 Instalaciones de gas | 14 |
| HU.6 Infraestructura de gas | 14 |
| OE.6 Instalaciones de comunicaciones | 9 |
| HU.1 Obras provisionales (HU) | 1 |

### Cómo se generó

1. Descarga del PDF oficial del SPIJ (154 pp., con capa de texto real).
2. Extracción de texto con **PyMuPDF** (`pymupdf`), página a página.
3. Parseo del **índice oficial** (Títulos II y III) → catálogo canónico de códigos y descripciones.
4. Parseo del **cuerpo**: para cada código se aísla su bloque (hasta el siguiente código) y su
   subárbol, y se extraen las etiquetas `Unidad de Medida` y `Forma de medición`.
5. Herencia controlada: las partidas enumeradas dentro de un grupo (p. ej. OE.3.1.1 a OE.3.1.14)
   heredan la unidad y la regla del grupo, **porque así lo dispone la norma** (una sola tabla de
   medición para toda la familia). Cada herencia queda marcada en `origen_*`.
6. Resolución de las remisiones explícitas del tipo *"Todo lo indicado en OE.3.2.2"*.
7. Filtro anti-falsos-positivos: el texto justificado del PDF parte frases y deja códigos sueltos a
   inicio de línea (p. ej. `OE.1` dentro de *"Comprende la partida OE.1 Obras Provisionales…"*);
   se descartan cuando la línea anterior no cierra oración.

El pipeline completo queda versionado y es re-ejecutable:

```
python docs/normas/_extraer_partidas.py     # lee el PDF y reescribe 01-partidas-peru.json
```

(requiere `pymupdf`; los rangos de línea del índice y del cuerpo están calibrados para ese PDF exacto
de 154 páginas — si se cambia el PDF hay que recalibrarlos).

---

## 6. Limitaciones y pendientes

1. **`verificado: false` en 436 registros.** No significa que estén mal: significa que la unidad o la
   regla se obtuvieron por herencia del grupo, por remisión, o que la norma no declara una regla
   propia para ese nivel. Usar `origen_unidad` / `origen_regla` para decidir cuánto confiar.
2. **30 registros sin unidad y 109 sin regla** — son en su casi totalidad **encabezados de capítulo o
   de grupo** (OE.2, OE.3, HU.3.5 Tuberías, HU.3.10 Estaciones de bombeo…) que la norma no mide
   directamente. No deben ofrecerse como partidas presupuestables.
3. **Fecha exacta de la R.D. y vigencia a 2026: no verificadas.** Contrastar con el portal del MVCS
   y/o el SPIJ antes de publicar el catálogo.
4. **Duplicidad de códigos en la propia norma.** El índice oficial repite `OE.3.2.22` (asignado a
   *"Preparación de descansos"* y a *"Gradas"*). Es un error del documento original; el dataset se
   quedó con una sola ocurrencia. Revisar si el motor necesita ambas.
5. **Errata `0,25 cm2` en OE.3.3.1** (debe leerse 0,25 m2), conservada literal en el JSON.
6. **Tablas del PDF sin estructura.** Algunas tablas (p. ej. factores de esponjamiento, cuadros
   `Descripción | Unidad de medida`) quedan aplanadas dentro de `regla_medicion`. Para el motor
   conviene extraerlas como datos aparte.
7. **`p2` y `pza` no existen en esta norma.** Si el catálogo de la app las necesita, deben venir de
   otra fuente y marcarse como tal.
8. **OE.7 (gas) y HU.6 (gas)** están en la norma pero el encargo no los pedía; se incluyeron igual
   porque completan el árbol.

---

## 7. Fuentes

- **Fuente primaria usada:** SPIJ – MINJUS, *Norma Técnica Metrados para Obras de Edificación y
  Habilitaciones Urbanas* — <https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf>
- **Espejo de respaldo (escaneado):** <https://waltervillavicencio.com/wp-content/uploads/2021/09/RD-073-2010-VIVIENDA-VMCS-DNC-Norma-Tecnica-Metrados-para-Obras-de-Edificacion-y-Habilitaciones-Urbanas.pdf>
- Copias locales en `C:\Users\ingvi\Proyectos\metra-ai\docs\normas\`.
