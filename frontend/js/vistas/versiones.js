// Versiones del metrado y comparación entre dos de ellas.

import { api } from '../core/api.js';
import { estado, puede, refrescarProyecto } from '../core/estado.js';
import { metrado, fechaHora } from '../core/fmt.js';
import {
  el, vaciar, icono, cargando, vacio, chip, panel, campo, modal,
  avisoCaja, exito, aviso, error as avisoError,
} from '../ui/base.js';

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);

  const zonaComparacion = el('div', { class: 'mt2' });

  const versionA = el('select', {},
    ...estado.versiones.map((v) => el('option', { value: v.id }, v.nombre)));
  const versionB = el('select', {},
    ...estado.versiones.map((v) => el('option', {
      value: v.id, selected: v.id === estado.versionId,
    }, v.nombre)));

  cuerpo.append(
    el('div', { class: 'fila entre mb2' },
      el('div', {},
        el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
          'Versiones'),
        el('p', { class: 'suave', estilo: { margin: 0 } },
          `${estado.versiones.length} versión(es) del metrado`)),
      puede('crear') ? el('button', {
        class: 'btn primario', onclick: () => nuevaVersion(proyectoId),
      }, icono('mas'), 'Nueva versión') : null),

    avisoCaja('info', 'Al crear una versión nueva, la vigente se congela con una copia completa '
      + 'del metrado. Esa copia es la que permite comparar meses después sin arqueología.'),

    panel('Historial de versiones', el('div', { class: 'tabla-envoltura' },
      el('table', { class: 'tabla' },
        el('thead', {}, el('tr', {},
          el('th', {}, 'Versión'), el('th', {}, 'Descripción'), el('th', {}, 'Estado'),
          el('th', {}, 'Creada'), el('th', {}))),
        el('tbody', {}, ...estado.versiones.map((v) => el('tr', {},
          el('td', { class: 'fuerte' }, v.nombre),
          el('td', { class: 'suave' }, v.descripcion || '—'),
          el('td', {}, chip(v.estado, v.estado === 'congelada' ? 'ok'
            : v.estado === 'aprobada' ? 'ok' : '')),
          el('td', { class: 'chico apagado' }, fechaHora(v.creado_en)),
          el('td', { class: 'centro' },
            v.id === estado.versionId ? chip('activa', 'acento') : el('button', {
              class: 'btn chico',
              onclick: () => { estado.versionId = v.id; exito(`Trabajando sobre ${v.nombre}.`); },
            }, 'Activar'))))))),

    el('div', { class: 'panel mt2' },
      el('div', { class: 'panel-cabecera' },
        el('h2', {}, 'Comparar versiones'),
        el('div', { class: 'crecer' })),
      el('div', { class: 'panel-cuerpo' },
        el('div', { class: 'fila-campos' },
          campo('Versión de referencia (A)', versionA),
          campo('Versión a comparar (B)', versionB),
          el('div', { class: 'campo' },
            el('label', {}, ' '),
            el('button', {
              class: 'btn primario',
              onclick: () => comparar(proyectoId, versionA.value, versionB.value, zonaComparacion),
            }, icono('versiones'), 'Comparar'))))),

    zonaComparacion);

  if (estado.versiones.length >= 2) {
    await comparar(proyectoId, estado.versiones[estado.versiones.length - 2].id,
      versionB.value, zonaComparacion);
  }
}

