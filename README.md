# METRA AI

Metrados de obra **trazables, auditables y exportables**. Calcula, revisa,
organiza y exporta cantidades de obra de todas las especialidades, desde
trabajos preliminares hasta acabados e instalaciones.

No asume una normativa única: el país del proyecto define la norma de medición,
la moneda, el sistema de unidades y las reglas de descuento.

---

## Arrancar

```
python run.py
```

Abre `http://127.0.0.1:8770`. En Windows también sirve `INICIAR.bat`.

Opciones:

| Comando | Qué hace |
|---|---|
| `python run.py --demo` | Borra y recrea el proyecto de demostración |
| `python run.py --puerto 9000` | Otro puerto |
| `python run.py --recargar` | Recarga automática al editar código |
| `python -m pytest tests/ -q` | Ejecuta las 56 pruebas |

Documentación viva de la API en `/api/docs`.

---

## Las cinco reglas que definen la app

Salieron de auditar un metrador real contra el texto de la norma. Cada una
corrige un error que se cobra caro en un expediente técnico.

**1. Un campo vacío se omite; no vale cero.**
En la planilla de sustento, `1 × 5.00 × 3.00` da 15,00 m². Si el motor
multiplicara por los campos vacíos, daría cero — y ese cero pasa desapercibido.

**2. El umbral de descuento de vanos depende de la familia, no de un
interruptor.** Los muros descuentan todo vano sin umbral (OE.3.1); los pisos no
descuentan huecos menores a 0,25 m² (OE.3.4). Hay cuatro modos distintos:
descontar todo, umbral, **descontar solo el exceso** (España, revestimientos) y
no descontar (Colombia, «vacío por lleno»). Un solo interruptor global produce
error garantizado en al menos una familia.

**3. El desperdicio no entra al metrado.** Va en el análisis de precios
unitarios. La app siempre muestra dos cifras separadas: *metrado neto* (lo que
va al presupuesto) y *cantidad a comprar* (referencial). Sumarlo en ambos sitios
lo cobra dos veces.

**4. Si falta un dato, la app lo dice; no lo inventa.** Una fila incompleta
queda fuera del total y aparece marcada. Nunca se rellena con un cero silencioso.

**5. Toda cantidad viaja con su origen.** Fórmula, plano, lámina, autor, fecha y
si fue medida, ingresada, importada, detectada por IA o **supuesta**. El botón
«¿De dónde sale?» reconstruye el cálculo paso a paso.

Además: análisis dimensional con bloqueo. Si la unidad es m² y las columnas
llenas producen un volumen, la fila no se guarda.

---

## Qué trae

| Módulo | Estado |
|---|---|
| Panel general con avance, presupuesto y pendientes | ✅ |
| Proyectos multi-país (10 sistemas normativos) | ✅ |
| Estructura edificio → sector → nivel → ambiente | ✅ |
| Carga de PDF, imágenes, DXF, IFC, Excel y CSV | ✅ |
| Visor de planos con calibración de escala y medición | ✅ |
| Hoja de metrados tecleable, con pegado desde Excel | ✅ |
| Repetición de filas por niveles y ejes | ✅ |
| Catálogo de **774 partidas** de la norma peruana | ✅ |
| Cuadro de acero con despiece | ✅ |
| Control de calidad: 13 validaciones con cita normativa | ✅ |
| Presupuesto, APU, insumos, curva S, adicionales | ✅ |
| Versiones y comparación | ✅ |
| Exportación a Excel (fórmulas vivas), PDF y CSV | ✅ |
| Roles, aprobación, bloqueo e historial de auditoría | ✅ |
| Asistente que pide confirmación antes de modificar | ✅ |
| Lectura automática de planos por IA | Arquitectura preparada, sin implementar |

---

## Fuentes

El catálogo y las tablas técnicas se extrajeron de documentos oficiales, y cada
dato viaja con su procedencia. Las etiquetas son: `NORMA`, `E060`,
`FICHA_FABRICANTE`, `LITERATURA`, `COSTUMBRE_OBRA` y `USUARIO`.

- **Norma Técnica de Metrados para Obras de Edificación y Habilitaciones
  Urbanas** — R.D. N° 073-2010-VIVIENDA/VMCS-DNC. 774 partidas extraídas del PDF
  oficial del SPIJ‑MINJUS; 338 con unidad y regla de medición verificadas
  literalmente.
- **RNE**: E.060 concreto armado, E.070 albañilería, E.090 estructuras
  metálicas, IS.010, EM.010, OS.050, OS.070, G.050.
- **Fichas de fabricante**: Aceros Arequipa, SiderPerú, ladrilleras Lark y
  Pirámide, Pavco, Nicoll, Indeco.
- **Internacional**: RICS NRM2, CSI MasterFormat, ICMS, y las normas de
  Colombia, Chile, México, Ecuador, Bolivia, Argentina, España y EE. UU.

Los informes completos están en `docs/investigacion/`. Los PDF originales no se
versionan por tamaño; el extractor `docs/normas/_extraer_partidas.py` regenera
el catálogo desde el PDF de la norma.

Lo que no se pudo verificar está marcado `verificado: false` y se muestra como
tal en la interfaz. Un número sin fuente no entra al motor.

---

## Arquitectura

Ver `ARCHITECTURE.md`. En una línea: motor de cálculo puro en `backend/motor`
(sin HTTP ni base de datos, testeable solo), API en `backend/api`, y una
interfaz de módulos ES sin compilación.

---

## Despliegue

Servicio web Python. `render.yaml` y `Procfile` incluidos.

```
gunicorn backend.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

Variables de entorno:

| Variable | Para qué |
|---|---|
| `METRA_DB_URL` | Cadena de conexión. Por defecto SQLite en `datos/metra.db`; acepta PostgreSQL sin cambiar código |
| `METRA_MODO` | `local` permite metrar sin cuenta; `nube` exige registro |
| `METRA_ADMIN_EMAIL` | Único correo que obtiene rol de administrador al registrarse |
| `METRA_DIR_DATOS` | Carpeta de base de datos y archivos subidos |

**Aviso sobre el plan gratuito de Render:** el disco es efímero. La base de
datos y los planos subidos se pierden en cada despliegue. El catálogo normativo
y el proyecto de demostración se regeneran solos al arrancar, así que la app
nunca queda vacía, pero para trabajo real hay que conectar un disco persistente
o una base PostgreSQL con `METRA_DB_URL`.
