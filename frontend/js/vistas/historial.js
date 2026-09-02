// Historial de cambios y copia de seguridad.

import { api } from '../core/api.js';
import { estado } from '../core/estado.js';
import { fechaHora, haceCuanto } from '../core/fmt.js';
import { el, vaciar, icono, cargando, vacio, chip, panel, avisoCaja } from '../ui/base.js';

const COLOR_ACCION = {
  crear: 'ok', editar: '', eliminar: 'peligro', aprobar: 'ok',
  revisar: 'info', importar: 'info', desbloquear: 'alerta',
};

let filtroEntidad = '';

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);
  cuerpo.append(cargando());

  const datos = await api.obtener(`/proyectos/${proyectoId}/historial?limite=400`);
  const entidades = [...new Set(datos.historial.map((h) => h.entidad))].sort();

  const lista = el('div', { class: 'panel' });

  const dibujar = () => {
    const visibles = datos.historial.filter((h) => !filtroEntidad || h.entidad === filtroEntidad);
    vaciar(lista);
    if (!visibles.length) {
      lista.append(vacio({
        icono: 'reloj', titulo: 'Sin movimientos registrados',
        mensaje: 'Cada cambio en el proyecto queda anotado aquí con su autor y su fecha.',
      }));
      return;
    }
    for (const h of visibles) {
      lista.append(el('div', {
        estilo: {
          padding: '11px 15px', borderBottom: '1px solid var(--panel-borde)',
          display: 'flex', gap: '12px', alignItems: 'flex-start',
        },
      },
        el('div', {
          estilo: {
            width: '30px', height: '30px', borderRadius: '8px', flexShrink: 0,
            background: 'var(--fondo-3)', display: 'grid', placeItems: 'center',
            color: 'var(--texto-2)',
          },
        }, icono(iconoDe(h.entidad))),
        el('div', { class: 'crecer', estilo: { minWidth: 0 } },
          el('div', { class: 'fila entre' },
            el('span', { class: 'fuerte chico' }, h.frase),
            el('span', { class: 'chico apagado nowrap' }, haceCuanto(h.fecha))),
          el('div', { class: 'chico suave' }, h.resumen || ''),
          h.antes || h.despues
            ? el('details', { class: 'chico mt1' },
                el('summary', { estilo: { cursor: 'pointer', color: 'var(--texto-3)' } },
                  'Ver el detalle del cambio'),
                el('div', { class: 'mono', estilo: { fontSize: '11px', marginTop: '6px' } },
                  ...Object.keys({ ...(h.antes || {}), ...(h.despues || {}) }).map((k) =>
                    el('div', {},
                      el('span', { class: 'apagado' }, `${k}: `),
                      el('span', { estilo: { textDecoration: 'line-through', opacity: .6 } },
                        String(h.antes?.[k] ?? '—')),
                      ' → ',
                      el('strong', {}, String(h.despues?.[k] ?? '—'))))))
            : null),
        chip(h.accion, COLOR_ACCION[h.accion] || '')));
    }
  };

  cuerpo.replaceChildren(
    el('div', { class: 'fila entre mb2 envuelve' },
      el('div', {},
        el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
          'Historial de cambios'),
        el('p', { class: 'suave', estilo: { margin: 0 } },
          `${datos.historial.length} movimiento(s) registrados`)),
      el('div', { class: 'fila' },
        el('select', {
          estilo: { width: 'auto' },
          onchange: (e) => { filtroEntidad = e.target.value; dibujar(); },
        },
          el('option', { value: '' }, 'Todo el proyecto'),
          ...entidades.map((x) => el('option', { value: x }, x.replace(/_/g, ' ')))),
        el('button', {
          class: 'btn',
          onclick: () => api.descargar(`/proyectos/${proyectoId}/respaldo`),
        }, icono('descargar'), 'Copia de seguridad'))),

    avisoCaja('info', 'El registro de auditoría no se puede editar ni borrar: es lo que permite '
      + 'responder «¿quién cambió esta cantidad y cuándo?» meses después.'),

    el('div', { class: 'mt2' }, lista));

  dibujar();
}

function iconoDe(entidad) {
  return {
    proyecto: 'proyectos', item: 'planilla', medicion: 'planilla', ubicacion: 'edificio',
    elemento: 'edificio', archivo: 'archivo', plano: 'plano', version: 'versiones',
    observacion: 'alerta', usuario: 'usuarios', partida_catalogo: 'catalogo',
    marcado: 'regla', apu: 'balanza', alerta: 'calidad', reporte: 'reporte',
  }[entidad] || 'info';
}
