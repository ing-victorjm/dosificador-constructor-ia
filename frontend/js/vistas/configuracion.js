// Configuración: reglas de cálculo del proyecto, redondeo, normativa y estado
// de las tablas técnicas cargadas.

import { api } from '../core/api.js';
import { estado, refrescarProyecto, alternarTema } from '../core/estado.js';
import { num } from '../core/fmt.js';
import {
  el, vaciar, icono, cargando, chip, panel, campo, cita, avisoCaja,
  exito, error as avisoError,
} from '../ui/base.js';

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const cuerpo = el('div', { class: 'contenido', estilo: { maxWidth: '1080px' } });
  contenedor.append(cuerpo);

  const ref = estado.referencia;
  const reglas = ref.reglas;

  cuerpo.append(
    el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
      'Configuración'),
    el('p', { class: 'suave mb2', estilo: { marginTop: 0 } },
      'Reglas de cálculo, apariencia y estado de las fuentes técnicas.'),

    panel('Apariencia', el('div', {},
      el('div', { class: 'fila entre' },
        el('div', {},
          el('div', { class: 'fuerte' }, 'Tema'),
          el('div', { class: 'chico apagado' },
            'Claro u oscuro. Los reportes impresos siempre salen en claro.')),
        el('button', {
          class: 'btn',
          onclick: () => { alternarTema(); location.reload(); },
        }, icono(estado.tema === 'oscuro' ? 'sol' : 'luna'),
          estado.tema === 'oscuro' ? 'Cambiar a claro' : 'Cambiar a oscuro')),
      el('div', { class: 'sep' }),
      el('div', { class: 'chico suave' },
        el('strong', {}, 'Atajos: '),
        'barra / o Ctrl+K para buscar · Ctrl+Shift+D cambia el tema · '
        + 'Enter y flechas navegan la planilla · Ctrl+V pega un bloque de Excel en la planilla.'))),

    proyectoId ? await panelProyecto(proyectoId) : avisoCaja('info',
      'Abra un proyecto para configurar sus reglas de cálculo.'),

    el('div', { class: 'mt2' },
      panel('Reglas normativas que aplica el motor', el('div', {},
        el('div', { class: 'chico fuerte mb1' }, 'Descuento de vanos por familia'),
        el('div', { class: 'tabla-envoltura' },
          el('table', { class: 'tabla densa' },
            el('thead', {}, el('tr', {},
              el('th', {}, 'Familia'), el('th', {}, 'Modo'), el('th', { class: 'num' }, 'Umbral'),
              el('th', {}, 'Código'), el('th', {}, 'País'))),
            el('tbody', {}, ...reglas.familias.map((f) => el('tr', {},
              el('td', { class: 'fuerte' }, f.nombre),
              el('td', { class: 'chico' }, f.modo_explicacion),
              el('td', { class: 'num mono' }, f.umbral_m2 === '0' ? '—' : `${f.umbral_m2} m²`),
              el('td', { class: 'codigo' }, f.codigo),
              el('td', {}, f.pais ? chip(f.pais) : chip('general')))))),
        avisoCaja('alerta', reglas.umbral_mito.aviso),
        el('div', { class: 'sep' }),
        el('div', { class: 'chico fuerte mb1' }, 'Desperdicio'),
        cita({ texto: reglas.desperdicio.cita, codigo: reglas.desperdicio.codigo,
          etiqueta: reglas.desperdicio.etiqueta }),
        el('p', { class: 'chico suave' }, reglas.desperdicio.explicacion),
        el('div', { class: 'sep' }),
        el('div', { class: 'chico fuerte mb1' }, 'Esponjamiento'),
        cita({ texto: reglas.esponjamiento.cita, codigo: reglas.esponjamiento.codigo,
          etiqueta: reglas.esponjamiento.etiqueta }),
        el('p', { class: 'chico suave' }, reglas.esponjamiento.contradiccion),
        el('div', { class: 'sep' }),
        el('div', { class: 'chico fuerte mb1' }, 'Erratas conocidas de la norma'),
        el('p', { class: 'chico suave' }, reglas.criterio_erratas),
        el('ul', { class: 'chico suave', estilo: { lineHeight: '1.7' } },
          ...reglas.erratas.map((e) => el('li', {},
            el('strong', { class: 'mono' }, e.codigo + ': '), e.detalle)))))),

    el('div', { class: 'mt2' }, await panelTablas()),
  );
}

