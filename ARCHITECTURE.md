# METRA AI — Arquitectura

## Decisiones críticas

| Decisión | Elección | Por qué (y qué se descartó) |
|---|---|---|
| Stack | FastAPI + SQLAlchemy + módulos ES sin build | Cero compilación en el frontend, validación y OpenAPI gratis en el backend. Se descartó React/Vite (paso de build frágil en Windows) y Flask (sin validación ni esquema de API). |
| Base de datos | SQLite por defecto, PostgreSQL sin tocar código | Un archivo, cero servicio que instalar. No se usa ningún dialecto propietario: cambiar `METRA_DB_URL` basta. Se descartó `localStorage`: esta app es multiusuario, con roles y auditoría. |
| Aritmética | `Decimal` de extremo a extremo; las cantidades se guardan como texto | `Numeric` sobre SQLite pierde precisión y `float` arrastra error binario. Un metrado no puede depender de eso. |
| Redondeo | Parcial redondeado por fila; total = suma de parciales redondeados | Convención de expediente: el revisor suma con calculadora lo que ve impreso. Redondear al final descuadra la planilla línea a línea. |
| Fórmulas | AST con lista blanca de nodos y funciones | Una fórmula guardada es dato del usuario, no código. Se descartó `eval()`. |
| Campos vacíos | Se omiten del producto | `1 × 5 × 3` = 15, no 0. Es la regla de la planilla de sustento de todo expediente. |
| Códigos de ítem | Calculados por posición (`01.02.03`); el código normativo (`OE.3.1.1`) viaja aparte | Mover una partida no obliga a renumerar. El expediente exige ambos. |
| Jerarquía física | UNA tabla auto-referenciada (`Ubicacion`) con `tipo` | Edificio → bloque → sector → nivel → ambiente son el mismo tipo de nodo. Una carretera usa tramo → progresiva sin cambiar el esquema. Se descartaron cinco tablas paralelas. |
| Coordenadas de plano | Píxeles del render canónico del servidor (zoom 2.0) | El zoom de pantalla es una transformación visual. Una medición al 400% vale igual que al 100%. |
| Reglas normativas | Datos con cita literal, no condicionales dispersos | Cuando el motor bloquea, muestra el texto de la norma. «Esto está mal» no se puede defender ante una supervisión. |
| Tablas técnicas | JSON en `datos/tablas/`, con `fuente` y `verificado` por fila | Corregir un peso de varilla no debe requerir tocar código ni volver a desplegar. |
| Asistente | Motor de intenciones determinista; enganche opcional a un modelo | Funciona sin conexión ni clave, y no puede alucinar una cantidad. Toda acción que modifica pasa por confirmación explícita. |

## Estructura

```
metra-ai/
  run.py                     Arranque: crea tablas, siembra, abre el navegador
  backend/
    main.py                  App FastAPI, manejo de errores, montaje del frontend
    db.py                    Motor, sesión, PRAGMA de SQLite (FK, WAL)
    models.py                22 entidades
    security.py              PBKDF2, sesiones, roles y permisos
    audit.py                 Registro de auditoría inmutable
    servicios.py             Puente base de datos ↔ motor; árbol y códigos de ítem
    semillas.py              Catálogo normativo e insumos base
    demo.py                  Edificio de tres pisos de demostración
    motor/                   PURO: sin HTTP, sin base de datos, testeable solo
      redondeo.py            Decimal, reglas de redondeo por proyecto
      unidades.py            43 unidades, dimensiones, conversión métrico/imperial
      formulas.py            Evaluador seguro + 14 plantillas de fórmula
      medicion.py            Planilla, análisis dimensional, deducción de vanos
      normas.py              Reglas con cita literal; 4 modos de descuento
      validaciones.py        13 validaciones de control de calidad
      acero.py               Cuadro de acero y despiece
      costos.py              APU (convención S10), resumen y curva S
      especialidades.py      11 especialidades con color y tipos de elemento
      paises.py              Configuración por país
      plantillas.py          Plantillas de metrados por tipo de proyecto
      tablas.py              Cargador de tablas técnicas con procedencia
    api/                     11 routers, 65 rutas
    export/                  Excel con fórmulas vivas · PDF con portada y firmas
  frontend/
    index.html               Shell
    css/app.css              Sistema de diseño (tokens, taller, planilla, impresión)
    js/core/                 api · estado · fmt
    js/ui/base.js            el(), iconos, modal, avisos, confirmación
    js/vistas/               17 pantallas
  datos/tablas/*.json        Catálogo normativo y tablas técnicas
  docs/investigacion/        Informes de las fuentes, con URL y verificación
  tests/                     56 pruebas
```

