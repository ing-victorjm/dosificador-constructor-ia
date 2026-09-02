// Reportes y exportaciones. Todo reporte lleva portada, filtros aplicados,
// versión, responsable, fecha y espacio de firmas.

import { api } from '../core/api.js';
import { estado } from '../core/estado.js';
import { el, icono, panel, campo, avisoCaja, chip, exito } from '../ui/base.js';

const DESCRIPCIONES = {
  metrados: 'Planilla de sustento completa: cada partida con sus filas, dimensiones y parciales. '
    + 'En Excel sale con fórmulas vivas (=PRODUCT), que es lo que exige una revisión.',
  resumen: 'Una línea por partida con su metrado total. Es el documento que se adjunta al '
    + 'expediente junto a la planilla.',
  presupuesto: 'Partidas con precio unitario y parcial, más el pie con gastos generales, '
    + 'utilidad e impuesto.',
  insumos: 'Consolidado de materiales, mano de obra y equipos de toda la obra.',
  acero: 'Cuadro de acero: despiece por marca, resumen por diámetro y peso total.',
  observaciones: 'Todas las observaciones del proyecto con su gravedad, estado y autor.',
  calidad: 'Informe del control de calidad: cada alerta con su explicación y cómo se corrige.',
  comparacion: 'Diferencias partida por partida entre dos versiones del metrado.',
  trazabilidad: 'De dónde sale cada cantidad: fila, cálculo, origen, lámina y responsable.',
};

const ICONOS = {
  metrados: 'planilla', resumen: 'reporte', presupuesto: 'dinero', insumos: 'catalogo',
  acero: 'edificio', observaciones: 'alerta', calidad: 'calidad',
  comparacion: 'versiones', trazabilidad: 'ojo',
};

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);

  const { reportes } = await api.obtener('/reportes');

  const especialidadFiltro = el('select', {},
    el('option', { value: '' }, 'Todas las especialidades'),
    ...estado.referencia.especialidades.map((e) => el('option', { value: e.clave }, e.nombre)));
  const soloObservadas = el('input', { type: 'checkbox' });
  const versionComparar = el('select', {},
    el('option', { value: '' }, 'Elija la versión de referencia'),
    ...estado.versiones.map((v) => el('option', { value: v.id }, v.nombre)));

  const descargar = (clave, formato) => {
    const p = new URLSearchParams({ formato });
    if (estado.versionId) p.set('version_id', estado.versionId);
    if (especialidadFiltro.value) p.set('especialidad', especialidadFiltro.value);
    if (soloObservadas.checked) p.set('solo_observadas', 'true');
    if (clave === 'comparacion' && versionComparar.value) p.set('comparar_con', versionComparar.value);
    api.descargar(`/proyectos/${proyectoId}/exportar/${clave}?${p}`);
    exito('Generando el archivo…');
  };

  cuerpo.append(
    el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
      'Reportes y exportaciones'),
    el('p', { class: 'suave mb2', estilo: { marginTop: 0 } },
      'Todos los reportes llevan portada con datos del proyecto, filtros aplicados, versión, '
      + 'responsable, fecha y espacio para firmas.'),

    panel('Filtros', el('div', {},
      el('div', { class: 'fila-campos' },
        campo('Especialidad', especialidadFiltro),
        campo('Versión de referencia (para comparar)', versionComparar)),
      el('label', { class: 'interruptor mt1' },
        soloObservadas, el('span', { class: 'pista' }),
        el('span', {}, 'Exportar únicamente las partidas observadas')))),

    el('div', { class: 'rejilla auto mt2' },
      ...reportes.map((r) => el('div', { class: 'panel' },
        el('div', { class: 'panel-cuerpo' },
          el('div', { class: 'fila mb1' },
            el('div', {
              class: 'icono',
              estilo: {
                width: '34px', height: '34px', borderRadius: '9px',
                background: 'var(--acento-suave)', color: 'var(--acento)',
                display: 'grid', placeItems: 'center',
              },
            }, icono(ICONOS[r.clave] || 'reporte')),
            el('div', { class: 'crecer' },
              el('div', { class: 'fuerte' }, r.nombre))),
          el('p', { class: 'chico suave', estilo: { margin: '0 0 12px', lineHeight: '1.55' } },
            DESCRIPCIONES[r.clave] || ''),
          el('div', { class: 'fila' },
            ...r.formatos.map((f) => el('button', {
              class: `btn chico ${f === 'xlsx' ? 'primario' : ''}`,
              onclick: () => descargar(r.clave, f),
            }, icono('descargar'), f.toUpperCase())))))))
  );
}
