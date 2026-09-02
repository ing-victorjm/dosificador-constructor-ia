# 04 — Normas de medición, unidades, monedas e impuestos por país

> Investigación para parametrizar el motor de metrados de **metra-ai** sin asumir una normativa única.
> Fecha: 2026-09-02. Todas las fuentes son documentos públicos. Las normas de pago (NCh353, ASTM E1557,
> MasterFormat, BEDEC, CESMM4) **no se descargaron**: su alcance se documenta desde fuentes públicas y así se indica.

---

## 0. Conclusión de arquitectura (lo que hay que construir)

La investigación confirma que **no existe un criterio de medición universal**. Ni siquiera dentro de un mismo
país: en México la cimbra es partida separada en edificación pero va incluida en el m³ de concreto en carreteras;
en Perú el umbral de descuento de vanos vale 0 m², 0,25 m², 0,50 m² o 1,00 m² según la familia de partida.

Por tanto el motor **no puede tener constantes de país**. Necesita:

1. **Un perfil de país** que fije *defaults* (moneda, formato numérico, sistema de unidades, impuesto, catálogo de unidades).
2. **Un perfil de reglas de medición por familia de partida**, no por país. La regla vive en la partida
   (`descuento_vanos_modo`, `umbral_m2`, `encofrado_separado`, …), y el país sólo la *precarga*.
3. **Un campo de "criterio de medición" editable y trazable por partida.** Bolivia, Ecuador, Argentina y México
   obligan por norma a que el proyectista declare la "Medición / Forma de pago" de cada ítem. España (CYPE)
   distingue además **criterio en proyecto** y **criterio en obra y condiciones de abono**: son dos números
   distintos para la misma partida y el motor debería poder guardar ambos.
4. **Separar el metrado del precio.** Todas las normas verificadas coinciden en una cosa: **el metrado es neto**
   y el desperdicio, las mermas, los despuntes y el esponjamiento **van en el análisis de precio unitario**, nunca
   sumados a la cantidad. Es el único invariante transnacional que encontré.

**Tres estructuras de presupuesto irreconciliables** que el motor debe soportar:

| Modelo | Países | Cómo se arma |
|---|---|---|
| **Impuesto al final** | Perú, México, Chile, Argentina, Colombia (parcial) | Costo directo → GG → utilidad → **+ IGV/IVA** |
| **Impuesto dentro del precio unitario** | **Bolivia** | El APU ya incorpora IVA 14,94 % sobre mano de obra e IT 3,09 %; **no se añade línea de impuesto al final** |
| **Mayoración reglada + IVA sobre base parcial** | **España** | PEM → +GG 13–17 % → +BI 6 % → **IVA 21 % sobre (PEM + GG)**, no sobre el BI según art. 131 |

Y dos casos que rompen el modelo "tasa única":
- **Colombia:** en contratos de construcción de inmueble el IVA se causa **sobre honorarios o utilidad del constructor**, no sobre el valor total.
- **EE. UU.:** no hay IVA. Hay *sales & use tax* estatal y local, con reglas distintas por estado según sea contrato *lump-sum* o *separated* y según sea *capital improvement* o *repair*. No es parametrizable con una tasa nacional.

---

## 1. Tabla comparativa

### 1.1 Norma de medición y codificación

| País | ¿Hay norma nacional de medición? | Norma / estándar vigente | Codificación de partidas |
|---|---|---|---|
| **Perú** | **Sí** | Norma Técnica *Metrados para Obras de Edificación y Habilitaciones Urbanas*, RD 073-2010/VIVIENDA/VMCS-DNC (2010) | `OE.1`–`OE.7` (edificación) y `HU.1`–`HU.6` (hab. urbanas), hasta 5 segmentos (`OE.3.4.2.21`). La norma define 4 órdenes de partida: título / subtítulo / específica / excepcional. En presupuesto (S10) se implementa como `01.01.01` |
| **Colombia** | **No** (NSR-10 es diseño) | INVÍAS *Especificaciones Generales de Construcción de Carreteras 2022* (Res. 4561/2022); IDU **ET-IC-01 v4.0** (Res. 010910/2019); Documentos Tipo de CCE v4 (Res. 465/2024) | INVÍAS: artículo de 3 dígitos + sufijo de año (`201-22`, `220-22`). IDU: 3–4 dígitos + `-18` (`800-18`, `1200-18`), 12 capítulos. Presupuesto: `CAP 1.0` → `ITEM 1.01` |
| **Chile** | **Sí** | **NCh353:2018** *Construcción — Cubicación de obras de edificación — Metodología de cálculo — Requisitos* (INN, 26-12-2018). Complementan: OGUC DS 47/1992 (superficies) y MINVU Itemizado Técnico DS49 (Res. Ex. 7713/2017) | MOP Manual de Carreteras V5: `5.514.4` → ítem de pago `514-1`. MINVU: 9 capítulos decimales (`2.4 Muros de albañilería confinada`) |
| **México** | **No** | LOPSRM (reformada DOF 16-04-2025) + RLOPSRM art. 185/188; **SICT** Normativa para la Infraestructura del Transporte; **CONAGUA** Catálogo General 2025; **CDMX** Libro 3 de Normas de Construcción | SICT: `N-CTR-CAR-1-02-006/01` (tipo-libro-tema-parte-título-capítulo/año). CDMX: `3.01.02.007` (libro.parte.sección.capítulo). CONAGUA: familia 4 dígitos + variante 2 (`4080 01`) |
| **Ecuador** | **No** para edificación; **sí** en vialidad | **NEVI-12 (MTOP, 2013)**, Vol. 3 *Especificaciones Generales para la Construcción de Caminos y Puentes*; LOSNCP (2008, reformada 07-10-2025). La **NEC no contiene** capítulo de medición | Vialidad: decimal jerárquica (`6.103.6.3 (1)`). Edificación: correlativa plana (`No. | Rubro | Unidad | Cantidad`) |
| **Bolivia** | **No** (reconocido oficialmente) | *Guía Boliviana para Diseño y Presentación de Proyectos* (MOPSV, 2017); *Modelo DBC de Obras* (MEFP, RM 021 de 02-02-2022) bajo DS 0181 (NB-SABS) | Correlativa plana (`1, 2, 3…`). La Guía normaliza 8 rubros: preliminares, cimentación y estructura, obra gruesa, obra fina, eléctricas, hidrosanitarias, complementarias, trabajos finales |
| **Argentina** | **No** encontrada | Pliegos DNV; **PUETG DVBA 2019** (Vialidad Prov. Buenos Aires, 512 pp.); INDEC *ICC* base 1993=100 | Pliegos: `CAPÍTULO → SECCIÓN → ART.`, último artículo = *Forma de medición y pago*. Edificación: `1 / 1.1 / 2.1.1` (rubro→ítem→subítem) |
| **España** | **No** como norma; sí **criterios publicados por partida** | CTE (RD 314/2006) y Código Estructural (RD 470/2021) son de **diseño**. Los criterios de medición están en las **bases de precios**: **BEDEC** (ITeC) y **Generador de precios CYPE**. Estructura del presupuesto: **RD 1098/2001 arts. 130–131** + Ley 9/2017 art. 100 | BEDEC: 9 caracteres `P/B/C/A + cap + subcap + familia + '-' + 4 dif.` (`P129-6553`, `A04-FEPZ`). CYPE: letra + 2 letras + 3 letras + 3 dígitos (`FFX010`, `EHS012`, `RPE005`) |
| **EE. UU.** | **No** | Ninguna norma obligatoria. Taxonomías: **CSI MasterFormat 2026** (50 divisiones 00-49, 6 dígitos en 3 pares); **UniFormat / ASTM E1557-09(2020)e1** (A–G + Z, `A10`, `A1010`); **ASPE Standard Estimating Practice** 12ª ed. | MasterFormat `06 10 00`; UniFormat `A1010` |
| **Internacional** | Sí, opcionales | **ICMS 3** (ICMS Coalition/RICS, 01-06-2022, **gratuito**); **RICS NRM 2** (2012, ef. 2013; reeditada oct-2021 y oct-2022); **POMI** (RICS/BCIS 1979, **archivado**); **SMM7** (sustituida por NRM2 el 01-07-2013); **CESMM4 Revised** (ICE, 2019) | ICMS: `C.GG.SSS` (`2.03.030`). NRM2: código elemental de 6 niveles + sufijo de work section (`DPB27-3.1.1.2.1.4/04`); 41 work sections |

### 1.2 Moneda, unidades e impuesto