async function panelProyecto(proyectoId) {
  const datos = await api.obtener(`/proyectos/${proyectoId}`);
  const p = datos.proyecto;
  const r = p.reglas || {};
  const redondeo = r.redondeo || {};

  const decMetrado = el('input', { type: 'number', min: 0, max: 6, value: redondeo.decimales_metrado ?? 2 });
  const decPrecio = el('input', { type: 'number', min: 0, max: 6, value: redondeo.decimales_precio ?? 2 });
  const modo = el('select', {},
    ...[['medio_arriba', 'Medio arriba (convención de obra)'],
        ['medio_par', 'Medio par (ISO 80000)'],
        ['arriba', 'Siempre hacia arriba'],
        ['abajo', 'Siempre hacia abajo']].map(([v, t]) =>
      el('option', { value: v, selected: v === (redondeo.modo || 'medio_arriba') }, t)));
  const gg = el('input', { type: 'text', value: r.gastos_generales_pct ?? '10', class: 'num' });
  const utilidad = el('input', { type: 'text', value: r.utilidad_pct ?? '5', class: 'num' });
  const impuestoTasa = el('input', { type: 'text', value: r.impuesto?.tasa ?? '18', class: 'num' });
  const impuestoNombre = el('input', { type: 'text', value: r.impuesto?.nombre ?? 'IGV' });
  const exigirLamina = el('input', { type: 'checkbox', checked: r.exigir_lamina !== false });
  const bloquearDim = el('input', {
    type: 'checkbox', checked: r.bloquear_dimension_incompatible !== false,
  });
  const regimen = el('select', {},
    ...[['OE', 'Edificación (OE) — el esponjamiento entra en el metrado de eliminación'],
        ['HU', 'Habilitación urbana (HU) — el esponjamiento va al análisis de precios']]
      .map(([v, t]) => el('option', { value: v, selected: v === (r.regimen || 'OE') }, t)));

  return panel(`Reglas de cálculo — ${p.nombre}`, el('div', {},
    avisoCaja('info', el('div', {},
      el('strong', {}, 'Normativa aplicada: '), p.normativa || 'Sin norma declarada.',
      el('div', { class: 'chico mt1' },
        `País: ${p.pais} · Moneda: ${p.moneda} · Sistema: ${p.sistema_unidades}`))),

    el('div', { class: 'fila-campos mt2' },
      campo('Decimales del metrado', decMetrado),
      campo('Decimales de precios', decPrecio),
      campo('Modo de redondeo', modo)),
    el('div', { class: 'chico apagado', estilo: { marginTop: '-8px' } },
      'Los parciales se redondean fila por fila y el total suma los parciales redondeados: '
      + 'así la planilla impresa cuadra línea a línea, como espera un revisor con calculadora.'),

    el('div', { class: 'sep' }),
    el('div', { class: 'fila-campos' },
      campo('Gastos generales %', gg),
      campo('Utilidad %', utilidad),
      campo('Impuesto', impuestoNombre),
      campo('Tasa %', impuestoTasa)),

    el('div', { class: 'sep' }),
    campo('Régimen de medición', regimen),

    el('label', { class: 'interruptor mt2' }, exigirLamina, el('span', { class: 'pista' }),
      el('span', {}, 'Exigir lámina de referencia en cada fila de metrado')),
    el('div', { class: 'chico apagado', estilo: { marginLeft: '46px' } },
      'La supervisión exige poder rastrear cada cantidad hasta un plano concreto.'),

    el('label', { class: 'interruptor mt2' }, bloquearDim, el('span', { class: 'pista' }),
      el('span', {}, 'Bloquear filas con incompatibilidad dimensional')),
    el('div', { class: 'chico apagado', estilo: { marginLeft: '46px' } },
      'Impide guardar una fila que alimenta una partida en m² con largo × ancho × alto.'),

    el('div', { class: 'fila mt2', estilo: { justifyContent: 'flex-end' } },
      el('button', {
        class: 'btn primario',
        onclick: async (e) => {
          e.target.disabled = true;
          try {
            await api.actualizar(`/proyectos/${proyectoId}`, {
              reglas: {
                redondeo: {
                  decimales_metrado: parseInt(decMetrado.value, 10),
                  decimales_precio: parseInt(decPrecio.value, 10),
                  decimales_parcial: parseInt(decPrecio.value, 10),
                  modo: modo.value,
                },
                gastos_generales_pct: gg.value,
                utilidad_pct: utilidad.value,
                impuesto: { nombre: impuestoNombre.value, tasa: impuestoTasa.value },
                exigir_lamina: exigirLamina.checked,
                bloquear_dimension_incompatible: bloquearDim.checked,
                regimen: regimen.value,
              },
            });
            await refrescarProyecto();
            exito('Reglas guardadas. El metrado se recalcula con ellas.');
          } catch (err) { avisoError(err.message); }
          e.target.disabled = false;
        },
      }, icono('guardar'), 'Guardar reglas'))));
}

async function panelTablas() {
  const { tablas } = await api.obtener('/referencia/tablas');
  return panel('Fuentes técnicas cargadas', el('div', {},
    el('p', { class: 'chico suave', estilo: { marginTop: 0 } },
      'Todo dato numérico que no sea una medida del proyecto vive en estas tablas y viaja con '
      + 'su fuente. Un número sin fuente no entra al motor.'),
    el('div', { class: 'tabla-envoltura' },
      el('table', { class: 'tabla densa' },
        el('thead', {}, el('tr', {},
          el('th', {}, 'Tabla'), el('th', { class: 'num' }, 'Filas'),
          el('th', { class: 'num' }, 'Verificadas'), el('th', { class: 'num' }, 'Tamaño'))),
        el('tbody', {}, ...tablas.map((t) => el('tr', {},
          el('td', { class: 'fuerte' }, t.nombre.replace(/_/g, ' ')),
          el('td', { class: 'num mono' }, num(t.filas, 0)),
          el('td', { class: 'num mono' },
            t.verificadas === t.filas
              ? chip(`${t.verificadas}`, 'ok')
              : chip(`${t.verificadas}`, 'alerta')),
          el('td', { class: 'num mono apagado' }, `${t.tamano_kb} KB`)))))));
}