async function comparar(proyectoId, a, b, zona) {
  if (!a || !b) return aviso('Elija las dos versiones.', 'alerta');
  if (a === b) return aviso('Elija dos versiones distintas.', 'alerta');
  vaciar(zona).append(cargando());
  try {
    const datos = await api.obtener(
      `/proyectos/${proyectoId}/versiones/comparar?a=${a}&b=${b}`);
    const r = datos.resumen;

    if (!datos.comparacion.length) {
      vaciar(zona).append(vacio({
        icono: 'check', titulo: 'Las dos versiones son idénticas',
        mensaje: 'No hay diferencias de metrado entre ambas.',
      }));
      return;
    }

    vaciar(zona).append(
      el('div', { class: 'rejilla c3 mb2' },
        el('div', { class: 'kpi alerta' },
          el('span', { class: 'etiqueta' }, 'Modificadas'),
          el('span', { class: 'valor' }, String(r.modificadas))),
        el('div', { class: 'kpi ok' },
          el('span', { class: 'etiqueta' }, 'Agregadas'),
          el('span', { class: 'valor' }, String(r.agregadas))),
        el('div', { class: 'kpi peligro' },
          el('span', { class: 'etiqueta' }, 'Eliminadas'),
          el('span', { class: 'valor' }, String(r.eliminadas)))),

      el('div', { class: 'panel' },
        el('div', { class: 'panel-cabecera' },
          el('h2', {}, 'Diferencias partida por partida'),
          el('div', { class: 'crecer' }),
          el('button', {
            class: 'btn chico',
            onclick: () => api.descargar(
              `/proyectos/${proyectoId}/exportar/comparacion?formato=xlsx`
              + `&version_id=${b}&comparar_con=${a}`),
          }, icono('descargar'), 'Exportar')),
        el('div', { class: 'tabla-envoltura' },
          el('table', { class: 'tabla densa' },
            el('thead', {}, el('tr', {},
              el('th', {}, 'Ítem'), el('th', {}, 'Partida'), el('th', { class: 'centro' }, 'Und.'),
              el('th', { class: 'num' }, 'Versión A'), el('th', { class: 'num' }, 'Versión B'),
              el('th', { class: 'num' }, 'Diferencia'), el('th', {}, 'Estado'))),
            el('tbody', {}, ...datos.comparacion.map((c) => el('tr', {},
              el('td', { class: 'codigo' }, c.item),
              el('td', {}, c.descripcion),
              el('td', { class: 'centro' }, c.unidad || '—'),
              el('td', { class: 'num' }, c.metrado_a ? metrado(c.metrado_a) : '—'),
              el('td', { class: 'num' }, c.metrado_b ? metrado(c.metrado_b) : '—'),
              el('td', {
                class: 'num fuerte',
                estilo: {
                  color: c.diferencia && parseFloat(c.diferencia) > 0 ? 'var(--peligro)'
                    : c.diferencia && parseFloat(c.diferencia) < 0 ? 'var(--ok)' : '',
                },
              }, c.diferencia ? metrado(c.diferencia) : '—'),
              el('td', {}, chip(c.estado,
                c.estado === 'agregada' ? 'ok' : c.estado === 'eliminada' ? 'peligro' : 'alerta')))))))));
  } catch (e) {
    vaciar(zona).append(avisoCaja('peligro', e.message));
  }
}

function nuevaVersion(proyectoId) {
  const nombre = el('input', { type: 'text', placeholder: `v${estado.versiones.length + 1}` });
  const descripcion = el('textarea', { placeholder: 'Qué cambia en esta versión' });
  const copiar = el('input', { type: 'checkbox', checked: true });

  const control = modal({
    titulo: 'Crear nueva versión',
    cuerpo: el('div', {},
      avisoCaja('alerta', 'La versión vigente quedará congelada: no se podrá seguir editando. '
        + 'Se guarda una copia completa del metrado para poder compararla después.'),
      el('div', { class: 'mt2' }, campo('Nombre', nombre)),
      campo('Descripción', descripcion),
      el('label', { class: 'interruptor' }, copiar, el('span', { class: 'pista' }),
        el('span', {}, 'Copiar el metrado actual a la versión nueva'))),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          try {
            await api.crear(`/proyectos/${proyectoId}/versiones`, {
              nombre: nombre.value.trim() || null,
              descripcion: descripcion.value.trim() || null,
              copiar_metrados: copiar.checked,
            });
            control.cerrar();
            await refrescarProyecto();
            exito('Versión creada.');
            location.reload();
          } catch (e) { avisoError(e.message); }
        },
      }, icono('check'), 'Crear versión'),
    ],
  });
}