| País | ISO | Símbolo | Dec. | Sep. decimal | Sep. miles | Sistema | Unidades típicas | Impuesto sobre obra |
|---|---|---|---|---|---|---|---|---|
| Perú | PEN | `S/` | 2 | `.` | `,` | métrico | m2, m3, kg, m, Und., Glb. | **IGV 18 %**, grava expresamente los contratos de construcción. Se suma al final |
| Colombia | COP | `$` | **0** | `,` | `.` | métrico | M2, M3, kg, ML, UN/UND, GLB/GL | **IVA 19 %** general, **pero** en contratos de construcción de inmueble se causa **sobre honorarios o utilidad** del constructor. AIU (22/3/5 típico) es mayoración del directo |
| Chile | CLP | `$` | **0** | `,` | `.` | métrico | m2, m3, kg, ml, N°, gl | **IVA 19 %** (art. 14 LIVS). CEEC (DL 910 art. 21) en extinción: 0,1625 del débito para contratos 2025-2026, **eliminado el 01-01-2027** |
| México | MXN | `$` | 2 | `.` | `,` | métrico | m2, m3, kg, t, m, **pza**, jgo, lote, pda, salida | **IVA 16 %**; **8 % efectivo** en región fronteriza norte/sur (estímulo, requiere padrón) |
| Ecuador | USD | `$` | 2 | `.` ⚠ | `,` ⚠ | métrico | m2, m3, kg, m (u/glb no verificados) | **IVA 15 %** (DE 198, desde 01-04-2024). **Tarifa 5 % para construcción**, alcance por confirmar. El presupuesto referencial SERCOP se expresa **SIN IVA** |
| Bolivia | BOB | `Bs` | 2 | `,` | `.` | métrico (SI obligatorio) | m, m2, m3, kg (catálogo **abierto**, texto libre en el DBC) | **IVA 13 % + IT 3 %, "por dentro"**: 14,94 % s/ mano de obra y 3,09 % sobre el subtotal, **dentro del APU**. No se añade línea al final |
| Argentina | ARS | `$` | 2 | `,` | `.` | métrico | m2, m3, ml/m, Un/u, Gl, mes, kg | **IVA 21 %**; **10,5 %** para obras sobre inmueble ajeno o propio **destinadas a vivienda** (art. 28 inc. c, Ley IVA t.o. Dec. 280/97) |
| España | EUR | `€` | 2 | `,` | `.` | métrico | m², m³, m, kg, t, **Ud** (CYPE) / **u** (BEDEC), **PA** (partida alzada) | **IVA 21 %**; **10 %** en renovación de vivienda y en obra promotor↔contratista de vivienda; **4 % sólo la entrega de VPO** (no la obra). Inversión del sujeto pasivo en obra (art. 84.Uno.2º.f). Canarias: **IGIC** |
| EE. UU. | USD | `$` | 2 | `.` | `,` | **imperial** | SF, SY, CY, CF, LF, EA, TON, LB, GAL, LS | **No hay IVA.** *Sales & use tax* estatal/local, variable por estado y por tipo de contrato |
| Internacional | — | — | — | — | — | métrico (NRM2/ICMS) | m, m2, m3, kg, t, nr, item | ICMS obliga a declarar **moneda local + base date + tipo de cambio**; no fija impuesto |

---

## 2. Diferencias prácticas de medición (lo que el motor debe parametrizar)

### 2.1 Descuento de vanos — es el parámetro con más dispersión

Hacen falta **cuatro modos**, no un solo umbral:

| Modo | Significado | Dónde aparece |
|---|---|---|
| `deducir_todo` | Se descuenta cualquier hueco, sin umbral | **Perú**, muros de albañilería y tarrajeos |
| `umbral` | No se deduce por debajo de X m²; por encima se deduce completo | **España** fábrica (X = 2 m²); **NRM2** albañilería (0,50 m²), encofrado (5,00 m²), cubiertas y malla (1,00 m²); **Perú** pisos (0,25 m²), recubrimientos (0,50 m²), coberturas (1,00 m²) |
| `deducir_exceso` | Se deduce **sólo lo que excede** de X m² | **España** revestimientos (X = 4 m²) |
| `no_deducir` | "Vacío por lleno": no se descuenta nada | **Colombia** (revoque/pañete) |

Textos literales verificados:

- **Perú**, muros (OE.3.1): *"Las áreas son netas, por lo tanto, se descontarán en la medición las áreas de los vanos de puertas, ventanas, mamparas y algunos otros vacíos si los hubiera."*
- **Perú**, revoques (OE.3.2.1): *"Se computarán todas las áreas netas a vestir o revocar. Por consiguiente se descontarán los vanos o aberturas…"*
- **Perú**, recubrimientos (OE.3.6): *"Se medirá el área neta ejecutada sin descontar luces o huecos de áreas menores de 0,50 m2."*
- **Perú**, pisos (OE.3.4): *"En todos los casos no se descontarán las áreas de columnas, huecos, rejillas, etc., inferiores a 0,25 m2."*
- **Perú**, cielorrasos (OE.3.3): *"no se deducirán las áreas de columnas, ni huecos menores de 0,25 cm2"* — **errata evidente de la norma** (debe leerse m²). Parametrizar, no copiar.
- **España** (CYPE `FFX010`): *"deduciendo los huecos de superficie mayor de 2 m². En los huecos que no se deduzcan, están incluidos los trabajos de realizar la superficie interior del hueco."*
- **España** (CYPE `RPE005`): *"sin deducir huecos menores de 4 m² y deduciendo, en los huecos de superficie mayor de 4 m², el exceso sobre 4 m²."*
- **Colombia** (ICBF, especificación de pañete): *"No se medirán y por tanto no se pagarán las aberturas y/o vanos para puertas y ventanas."*
- **NRM2** 3.3.2(2): *"Unless otherwise stated, minimum deductions for voids refer only to openings or wants within the boundaries of the measured work."* / *"Always deduct openings or wants at the boundaries of measured areas, irrespective of size."*
- **NRM2** sección 14 (Masonry): *"No deductions will be made for voids or built in items whose cross sectional area is equal to or less than 0.50m2."*
- **NRM2** sección 11 (Formwork): *"No deductions shall be made for voids ≤ 5.00m2."*

**Sin regla publicada:** México, Bolivia, Ecuador, Argentina. En Chile la tabla que circula (0 % < 1,5 m²; 25 % entre 1,5 y 3,0; 75 % > 3,0) **no se pudo verificar** en NCh353:2018 (norma de pago, no descargada) — **no usarla como default duro**.

**Consecuencia de diseño:** cuando el modo es `deducir_todo` (Perú), el presupuesto necesita partidas compensatorias.
La propia norma peruana las tiene: *"Vestidura de derrames"* medida en **metros lineales**, y en zócalos
*"se tomará el área realmente ejecutada… **agregando el área de derrames**"*. El motor debe poder generar el
derrame automáticamente a partir del perímetro del vano × espesor del muro.

### 2.2 Muros: eje o cara

Ningún país normó literalmente "eje vs cara" para cubicación de partidas. Lo que sí está publicado:

- **Perú:** altura de muros y placas *"de la cara superior del entrepiso inferior a la cara inferior del entrepiso superior"*; pisos *"entre los muros **sin revestir**"*; y una regla de intersección que sustituye al eje: *"En tramos que se cruzan se medirá la intersección una sola vez."*
- **Chile (OGUC art. 1.1.2):** *superficie edificada* se mide **hasta la cara exterior** de los muros perimetrales; *superficie útil* y *superficie común*, **hasta el eje** de los muros. Son definiciones de arquitectura, no de cubicación de partidas, pero fijan el vocabulario chileno.
- **España (CYPE FFX010):** *"Superficie medida en verdadera magnitud **desde las caras exteriores de la fachada**."*
- **Colombia (ICBF):** el replanteo se hace sobre **ejes estructurales** y *"no se contabilizarán sobreanchos adicionales"*.
- **NRM2** sección 14: *"All wall dimensions exclude applied finishes"*; espesor de muros cónicos = espesor medio; radio de curvas tomado del eje.
- **México, Bolivia, Ecuador, Argentina:** sin regla publicada.

### 2.3 Encofrado / cimbra / moldaje / formaleta — **no hay consenso**