## Contrato del motor

Todo el motor recibe y devuelve tipos simples. No conoce el ORM.

- `formulas.evaluar(expresion, variables) -> Resultado`
  Devuelve `valor`, la expresión con los números sustituidos, el paso a paso y
  la lista de `faltantes`. **Nunca asume cero.**
- `medicion.calcular_fila(datos, unidad, reglas) -> Fila`
  Producto de las columnas llenas o evaluación de fórmula, con análisis
  dimensional. `error` bloquea; `aviso` solo informa.
- `medicion.total_partida(filas, unidad, desperdicio, cantidad_manual, reglas)`
  Suma los parciales ya redondeados. El desperdicio sale como
  `cantidad_a_comprar`, aparte del metrado.
- `normas.descontar_vano(area, familia) -> (aplica, motivo, area_a_descontar)`
  El tercer valor importa: en modo `deducir_exceso` no se descuenta el vano
  completo.
- `validaciones.evaluar(contexto) -> [Alerta]`
  Cada alerta trae gravedad, explicación, **cómo se corrige** y la cita.
- `acero.cuadro(barras, desperdicio) -> dict`
  Despiece, resumen por diámetro y peso. Una barra sin longitud no inventa peso:
  se cuenta como incompleta.
- `costos.analisis(filas, rendimiento, reglas) -> dict`
  Cantidad de mano de obra y equipo = cuadrilla × 8 h / rendimiento, a 4
  decimales.

## Contrato de las vistas

Cada vista exporta `render(contenedor, params)` y se vuelve a invocar en cada
cambio de ruta. El estado de interfaz (nodo abierto, filtro, partida activa)
vive a nivel de módulo. El estado compartido está en `core/estado.js`; las
mutaciones de datos van siempre por la API, nunca a un objeto local.

## Trazabilidad: la cadena completa

```
Elemento (C-1, 0.25×0.50)  ─┐
Trazo sobre plano calibrado ─┼─→ Medicion (fila) ─→ Item (partida) ─→ Presupuesto
Pegado desde Excel          ─┤        │
Fórmula escrita a mano      ─┘        └─→ origen · lámina · autor · fecha · supuesto
                                          └─→ Historial (quién, qué, cuándo)
```

Cualquier cantidad del presupuesto se recorre hacia atrás hasta la fila que la
produjo, el plano del que salió y la persona que la escribió.

## Fuera de alcance (deliberado)

Lectura automática de planos por visión artificial, importación directa de DWG y
RVT (formatos propietarios sin lector abierto), CPM con holguras, fórmula
polinómica y firma digital de reportes. Cada uno es un módulo futuro con su
punto de enganche ya previsto, no una omisión accidental.

## Deudas conocidas

- `servicios.arbol()` calcula cada partida por separado: N+1 consultas. Con 68
  partidas es imperceptible; a partir de unas 500 conviene una consulta única de
  mediciones agrupadas por item.
- El proyecto de demostración usa dos valores de literatura marcados como
  `supuesto` (concreto por m² de aligerado y ladrillos por m²). Están así a
  propósito, para que se vea cómo la app trata un supuesto.
- Las tablas de tierras e instalaciones están cargadas pero el motor todavía no
  las consume: los cálculos de volumen por secciones y de conductores por
  canalización están especificados en `docs/investigacion/03-*` y pendientes de
  implementar.
