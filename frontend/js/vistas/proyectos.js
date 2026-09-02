// Lista de proyectos con filtros y acciones.

import { api } from '../core/api.js';
import { moneda, pct, fecha, haceCuanto } from '../core/fmt.js';
import { el, icono, cargando, vacio, chip, barra, confirmar, exito, error as avisoError } from '../ui/base.js';
import { ir } from '../app.js';

let filtro = '';
let soloActivos = true;

export async function render(contenedor) {
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);
  cuerpo.append(cargando());

  const { proyectos } = await api.obtener('/proyectos');
  cuerpo.replaceChildren();

  const lista = el('div');
  const dibujar = () => {
    const texto = filtro.toLowerCase();
    const visibles = proyectos.filter((p) =>
      (!soloActivos || p.estado === 'activo')
      && (!texto || `${p.nombre} ${p.codigo} ${p.cliente || ''} ${p.ubicacion_texto || ''}`
        .toLowerCase().includes(texto)));

    lista.replaceChildren();
    if (!visibles.length) {
      lista.append(vacio({
        icono: 'buscar',
        titulo: filtro ? 'Ningún proyecto coincide' : 'No hay proyectos',
        mensaje: filtro
          ? `No se encontró nada para «${filtro}». Pruebe con el código o el nombre del cliente.`
          : 'Cree su primer proyecto para empezar.',
        acciones: [el('button', { class: 'btn primario', onclick: () => ir('/nuevo') },
          icono('mas'), 'Crear proyecto')],
      }));
      return;
    }
    lista.append(el('div', { class: 'rejilla auto' }, ...visibles.map(tarjeta)));
  };

  cuerpo.append(
    el('div', { class: 'fila entre mb2 envuelve' },
      el('div', {},
        el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } }, 'Proyectos'),
        el('p', { class: 'suave', estilo: { margin: 0 } },
          `${proyectos.length} proyecto(s) en total`)),
      el('div', { class: 'fila' },
        el('label', { class: 'interruptor' },
          el('input', {
            type: 'checkbox', checked: soloActivos,
            onchange: (e) => { soloActivos = e.target.checked; dibujar(); },
          }),
          el('span', { class: 'pista' }),
          el('span', { class: 'chico' }, 'Solo activos')),
        el('input', {
          type: 'search', placeholder: 'Filtrar por nombre, código o cliente…',
          estilo: { width: '280px' },
          oninput: (e) => { filtro = e.target.value; dibujar(); },
        }),
        el('button', { class: 'btn primario', onclick: () => ir('/nuevo') },
          icono('mas'), 'Nuevo'))),
    lista);

  dibujar();

  function tarjeta(p) {
    const r = p.resumen || {};
    const conteo = r.conteo || {};
    return el('div', { class: 'panel' },
      el('div', {
        class: 'panel-cuerpo', estilo: { cursor: 'pointer' },
        onclick: () => ir(`/proyecto/${p.id}/metrados`),
      },
        el('div', { class: 'fila entre mb1' },
          chip(p.etapa, 'acento'),
          el('span', { class: 'chico apagado mono' }, p.codigo)),
        el('h3', { estilo: { margin: '2px 0 4px', fontSize: '15px', letterSpacing: '-.2px' } }, p.nombre),
        el('div', { class: 'chico apagado mb2' },
          [p.cliente, p.ubicacion_texto].filter(Boolean).join(' · ') || 'Sin cliente registrado'),

        el('div', { class: 'fila entre chico mb1' },
          el('span', { class: 'suave' }, 'Avance del metrado'),
          el('span', { class: 'mono fuerte' }, pct(r.avance_pct || 0))),
        barra(r.avance_pct || 0),

        el('div', { class: 'fila envuelve mt2', estilo: { gap: '6px' } },
          chip(`${conteo.partidas || 0} partidas`),
          conteo.observadas ? chip(`${conteo.observadas} observadas`, 'alerta') : null,
          conteo.incompletas ? chip(`${conteo.incompletas} incompletas`, 'peligro') : null,
          conteo.aprobadas ? chip(`${conteo.aprobadas} aprobadas`, 'ok') : null),

        el('div', { class: 'sep' }),
        el('div', { class: 'fila entre' },
          el('div', {},
            el('div', { class: 'chico apagado' }, 'Costo directo'),
            el('div', { class: 'fuerte mono' }, moneda(r.costo_directo))),
          el('div', { estilo: { textAlign: 'right' } },
            el('div', { class: 'chico apagado' }, `${p.pisos} piso(s) · ${p.sectores} sector(es)`),
            el('div', { class: 'chico apagado' }, haceCuanto(p.actualizado_en))))),

      el('div', { class: 'panel-cabecera', estilo: { borderTop: '1px solid var(--panel-borde)', borderBottom: 'none' } },
        el('button', { class: 'btn chico', onclick: () => ir(`/proyecto/${p.id}/metrados`) },
          icono('planilla'), 'Metrados'),
        el('button', { class: 'btn chico', onclick: () => ir(`/proyecto/${p.id}/planos`) },
          icono('plano'), 'Planos'),
        el('button', { class: 'btn chico', onclick: () => ir(`/proyecto/${p.id}/presupuesto`) },
          icono('dinero'), 'Presupuesto'),
        el('div', { class: 'crecer' }),
        el('button', {
          class: 'btn chico fantasma', title: 'Eliminar proyecto',
          onclick: async (e) => {
            e.stopPropagation();
            const ok = await confirmar({
              titulo: 'Eliminar proyecto',
              mensaje: `Se archivará «${p.nombre}» con todo su metrado.`,
              detalle: 'El proyecto deja de listarse pero no se borra de la base de datos: '
                + 'puede recuperarse desde el respaldo. El historial de cambios se conserva.',
              aceptar: 'Archivar', peligroso: true,
            });
            if (!ok) return;
            try {
              await api.borrar(`/proyectos/${p.id}`);
              exito('Proyecto archivado.');
              render(contenedor.replaceChildren() || contenedor);
            } catch (err) { avisoError(err.message); }
          },
        }, icono('borrar'))));
  }
}