| País | ¿Partida separada? | Unidad y criterio |
|---|---|---|
| **Perú** | **Sí, siempre.** Cada elemento de concreto armado se abre en 3 sub-partidas: `.1 concreto (m3)`, `.2 encofrado y desencofrado (m2)`, `.3 armadura (kg)` | *"el área efectiva se obtendrá midiendo el desarrollo de la superficie del molde o encofrado en contacto con el concreto, **con excepción de losas aligeradas**, donde se medirá el área total de la losa, que incluye la superficie del ladrillo hueco"*. "Cara vista" se computa aparte |
| **México** | **Depende del sector.** Edificación y obra hidráulica: **sí** (CDMX Libro 3 cap. 007; CONAGUA familia `4080`). Carreteras: **no** — la norma SICT N-CTR-CAR-1-02-003/04 incluye en la base de pago *"Suministro, colocación, preparación y remoción de cimbras"* | CDMX: *"se medirá la superficie de contacto de la cimbra con el concreto fresco"*, m² con 2 decimales |
| **Colombia** | **No** — va incluida en el APU del concreto. Verificado: en "Columnas en concreto a la vista" (unidad m³) la formaleta aparece en los numerales *Equipo* y *Materiales* | m³ de concreto "todo incluido" |
| **España** | **Ambas.** CYPE publica `EHS010` (pilar en m³ con encofrado incluido) **y** `EHS012` (sistema de encofrado en m²) | m²: *"superficie de encofrado en contacto con el hormigón"* |
| **Internacional (NRM2)** | **Sí**, sección 11 ítems 13–19 | m² (y m para anchos ≤ 500 mm); sin deducir huecos ≤ 5,00 m² |
| **EE. UU.** | Sí, por práctica | **SFCA** = *square feet of contact area* |
| **Chile / Bolivia / Ecuador / Argentina** | **No verificado / no normado** | — |

### 2.4 Acero: el metrado **nunca** incluye desperdicio

Éste es el punto de mayor coincidencia internacional. En **todas** las fuentes verificadas el acero se mide a
**peso teórico de planos** y las mermas van al precio:

- **Perú:** *"El cómputo de la armadura de acero **no incluye los sobrantes de las barras (desperdicios)**, alambres, espaciadores, accesorios de apoyo ni desperdicios, los mismos que irán como parte integrante de los análisis de precios."* **Sí incluye** *"los ganchos, dobleces y traslapes de varillas"*. Excluye vástagos y arranques de columnas en zapatas.
- **Perú, regla general:** *"Como aplicación general, el cómputo de metrado de las partidas será neto, sin tener en cuenta el volumen de esponjamiento… ni desperdicios…, los mismos que irán como parte integrante del Análisis de Precios."*
- **México (SICT N-CTR-CAR-1-02-004/02):** unidad *"kilogramo de acero habilitado y colocado"* con aproximación a 0,1; la masa se calcula **de las dimensiones de planos**; la base de pago incluye *"Valor de adquisición o fabricación, **incluyendo mermas y desperdicios**"*.
- **México (CDMX Libro 3 cap. 011):** unidad **tonelada** con 2 decimales; *"se tomará como base el peso que se obtenga del cálculo en planos"*; el precio incluye *"traslapes, ganchos… retiro de desperdicios"*.
- **Colombia:** *"Se medirá y se pagará por kilogramos (kg) de acero de refuerzo debidamente colocados… La medida se efectuará sobre los Planos Estructurales y los pesos se determinarán de acuerdo con la norma NSR."* Las especificaciones tienen un numeral explícito *"10. DESPERDICIOS — Incluidos Sí/No"*.
- **España (CYPE `EAS010`):** en proyecto, *"**Peso nominal** medido según documentación gráfica"*; en obra, peso de báscula; y *"El precio incluye las soldaduras, **los cortes, los despuntes**…"*.
- **Chile (NCh353:2018):** el alcance excluye *"el sobredimensionamiento, ni el rechazo de materiales"* e impulsa considerar *"las pérdidas mínimas posibles de los materiales"*.
- **NRM2** 3.3.2(1)(b): *"Net quantity measured shall be deemed to include all additional material required for laps, joints, seams and the like, as well as any waste material."* Barras en toneladas; *"Forming hooks, tying wire, spacers, cutting, and bending is deemed included"*.

**Ningún país publica un porcentaje de desperdicio.** El 3–5 % habitual es práctica de APU, no norma.
El motor debe pedirlo, no asumirlo — por eso `desperdicio_acero_pct` va en `null` en el JSON.

### 2.5 Esponjamiento y movimiento de tierras

- **Perú:** corte y excavación se miden en **volumen natural (banco)**. Pero la **eliminación de material excedente sí se afecta por esponjamiento**, con **tabla de factores normada**: roca dura volada 1,50–2,00 · roca mediana 1,40–1,80 · roca blanda 1,25–1,40 · grava compacta 1,35 · grava suelta 1,10 · arena compacta 1,25–1,35 · arena mediana dura 1,15–1,25 · arena blanda 1,05–1,15 · limos recién depositados 1,10–1,40 · arcillas muy duras 1,15–1,25. Además obliga a **clasificar las excavaciones por profundidad**.
- **Ecuador (NEVI-12 Vol. 6):** *"se cuantificará por metro cúbico (m3) excavado determinado con **secciones geométricas de perfiles normales al eje del camino**"* → volumen en banco.
- **Argentina (PUETG DVBA 2019):** terraplén *"en metros cúbicos (m³) de terraplén debidamente construido… con las exigencias de compactación"* → **volumen compactado en obra**, criterio opuesto al de banco. Zanja: m³ de suelo excavado. Apertura de caja: **m² de superficie ejecutada**.
- **NRM2** sección 5: *"The quantities given for excavation and filling are the bulk before excavating or the net void to be filled. **No allowance is made for subsequent variations to bulk** or for the extra space taken up by working space or earthwork support."*

**Consecuencia:** el motor necesita, por partida de movimiento de tierras, un campo `estado_del_volumen`
(`banco` | `suelto` | `compactado`) y un factor de conversión. Asumir "banco" para todos rompe Argentina.

### 2.6 Redondeo y aproximación — está normado, y difiere

- **NRM2:** dimensiones al múltiplo de 10 mm más cercano (≥5 mm sube); cantidades a entero **salvo toneladas, a 2 decimales**.
- **México (SICT N-LEG-3/24 cl. E.6):** redondeo a la unidad o decimal superior cuando la fracción es ≥ 0,5 / 0,05 / 0,005. Concreto y acero de carreteras con aproximación a **0,1**; cimbra y acero de CDMX con **2 decimales**.
- **Bolivia:** el APU trabaja a 3 decimales y el precio unitario final se adopta *"con dos (2) decimales"*. Además los importes van **en numeral y en literal**, y *"Cuando exista discrepancia… prevalecerá el literal"* — el exportador boliviano debe emitir el monto en letras.
- **Colombia:** *"PRECIO UNITARIO APROXIMADO AL PESO"* (0 decimales).

Esto encaja con `backend/motor/redondeo.py`: el modo y los decimales ya son configurables por proyecto; sólo
falta que el **perfil de país** los precargue y que el redondeo de cantidades sea distinto del de importes.

---

## 3. Fichas por país

### 3.1 Perú 🇵🇪 — el único con norma de metrados detallada y obligatoria

**Norma:** *Norma Técnica: Metrados para Obras de Edificación y Habilitaciones Urbanas*, aprobada por
**RD N° 073-2010/VIVIENDA/VMCS-DNC** (Ministerio de Vivienda, Construcción y Saneamiento — Dirección Nacional de
Construcción, 2010).
<https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf>
Aplicación (texto literal, cap. 3): *"es de aplicación obligatoria en la elaboración de los Expedientes Técnicos
para Obras de Edificación y para Habilitaciones Urbanas en todo el territorio nacional."*
⚠ La propia portada advierte que **no fue publicada en El Peruano**.

**Complementan:** RNE (DS 011-2006-VIVIENDA) — diseño, no medición; **Ley 32069 de Contrataciones Públicas**
(24-06-2024) y su Reglamento **DS 009-2025-EF**, vigentes desde el **22-04-2025** (OSCE → **OECE**), que exigen
expediente técnico con estructura de costos y **metodología BIM**
(<https://leyes.congreso.gob.pe/Documentos/2021_2026/ADLP/Texto_Consolidado/32069-TXM.pdf>); y para vialidad el
**Manual de Carreteras EG-2013** (RD 22-2013-MTC/14), con "Medición" y "Pago" por sección
(<https://portal.mtc.gob.pe/transportes/caminos/normas_carreteras/manuales.html>).
**No existe** un manual de metrados viales específico.

**Impuesto:** IGV **18 %**, que grava expresamente *"Los contratos de construcción"* y *"La primera venta de
inmuebles que realicen los constructores"* (<https://orientacion.sunat.gob.pe/3053-concepto-tasa-y-operaciones-gravadas-igv-empresas>).
El 18 % se descompone internamente en IGV + IPM; la proporción la fija SUNAT y ha sido modificada — el total
es lo relevante para el motor.

**Detalle propio a parametrizar:** derrames en ml; encofrado de losa aligerada medido como losa maciza
(incluye el área del ladrillo); ladrillos de techo por unidad o millar; pintura de puertas y ventanas **por las
dos caras**; el tarrajeo exterior se separa del interior porque *"requiere de un andamiaje apropiado"*.

### 3.2 Colombia 🇨🇴

**NSR-10** (Decreto 926 de 19-03-2010) es **reglamento de diseño sismo resistente, no de medición**
(<https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=39255>). Se cita en los pliegos sólo para
determinar pesos de acero.

Las reglas de "medida y forma de pago" viven en las especificaciones de cada entidad:
**INVÍAS 2022** (Res. 4561 de 29-11-2022, <https://www.invias.gov.co/index.php/archivo-y-documentos/documentos-tecnicos/12865-especificaciones-generales-de-construccion-de-carreteras-2022>),
**IDU ET-IC-01 v4.0** (Res. 010910 de 27-12-2019, <https://www.idu.gov.co/page/especificaciones-tecnicas-generales-de-materiales>),
**ICBF** (<https://www.icbf.gov.co/sites/default/files/anexo_no.2_-_especificaciones_tecnicas_de_obra.pdf>, la
fuente que sí pude leer íntegra) y los **Documentos Tipo de Colombia Compra Eficiente v4** (Res. 465 de 2024,
<https://www.colombiacompra.gov.co/archivos/tema/obra-publica>). El formato de especificación por ítem del ICBF
tiene 15 numerales, entre ellos *"10. DESPERDICIOS (Incluidos Sí/No)"* y *"13/15. MEDIDA Y FORMA DE PAGO"*.

**Impuesto — corregir un error extendido.** El IVA general es 19 % (ET art. 468, modificado por art. 184 Ley
1819 de 2016). En **contratos de construcción de bien inmueble** el IVA se genera *"sobre la parte de los
ingresos correspondiente a los honorarios obtenidos por el constructor"* (Decreto 1372 de 1992 art. 3, compilado
en DUR 1625 de 2016 art. 1.3.1.7.9). **Pero eso no es la base gravable AIU del art. 462-1 ET**: la DIAN excluye
expresamente la construcción de ese régimen (Oficio 901006 (165) de 2021,
<https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_901006_2021.htm>). Hay que modelar dos cosas
distintas: (a) el **AIU como factor de mayoración** del costo directo — el APU oficial del DNP usa A 22 % / I 3 % /
U 5 % (<https://documentossoportewcf.dnp.gov.co/DocumentosSoportes/Territorial/Tramites/2__ANALISIS_DE_PRECIOS_UNITARIOS_20230713_1005.PDF>);
y (b) la **base gravable del IVA en construcción** = honorarios o utilidad.

### 3.3 Chile 🇨🇱

**NCh353:2018** *"Construcción — Cubicación de obras de edificación — Metodología de cálculo — Requisitos"* (INN,
aprobada 26-12-2018, 45 pp., reemplaza NCh353.Of2000) es **la** norma chilena de medición.
<https://ecommerce.inn.cl/nch353201870066> — **es norma de pago; no se descargó**. De su ficha pública se verifica
el alcance: establece *"procedimientos y metodologías para cubicar y determinar cantidades referidas a las
diferentes partidas que constituyen una obra de edificación"*, y **excluye** *"el sobredimensionamiento, ni el
rechazo de materiales"*, considerando *"las pérdidas mínimas posibles de los materiales"*.

**OGUC** (DS 47 de 1992, texto actualizado a marzo 2026) **no contiene reglas de cubicación**, pero sí las
definiciones de superficie citadas en §2.2
(<https://www.minvu.gob.cl/wp-content/uploads/2019/05/OGUC-Marzo-2026-D.S.-N%C2%B02-D.O.-16-03-2026.pdf>).
El **Itemizado Técnico DS49 del MINVU** (Res. Ex. 7713 de 16-06-2017,
<https://www.minvu.gob.cl/wp-content/uploads/2019/05/Res_7713-16062017_Itemizado-Tecnico.pdf>) es un itemizado de
**exigencias técnicas mínimas obligatorias**, no una tabla de unidades de pago. El **Manual de Carreteras MOP
Vol. 5** tiene en cada sección el numeral `.4 PARTIDAS DEL PRESUPUESTO Y BASES DE MEDICIÓN` con su código de ítem
de pago (<https://vialidad.mop.gob.cl/2026/01/29/vialidad-publico-nueva-edicion-del-manual-de-carreteras/>).

**UF:** el motor debe soportarla como unidad de cuenta paralela al CLP. El SII la publica diariamente con
**2 decimales, punto de miles y coma decimal** (ej. `40.875,09` al 01-09-2026): <https://www.sii.cl/valores_y_fechas/uf/uf2026.htm>.
Los topes de subsidio y del crédito de constructoras están fijados **en UF** (2.000 / 2.200 UF, tope 225 UF por vivienda).

**CEEC (DL 910 art. 21):** no cambia el IVA facturado (19 %); es un crédito del constructor contra PPM.
Para contratos generales de construcción celebrados entre el **01-01-2025 y el 31-12-2026** la deducción es
**0,1625** del débito fiscal (0,030875 del valor del contrato en viviendas exentas por subsidio ≤ 2.200 UF), y
**se elimina el 01-01-2027**. Circular SII N° 37 de 2023: <https://www.sii.cl/normativa_legislacion/circulares/2023/circu37.pdf>

### 3.4 México 🇲🇽

**La LOPSRM no fue sustituida: fue reformada** por decreto publicado en el **DOF del 16-04-2025**
(<https://sidof.segob.gob.mx/notas/5755218>), que entra en vigor al día siguiente salvo lo que dependa de la nueva
**Plataforma Digital de Contrataciones Públicas** (hasta entonces sigue **CompraNet**). El art. 45 fr. I define el
contrato a precios unitarios y el art. 59 exige conciliar los conceptos fuera de catálogo.

El **RLOPSRM art. 185** integra el precio unitario con *"costos directos… costos indirectos, el costo por
financiamiento, el cargo por la utilidad del contratista y los cargos adicionales"*, y el **art. 188** obliga a que
*"Las unidades de medida de los conceptos de trabajo corresponderán al Sistema General de Unidades de Medida"*
(NOM-008-SE-2021, DOF 29-12-2023).

Las reglas de medición y base de pago están en normas sectoriales:
**SICT** (<https://normas.imt.mx/libros>) — cada norma CTR tiene cláusulas `I. MEDICIÓN` y `J. BASE DE PAGO`, y la
**N-LEG-3/24** fija las reglas generales, incluida la clave para el motor: *"La medición de los conceptos de obra
se realizará en la forma, unidades y aproximación que establezcan **las especificaciones particulares**"*
(<https://normas.imt.mx/storage/normativa/N-LEG-3-24.pdf>).
**CONAGUA**, Catálogo General de Precios Unitarios 2025
(<https://www.gob.mx/cms/uploads/attachment/file/985551/CATALOGO_GENERAL_DE_AGUA_POTABLE_DE_PRECIOS_UNITARIOS_PARA_LA_CONSTRUCCI_N_DE_SISTEMAS_DE_AGUA_POTABLE_Y_ALCANTARILLADO_2025.pdf>).
**CDMX**, Libro 3 de las Normas de Construcción, con el apartado *"F. SUBCONCEPTOS DE OBRA, ALCANCES, UNIDADES DE
MEDIDA, CRITERIOS PARA CUANTIFICAR Y BASE DE PAGO"* por capítulo
(<https://infocdmx.org.mx/escuela/curso_capacitadores/procesos_contratacion/normas_tecnicas_VII.pdf>).

**Unidades:** confirmado que la unidad de conteo es **`pza`**, no `und` (tabla 7 de N-INT-4/26,
<https://normas.imt.mx/storage/normativa/N-INT-4-26.pdf>), junto con `jgo`, `lote`, `pda`, `conj`, `sist`, `elem`,
y `salida` en instalaciones.

**IVA:** 16 % general. El **8 % de la región fronteriza** norte y sur es un **estímulo fiscal** (no una tasa), que
exige inscripción en el padrón del SAT y excluye expresamente la **enajenación de bienes inmuebles** — la
ejecución de obra como servicio no está en la lista de exclusiones.
<https://www.sat.gob.mx/minisitio/EstimulosFiscalesFronteraNorteSur/documentos/PreguntasFrecuentes.pdf>

**No encontré ninguna norma mexicana pública que fije umbral de deducción de vanos ni criterio eje/cara.**
Búsqueda explícita en el Libro 3 Tomo II de CDMX: cero coincidencias. Se define por especificación particular.

### 3.5 Ecuador 🇪🇨

La **NEC** (rectoría del Ministerio de Infraestructura y Transporte desde el DE 102 de 15-08-2025,
<https://www.mit.gob.ec/norma-ecuatoriana-de-la-construccion/>) **no contiene** ningún capítulo de medición de
cantidades. Verificado eje por eje (NEC-SE, NEC-HS, NEC-SB).

Lo que sí normaliza medición es **NEVI-12 (MTOP, 2013)**: cada operación cierra con *"Partidas del Presupuesto y
Bases de Medición"*. Ejemplo literal del Vol. 6: *"La operación se cuantificará por metro cúbico (m3) excavado
determinado con secciones geométricas de perfiles normales al eje del camino."*
<https://www.mit.gob.ec/wp-content/uploads/downloads/2013/12/01-12-2013_Manual_NEVI-12_VOLUMEN_6.pdf>
(El Vol. 3, el de edificación de caminos y puentes, supera el límite de descarga y quedó sin leer:
<https://www.mit.gob.ec/wp-content/uploads/downloads/2013/12/01-12-2013_Manual_NEVI-12_VOLUMEN_3.pdf>)

La **LOSNCP** (RO 395 de 04-08-2008, reformada el **07-10-2025**) exige APU y presupuesto referencial (art. 23) y
regula el reajuste con índices **IPCO del INEC** (arts. 96–97; antes 82–83). El SERCOP **no emite** norma de
medición: obliga a la entidad contratante a definir la *"forma de pago"* rubro por rubro.

⚠ **Punto abierto de alto impacto:** el SRI publica la tarifa general de **15 %** desde el 01-04-2024 (DE 198) y a
la vez una **tarifa reducida del 5 % para "Construcción"** (Ley Orgánica para Enfrentar el Conflicto Armado
Interno, RO 516). En el propio portal el 5 % se precisa como *"la transferencia de materiales de construcción"*.
**No pude confirmar si cubre también los contratos/servicios de construcción.** Es la diferencia entre 5 % y 15 %
sobre todo el presupuesto ecuatoriano: resolver antes de codificar. <https://www.sri.gob.ec/impuesto-al-valor-agregado-iva>

Además: el presupuesto referencial SERCOP **se expresa sin IVA** (*"El presupuesto referencial es (…) NO INCLUYE IVA"*).

### 3.6 Bolivia 🇧🇴 — la ausencia de norma está reconocida oficialmente

Cita literal de la *Guía Boliviana para Diseño y Presentación de Proyectos* (MOPSV, 2017):
*"el diseño técnico (planos, especificaciones técnicas, cómputos métricos y presupuestos)… cuenta con una
heterogeneidad de criterios para su presentación y futura implementación, **sin que exista una normativa
específica ni estándares de calidad adecuados**"*.
<https://www.oopp.gob.bo/wp-content/uploads/2020/antiguos/Guia-Boliviana-para-diseno.pdf>

Lo que sí está normado es **el contenedor**, y eso el motor sí puede implementarlo:

- **Planilla de cómputos métricos obligatoria** con columnas fijas:
  `ÍTEM | UBICACIÓN | UNIDAD | Nº DE VECES | LARGO | ANCHO | ÁREA | ALTO | VOLUMEN | CÓMPUTO PARCIAL | CÓMPUTO TOTAL | TOTAL`, más un **croquis referencial por ítem**.
- **Cada ítem lleva su especificación técnica** con apartados obligatorios *"12.3.4 Medición"* y *"12.3.5 Forma de Pago"*.
- **APU del Formulario B-2** con la cascada normada: cargas sociales 55–71,18 % de la mano de obra → **IVA MO 14,94 %** → herramientas 5 % → gastos generales 12 % → utilidad 10 % → **IT 3,09 %**.
- **Precio unitario adoptado "con dos (2) decimales"**, importes en numeral **y en literal**, prevaleciendo el literal.

Modelo DBC de Obras, RM 021 de 02-02-2022 (MEFP), bajo el DS 0181 (NB-SABS):
<https://www.economiayfinanzas.gob.bo/sites/default/files/2023-01/DBC_LP_OBRAS_02022022.pdf>
Impuestos: SIN, *Cuadro General de Impuestos en Vigencia*: <https://www.impuestos.gob.bo/wp-content/uploads/2025/10/8580c1ef52.pdf>

**Consecuencia crítica para el motor:** en Bolivia **no se añade una línea de IVA al final del presupuesto**;
los impuestos ya están dentro de cada precio unitario. Un exportador que sume IVA al total de un presupuesto
boliviano lo duplica.

### 3.7 Argentina 🇦🇷

**No se encontró norma nacional ni IRAM de cómputo métrico.** Las reglas de medición viven en cada pliego. La
mejor fuente abierta y completa localizada es el **Pliego Único de Especificaciones Técnicas Generales de la
Dirección de Vialidad de la Provincia de Buenos Aires, Edición 2019** (512 pp.), donde el último artículo de cada
sección es *"Forma de medición y pago"*:
<https://www.vialidad.gba.gob.ar/datos/licitaciones/Pliego%20%C3%9Anico%20de%20Especificaciones%20T%C3%A9cnicas%202019.pdf>
Pliegos DNV: <https://www.argentina.gob.ar/transporte/vialidad-nacional/licitaciones/pliegos-de-especificaciones-tecnicas>

**INDEC — ICC** (base 1993 = 100) es la referencia de estructura de capítulos: por insumo, Materiales 46,0 /
Mano de obra 45,6 / Gastos generales 8,4; y **13 ítems de obra** con ponderación (Albañilería 34,7 · Estructura
14,1 · Sanitaria 9,7 · Pintura 8,4 · Carpintería de madera 8,0 · Otros 6,1 · Eléctrica 4,7 · Ascensores 4,3 ·
Gas 3,4 · Yesería 2,4 · Carpintería metálica 2,0 · Movimiento de tierra 1,6 · Vidrios 0,6).
Importante: el ICC *"no incluye… el impuesto al valor agregado (IVA)… Tampoco se considera el beneficio de la
empresa constructora"*. <https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-33> ·
metodología: <https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_icc.pdf>

**Particularidad de unidades:** la mampostería convive en **m³**, **m²** y **ml** según el pliego
(`Muro en elevación 0.20 — m2`, `Muro en cimiento 0.20 — ml`, `MAMPOSTERÍA… ELEVACIÓN DE 30 CM — M3`).
El motor debe permitir las tres para el mismo concepto.

**IVA (art. 28, Ley de IVA t.o. Dec. 280/97):** 21 % general; **10,5 %** para *"Los hechos imponibles previstos en
el inciso a) del artículo 3º **destinados a vivienda**, excluidos los realizados sobre construcciones preexistentes
que no constituyan obras en curso"* y los del inciso b) destinados a vivienda.
<https://servicios.infoleg.gob.ar/infolegInternet/anexos/40000-44999/42701/texact.htm>
(AFIP fue reemplazada por **ARCA** en 2024.)

### 3.8 España 🇪🇸 — los criterios de medición están publicados, pero en bases de precios

El **CTE** (RD 314/2006) regula *"las exigencias básicas de calidad"* — **no** contiene criterios de medición
(<https://www.boe.es/buscar/act.php?id=BOE-A-2006-5515>). El **Código Estructural** (RD 470/2021) sustituye a la
EHE-08 (<https://www.boe.es/buscar/act.php?id=BOE-A-2021-13681>).

Los criterios de medición reales están en las **bases de precios**:

- **BEDEC (ITeC)** — **de suscripción** (desde 85 € /mes, <https://tienda.itec.es/producto/bedec-es/banco-bedec/>), con **visor web público** en <https://bdc.itec.cat/vide> (publicaciones desde 2025) y <https://metabase.itec.cat/vide> (anteriores). Documento público de criterios: <https://itec.es/docs/pdf/bedec-criterios-es.pdf>. El tercer apartado de cada pliego *"recoge la unidad y el criterio con que es necesario hacer la medición correspondiente"*. ~5.000 pliegos paramétricos.
- **Generador de precios CYPE** — **consulta web gratuita y sin registro**, <https://www.generadordeprecios.info/>. Es la fuente pública más útil: cada partida publica **"criterio de medición en proyecto"**, **"criterio de medición en obra y condiciones de abono"** y, a menudo, **"criterio de valoración económica"**. Exporta a **FIEBDC-3 (.bc3)**.
- **PREOC** — privado, de pago: <https://www.preoc.es/>
- Bases autonómicas (BCCA Andalucía, IVE, País Vasco): **no verificadas** en esta investigación.

**Estructura del presupuesto (RD 1098/2001, arts. 130–131 — vigentes, sin nota de derogación en el BOE):**
`PEM` = Σ (cantidad × precio unitario) + partidas alzadas → `+ gastos generales de estructura 13 a 17 %`
(el 13 % es el habitual por Orden FOM/1824/2013 y APM/401/2018) → `+ 6 % de beneficio industrial` →
**`+ IVA aplicado sobre la suma del PEM y los gastos generales`** (literal del art. 131.2) = `PBL`.
El art. 130 prohíbe expresamente incorporar el IVA al precio unitario. En obra privada los porcentajes **no están regulados**.
<https://www.boe.es/buscar/act.php?id=BOE-A-2001-19995> · Ley 9/2017 art. 100: el PBL es *"el límite máximo de
gasto… **incluido el Impuesto sobre el Valor Añadido**"*; el **valor estimado** (art. 101) va **sin IVA**.
<https://www.boe.es/buscar/act.php?id=BOE-A-2017-12902>

**IVA (Ley 37/1992, <https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740>):**
21 % general (art. 90.Uno); **10 %** en renovación/reparación de vivienda con **tres requisitos acumulativos**
(destinatario persona física o comunidad, vivienda terminada ≥ 2 años antes, y **materiales ≤ 40 % de la base
imponible**) — art. 91.Uno.2.10º; y **10 %** en ejecuciones de obra *"consecuencia de contratos directamente
formalizados entre el promotor y el contratista"* de edificaciones *"destinadas principalmente a viviendas"*
(≥ 50 % de la superficie construida) — art. 91.Uno.3.1º.
⚠ **El 4 % de VPO es sólo para la ENTREGA por el promotor** (art. 91.Dos.1.6º); el art. 91.Tres excluye
expresamente las ejecuciones de obra de VPO de régimen especial o promoción pública del tipo superreducido:
**la obra de VPO tributa al 10 %**.
⚠ **Inversión del sujeto pasivo** (art. 84.Uno.2º.f) en ejecuciones de obra de urbanización, construcción o
rehabilitación entre promotor y contratista (y entre contratista y subcontratistas): **la factura va sin IVA**.
En Canarias no aplica IVA sino **IGIC**.

**La costumbre de "medición a cinta corrida" no está publicada** en BEDEC ni en CYPE — es práctica profesional,
no regla normativa. No convertirla en default.

### 3.9 Estados Unidos 🇺🇸

**No existe norma nacional obligatoria de medición.** Lo que existe son taxonomías y prácticas recomendadas:

- **CSI MasterFormat** (CSI + Construction Specifications Canada): 50 divisiones (00–49) agrupadas en 6 grupos; número de **6 dígitos leído en tres pares** (división / sección / subsección). Divisiones reservadas para expansión: 15–20, 24, 29, 30, 36–39, 47, 49. **MasterFormat 2020** fue la última edición fechada; en febrero de 2026 CSI pasó al modelo de actualización continua bajo *The Construction Standard* / **CSI Dynamic Standards** y publicó **MasterFormat 2026** (2.185 listados nuevos, 617 reorganizados). **De suscripción.**
  <https://www.csiresources.org/standards/masterformat> · <https://www.csiresources.org/standards/masterformat2026>
- **UniFormat** (CSI/CSC) y **ASTM E1557-09(2020)e1** *Standard Classification for Building Elements and Related Sitework—UNIFORMAT II*: **de pago (USD 136)**. Niveles: 1 letra (`A` Substructure, `B` Shell, `C` Interiors, `D` Services, `E` Equipment & Furnishings, `F` Special Construction, `G` Building Sitework, `Z` General), nivel 2 de 3 caracteres (`A10`), nivel 3 de 5 (`A1010`), y un nivel 4 opcional en el apéndice X1.
  <https://www.csiresources.org/standards/uniformat/about-uniformat> · <https://store.astm.org/e1557-09r20e01.html>
- **ASPE Standard Estimating Practice**, 12ª edición (American Society of Professional Estimators): práctica recomendada, **no obligatoria**, de pago. <https://aspenational.org/12sep/>

**Unidades imperiales:** SF (área), SY, CF, **CY** (volumen: concreto y excavación), **LF** (longitud), **EA**
(conteo), **TON** y **LB** (peso: acero estructural y refuerzo), GAL, HR, **LS** (lump sum). El encofrado se mide
en **SFCA** — *square feet of contact area*.

**Impuestos:** **no hay IVA**. Hay *sales & use tax* estatal y local. En la mayoría de estados el contratista es
tratado como **consumidor final** de los materiales (paga el impuesto al comprarlos) y no cobra impuesto sobre el
servicio; pero el resultado depende de si el contrato es *lump-sum* o *separated* y de si la obra es *capital
improvement* o *repair*. **El motor no debe llevar una tasa nacional para EE. UU.**: debe pedir jurisdicción y
tratamiento.

### 3.10 Estándar internacional 🌐

**ICMS 3** — *International Cost Management Standard*, 3ª edición, **publicada el 01-06-2022** por la
**ICMS Coalition** (49 organizaciones profesionales, constituida en 2015 en la sede del FMI) con RICS como editor.
**Descarga gratuita**, con traducción al español.
<https://icms-coalition.org/the-standard/> · <https://www.rics.org/profession-standards/rics-standards-and-guidance/sector-standards/construction-standards/icms-international-cost-management-standards>
Ediciones: 1ª julio 2017 · 2ª 2019 (life cycle costs) · 3ª 2022 (costes **y** emisiones de carbono).

- **Jerarquía:** nivel 1 *project / sub-project* → nivel 2 *categories* → nivel 3 *groups* → nivel 4 *sub-groups*.
  Los niveles 2 y 3 son **obligatorios y estandarizados**; el nivel 4 es discrecional y adaptable a la práctica local.
- **Seis categorías de nivel 2 (acrónimo ACROME):** *Acquisition, Construction, Renewal, Operation, Maintenance, End of life*. La suma de las cinco últimas es el coste de ciclo de vida.
- **Codificación real:** `C.GG.SSS` — p. ej. `1.01.010`, `2.03.030`, `2.09.010` (*Exchange rate fluctuation*).
- **Moneda:** *"No single currency is used as the basis of cost classification in ICMS"* — se reporta en la moneda
  local del proyecto, y es obligatorio declarar la **base date** y el **tipo de cambio** para que otro pueda
  reajustar. **Éste es exactamente el modelo que metra-ai debería adoptar para exportar entre países.**
- **Cantidad de proyecto:** se declara junto con su *"Quantity's Units of Measurement"* (p. ej. m²).
- Guía complementaria gratuita: <https://www.rics.org/content/dam/ricsglobal/documents/standards/icms-3-explained.pdf>

**RICS NRM 2** — *Detailed measurement for building works*. 1ª edición **abril 2012**, operativa desde el
**01-01-2013**; sustituyó a **SMM7** el **01-07-2013**. La suite NRM se reeditó en **octubre de 2021** (efectiva
01-12-2021) y de nuevo en **octubre de 2022**, cambiando su categoría a *practice information* sin cambios
materiales de contenido.
PDF oficial: <https://www.rics.org/content/dam/ricsglobal/documents/standards/nrm_2_detailed_measurement_for_building_works_1st_edition_rics.pdf> ·
actualización: <https://www.rics.org/content/dam/ricsglobal/documents/standards/NRM-2_Oct2022_Update.pdf> ·
portada: <https://www.rics.org/profession-standards/rics-standards-and-guidance/sector-standards/construction-standards/nrm>

- **41 work sections**: 1 Preliminaries · 2 Off-site manufactured materials · 3 Demolitions · 4 Alterations, repairs and conservation · 5 Excavating and filling · 6 Ground remediation · 7 Piling · 8 Underpinning · 9 Diaphragm walls · … · 11 In-situ concrete works · 12 Precast/composite concrete · 13 Precast concrete · 14 Masonry · 15 Structural metalwork · 16 Carpentry · 17 Sheet roof coverings · 18 Tile and slate roof and wall coverings · 19 Waterproofing · 21 Cladding and covering · 22 General joinery · 23 Windows, screens and lights · … · 28 Floor, wall, ceiling and roof finishings · … · 32 FF&E · 33 Drainage above ground · 34 Drainage below ground · 35 Site works · 36 Fencing · 37 Soft landscaping · 38 Mechanical services · 39 Electrical services · 40 Transportation · 41 External works.
- **Codificación elemental de 6 niveles** (0 project number · 1 bill number · 2 group element · 3 element · 4 sub-element · 5 component · 6 sub-component definido por el usuario), con sufijo opcional de work section. Ejemplo literal del propio documento: `DPB27-3.1.1.2.1.4` → con sufijo `DPB27-3.1.1.2.1.4/04`.
- **Unidades:** `m`, `m2`, `m3`, `kg`, `t`, `nr`, `item`.
- **Reglas generales de cantidad (3.3.2):** medir **neto tal como queda fijado en su posición**; el neto *"se
  considera que incluye todo el material adicional para solapes, juntas, costuras y similares, así como cualquier
  material de desperdicio"*; el trabajo curvo se mide **en el eje del material**; dimensiones al múltiplo de 10 mm;
  cantidades a entero salvo toneladas (2 decimales).

**POMI** — *Principles of Measurement (International) for Works of Construction*, RICS/BCIS, **junio 1979**
(reimpresión inglesa 2004). RICS lo tiene **archivado**, pero sigue en uso en contratos internacionales.
<https://www.isurv.com/downloads/download/164/principles_of_measurement_international_for_works_of_construction_archived>

**SMM7** — *Standard Method of Measurement of Building Works*, 7ª ed., 23 work sections. **Sustituido por NRM2 el
01-07-2013**; no debe adoptarse.

**CESMM4 Revised** — *Civil Engineering Standard Method of Measurement*, 4ª edición revisada, **ICE Publishing,
junio 2019** (4ª ed. original abril 2012). De pago. Es el equivalente de NRM2 para obra civil británica.

---

## 4. Cómo se traduce esto al código de metra-ai

El registro `backend/motor/unidades.py` ya soporta lo esencial: dimensiones físicas, factores a unidad base,
sistema `metrico`/`imperial`, mapa `EQUIVALENTE_SISTEMA` (`m2↔sf`, `m3↔cy`, `kg↔lb`, `und↔ea`, `glb↔ls`) y alias.
Lo que falta y esta investigación aporta:

1. **Añadir alias de país que hoy no resuelven:** `pza` ya existe; faltan `PA` (partida alzada, España),
   `Ud` (España), `pda`, `conj`, `sist`, `elem`, `jgo` (ya existe), `N°` (Chile), `UN`/`Un` (Argentina/Colombia),
   `GL` (Colombia/Argentina), `ML` (Colombia), `Gl` (Argentina), `SFCA` (EE. UU., alias de `sf`).
2. **Perfil de país** que precargue moneda, separadores, decimales, sistema de unidades y el catálogo de unidades
   sugeridas — pero **sin cerrarlo**: Bolivia y Ecuador tienen el campo "Unidad" como texto libre por norma.
3. **Modelo fiscal de tres variantes** (impuesto al final / dentro del APU / mayoración reglada con base parcial)
   más el caso colombiano de base gravable sobre utilidad y el caso estadounidense sin IVA.
4. **`estado_del_volumen`** en movimiento de tierras (`banco` | `suelto` | `compactado`) con factor de conversión;
   Perú aporta una tabla de esponjamiento normada que puede venir precargada.
5. **Reglas de vano por familia de partida**, con los cuatro modos de §2.1 — nunca un umbral único de país.
6. **Partidas derivadas automáticas** cuando el modo es `deducir_todo`: vestidura de derrames en ml a partir del
   perímetro del vano × espesor del muro (Perú lo exige explícitamente).
7. **Doble criterio de medición por partida** (proyecto vs obra/abono), como hace CYPE: son cantidades distintas
   y hoy se confunden.
8. **Exportador consciente del país:** Bolivia exige el importe **en literal** además de en numeral, y que
   prevalezca el literal ante discrepancia.

---

## 5. Lo que quedó sin verificar (no inventar)

| # | País | Dato pendiente | Por qué |
|---|---|---|---|
| 1 | **Ecuador** | **Alcance del IVA 5 % de construcción**: ¿sólo transferencia de materiales o también contratos de obra? | El portal del SRI enuncia ambas cosas en puntos distintos. Es el dato de mayor impacto económico del informe |
| 2 | **Chile** | Contenido de **NCh353:2018**: tabla de descuento de vanos, criterio eje/cara, tratamiento del moldaje | Norma de pago del INN; no se descarga por política |
| 3 | **Chile** | Que el Banco Central calcule la UF; Res. Ex. que aprueban la edición 2026 del Manual de Carreteras; itemizado oficial del DS19 | Fuentes no accesibles |
| 4 | **Colombia** | Texto literal de los numerales "Medida" y "Forma de pago" de INVÍAS 2022 e IDU ET-IC-01 | `invias.gov.co` e `idu.gov.co` devuelven 403 a acceso automatizado |
| 5 | **Colombia** | Criterio explícito eje vs cara para mampostería; % de desperdicio; esponjamiento | No publicado |
| 6 | **México** | Umbral de deducción de vanos y criterio eje/cara | Búsqueda explícita en CDMX Libro 3 Tomo II: cero coincidencias. Se fija por especificación particular (N-LEG-3 cl. E.5) |
| 7 | **México** | Catálogo de conceptos del IMSS; fecha de la última reforma al RLOPSRM; edición 2026 del catálogo CONAGUA | No disponibles públicamente |
| 8 | **Argentina** | Existencia de norma nacional o IRAM de medición; regla "vacío por lleno" y su umbral de 3,00 m²; si el encofrado es ítem separado; % de desperdicio | No hallada en fuente oficial. **No convertir la costumbre en default** |
| 9 | **Bolivia / Ecuador** | Todas las reglas de medición (vanos, eje/cara, encofrado, desperdicio) | No existen a nivel nacional; son por proyecto |
| 10 | **Bolivia** | Manual de Especificaciones Técnicas ABC 2011; normativa de CABOCO | El portal de la ABC no lo lista; `caboco.org` devuelve 404 |
| 11 | **Ecuador** | Abreviaturas oficiales de unidades (`u`, `glb`) en documento SERCOP; decimales exigidos | `portal.compraspublicas.gob.ec` inaccesible. **El separador decimal ecuatoriano queda como no verificado**: CLDR asigna coma decimal a `es-EC`, la práctica dolarizada usa punto |
| 12 | **España** | Umbrales concretos de BEDEC (los verificados son de CYPE); bases de precios autonómicas (BCCA, IVE, País Vasco); significado del código clásico de 8 caracteres | BEDEC exige suscripción o visor interactivo |
| 13 | **Perú** | Separador decimal en presupuestos oficiales (la **norma técnica usa coma**; los presupuestos S10 usan punto); composición interna IGV/IPM del 18 % en 2026 | `gob.pe` devuelve 418/403 |
| 14 | **EE. UU.** | Reglas de medición de ASPE SEP 12ª ed. | Publicación de pago |
| 15 | **Todos** | Separador decimal y de miles respaldado por norma oficial | Salvo Chile (formato publicado por el SII) y España/México (ejemplos en documentos oficiales), la fuente usada es **Unicode CLDR** (vía Babel), que es el estándar de facto de localización, no una norma nacional |

---

## 6. Fuentes

**Internacional**
- ICMS Coalition — The Standard: <https://icms-coalition.org/the-standard/>
- RICS — ICMS: <https://www.rics.org/profession-standards/rics-standards-and-guidance/sector-standards/construction-standards/icms-international-cost-management-standards>
- RICS — ICMS 3 explained (PDF): <https://www.rics.org/content/dam/ricsglobal/documents/standards/icms-3-explained.pdf>
- RICS — NRM suite: <https://www.rics.org/profession-standards/rics-standards-and-guidance/sector-standards/construction-standards/nrm>
- RICS — NRM 2 (PDF): <https://www.rics.org/content/dam/ricsglobal/documents/standards/nrm_2_detailed_measurement_for_building_works_1st_edition_rics.pdf>
- RICS — NRM 2 Oct 2022 update (PDF): <https://www.rics.org/content/dam/ricsglobal/documents/standards/NRM-2_Oct2022_Update.pdf>
- isurv — POMI (archivado): <https://www.isurv.com/downloads/download/164/principles_of_measurement_international_for_works_of_construction_archived>
- ISO — ISO 4217 currency codes: <https://www.iso.org/iso-4217-currency-codes.html> · agencia de mantenimiento SIX: <https://www.six-group.com/en/products-services/financial-information/market-reference-data/data-standards.html>

**Perú** · SPIJ RD 073-2010: <https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf> · Ley 32069: <https://leyes.congreso.gob.pe/Documentos/2021_2026/ADLP/Texto_Consolidado/32069-TXM.pdf> · MTC manuales: <https://portal.mtc.gob.pe/transportes/caminos/normas_carreteras/manuales.html> · SUNAT IGV: <https://orientacion.sunat.gob.pe/3053-concepto-tasa-y-operaciones-gravadas-igv-empresas>

**Colombia** · NSR-10: <https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=39255> · INVÍAS 2022: <https://www.invias.gov.co/index.php/archivo-y-documentos/documentos-tecnicos/12865-especificaciones-generales-de-construccion-de-carreteras-2022> · IDU ET-IC-01: <https://www.idu.gov.co/page/especificaciones-tecnicas-generales-de-materiales> · ICBF especificaciones: <https://www.icbf.gov.co/sites/default/files/anexo_no.2_-_especificaciones_tecnicas_de_obra.pdf> · APU DNP: <https://documentossoportewcf.dnp.gov.co/DocumentosSoportes/Territorial/Tramites/2__ANALISIS_DE_PRECIOS_UNITARIOS_20230713_1005.PDF> · ET art. 468: <https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6533> · DIAN Oficio 901006/2021: <https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_901006_2021.htm> · Colombia Compra Eficiente: <https://www.colombiacompra.gov.co/archivos/tema/obra-publica>

**Chile** · NCh353:2018 (ficha INN): <https://ecommerce.inn.cl/nch353201870066> · OGUC: <https://www.minvu.gob.cl/wp-content/uploads/2019/05/OGUC-Marzo-2026-D.S.-N%C2%B02-D.O.-16-03-2026.pdf> · Itemizado DS49: <https://www.minvu.gob.cl/wp-content/uploads/2019/05/Res_7713-16062017_Itemizado-Tecnico.pdf> · Manual de Carreteras MOP: <https://www.mop.gob.cl/serviciosmop/manual-de-carreteras/> · UF (SII): <https://www.sii.cl/valores_y_fechas/uf/uf2026.htm> · IVA 19 %: <https://www.sii.cl/preguntas_frecuentes/impuestos_mensuales/001_130_0572.htm> · CEEC Circular 37/2023: <https://www.sii.cl/normativa_legislacion/circulares/2023/circu37.pdf>

**México** · Reforma LOPSRM DOF 16-04-2025: <https://sidof.segob.gob.mx/notas/5755218> · SICT normas: <https://normas.imt.mx/libros> · N-LEG-3/24: <https://normas.imt.mx/storage/normativa/N-LEG-3-24.pdf> · N-INT-1/24: <https://normas.imt.mx/storage/normativa/N-INT-1-24.pdf> · N-INT-4/26 (unidades): <https://normas.imt.mx/storage/normativa/N-INT-4-26.pdf> · N-CTR-CAR-1-02-003/04 (concreto): <https://normas.imt.mx/storage/normativa/N-CTR-CAR-1-02-003-04.pdf> · N-CTR-CAR-1-02-004/02 (acero): <https://normas.imt.mx/storage/normativa/N-CTR-CAR-1-02-004-02.pdf> · CONAGUA 2025: <https://www.gob.mx/cms/uploads/attachment/file/985551/CATALOGO_GENERAL_DE_AGUA_POTABLE_DE_PRECIOS_UNITARIOS_PARA_LA_CONSTRUCCI_N_DE_SISTEMAS_DE_AGUA_POTABLE_Y_ALCANTARILLADO_2025.pdf> · CDMX Libro 3: <https://infocdmx.org.mx/escuela/curso_capacitadores/procesos_contratacion/normas_tecnicas_VII.pdf> · NOM-008-SE-2021: <https://www.dof.gob.mx/nota_detalle.php?codigo=5713228&fecha=29/12/2023> · SAT frontera: <https://www.sat.gob.mx/minisitio/EstimulosFiscalesFronteraNorteSur/documentos/PreguntasFrecuentes.pdf>

**Ecuador** · NEC (MIT): <https://www.mit.gob.ec/norma-ecuatoriana-de-la-construccion/> · NEVI-12 Vol. 3: <https://www.mit.gob.ec/wp-content/uploads/downloads/2013/12/01-12-2013_Manual_NEVI-12_VOLUMEN_3.pdf> · NEVI-12 Vol. 6: <https://www.mit.gob.ec/wp-content/uploads/downloads/2013/12/01-12-2013_Manual_NEVI-12_VOLUMEN_6.pdf> · LOSNCP consolidada: <https://institutodemocracia.gob.ec/wp-content/uploads/2025/10/Ley_organica_del_sistema_nacional_de_contratacion_public_LOSNCP.pdf-07102025.pdf> · IPCO INEC: <https://www.ecuadorencifras.gob.ec/indice-de-precios-de-la-construccion/> · SRI IVA: <https://www.sri.gob.ec/impuesto-al-valor-agregado-iva>

**Bolivia** · Guía Boliviana: <https://www.oopp.gob.bo/wp-content/uploads/2020/antiguos/Guia-Boliviana-para-diseno.pdf> · DBC Obras (RM 021/2022): <https://www.economiayfinanzas.gob.bo/sites/default/files/2023-01/DBC_LP_OBRAS_02022022.pdf> · SIN impuestos: <https://www.impuestos.gob.bo/wp-content/uploads/2025/10/8580c1ef52.pdf> · Ley 843: <https://www.lexivox.org/norms/BO-L-843R2.html>

**Argentina** · PUETG DVBA 2019: <https://www.vialidad.gba.gob.ar/datos/licitaciones/Pliego%20%C3%9Anico%20de%20Especificaciones%20T%C3%A9cnicas%202019.pdf> · Pliegos DNV: <https://www.argentina.gob.ar/transporte/vialidad-nacional/licitaciones/pliegos-de-especificaciones-tecnicas> · INDEC ICC: <https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-33> · metodología ICC: <https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_icc.pdf> · Ley IVA t.o. Dec. 280/97: <https://servicios.infoleg.gob.ar/infolegInternet/anexos/40000-44999/42701/texact.htm> · CAMARCO indicadores: <https://www.camarco.org.ar/indicadores/indicadores-de-costos/>

**España** · CTE RD 314/2006: <https://www.boe.es/buscar/act.php?id=BOE-A-2006-5515> · Código Estructural RD 470/2021: <https://www.boe.es/buscar/act.php?id=BOE-A-2021-13681> · RD 1098/2001 (arts. 130-131): <https://www.boe.es/buscar/act.php?id=BOE-A-2001-19995> · Ley 9/2017: <https://www.boe.es/buscar/act.php?id=BOE-A-2017-12902> · Ley 37/1992 (IVA): <https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740> · BEDEC criterios (ITeC): <https://itec.es/docs/pdf/bedec-criterios-es.pdf> · BEDEC visor: <https://bdc.itec.cat/vide> · BEDEC tienda: <https://tienda.itec.es/producto/bedec-es/banco-bedec/> · CYPE Generador de precios: <https://www.generadordeprecios.info/> · CYPE FFX010: <https://generadordeprecios.info/obra_nueva/Fachadas_y_particiones/Fabrica_no_estructural/FFX_Hoja_exterior_cara_vista_en_fa/FFX010_Hoja_exterior_de_fachada_de_dos_hoj.html> · CYPE RPE005: <https://generadordeprecios.info/obra_nueva/Revestimientos_y_trasdosados/Conglomerados_tradicionales/Enfoscados/RPE005_Enfoscado_de_cemento_sobre_parament.html> · PREOC: <https://www.preoc.es/>

**Estados Unidos** · CSI MasterFormat: <https://www.csiresources.org/standards/masterformat> · MasterFormat 2026: <https://www.csiresources.org/standards/masterformat2026> · UniFormat: <https://www.csiresources.org/standards/uniformat/about-uniformat> · ASTM E1557-09(2020)e1: <https://store.astm.org/e1557-09r20e01.html> · ASPE SEP 12ª ed.: <https://aspenational.org/12sep/>
