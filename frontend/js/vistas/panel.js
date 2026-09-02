// Panel general: proyectos recientes, avance por especialidad, pendientes y alertas.

import { api } from '../core/api.js';
import { estado } from '../core/estado.js';
import { moneda, num, pct, haceCuanto, metrado } from '../core/fmt.js';
import { el, icono, cargando, vacio, barra, chip, panel, puntoEspecialidad } from '../ui/base.js';
import { ir } from '../app.js';

export async function render(contenedor) {
  const cuerpo = el('div', { class: 'contenido' });
  contenedor.append(cuerpo);
  cuerpo.append(cargando('Cargando sus proyectos…'));

  const { proyectos } = await api.obtener('/proyectos');
  cuerpo.replaceChildren();

  if (!proyectos.length) {
    cuerpo.append(vacio({
      icono: 'proyectos',
      titulo: 'Todavía no hay proyectos',
      mensaje: 'Cree su primer proyecto para empezar a metrar. Puede partir de una '
        + 'plantilla con las partidas de la norma ya organizadas por especialidad.',
      acciones: [
        el('button', { class: 'btn primario', onclick: () => ir('/nuevo') },
          icono('mas'), 'Crear proyecto'),
        el('button', { class: 'btn', onclick: () => ir('/catalogo') },
          icono('catalogo'), 'Ver el catálogo de partidas'),
      ],
    }));
    return;
  }

  const activos = proyectos.filter((p) => p.estado === 'activo');
  const totalCosto = activos.reduce((s, p) => s + parseFloat(p.resumen?.costo_directo || 0), 0);
  const totalPartidas = activos.reduce((s, p) => s + (p.resumen?.conteo?.partidas || 0), 0);
  const metradas = activos.reduce((s, p) => s + (p.resumen?.conteo?.con_metrado || 0), 0);
  const pendientes = totalPartidas - metradas;
  const conProblema = activos.reduce(
    (s, p) => s + (p.resumen?.conteo?.incompletas || 0) + (p.resumen?.conteo?.con_error || 0), 0);

  cuerpo.append(
    el('div', { class: 'fila entre mb2' },
      el('div', {},
        el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
          `Hola, ${(estado.usuario?.nombre || '').split(' ')[0] || 'bienvenido'}`),
        el('p', { class: 'suave', estilo: { margin: 0 } },
          `${activos.length} proyecto(s) activo(s) · ${totalPartidas} partidas en total`)),
      el('div', { class: 'fila' },
        el('button', { class: 'btn', onclick: () => ir('/catalogo') },
          icono('catalogo'), 'Catálogo'),
        el('button', { class: 'btn primario', onclick: () => ir('/nuevo') },
          icono('mas'), 'Nuevo proyecto'))),

    el('div', { class: 'rejilla c4 mb2' },
      indicador('Presupuesto estimado', moneda(totalCosto), 'Costo directo de todos los proyectos activos'),
      indicador('Avance del metrado',
        pct(totalPartidas ? (metradas / totalPartidas) * 100 : 0),
        `${metradas} de ${totalPartidas} partidas con sustento`,
        totalPartidas && metradas / totalPartidas > 0.8 ? 'ok' : ''),
      indicador('Partidas pendientes', num(pendientes, 0),
        'Sin ninguna fila de metrado', pendientes ? 'alerta' : 'ok'),
      indicador('Filas con problema', num(conProblema, 0),
        'Datos faltantes o errores de cálculo', conProblema ? 'peligro' : 'ok')),

    el('div', { class: 'rejilla', estilo: { gridTemplateColumns: '1.6fr 1fr' } },
      panel('Proyectos recientes', tarjetasProyectos(activos), [
        el('button', { class: 'btn chico', onclick: () => ir('/proyectos') }, 'Ver todos'),
      ]),
      el('div', { class: 'col' },
        panel('Accesos rápidos', accesosRapidos(activos)),
        panel('Avance por especialidad', avanceEspecialidades(activos)))),
  );
}

function indicador(etiqueta, valor, nota, tipo = '') {
  return el('div', { class: `kpi ${tipo}` },
    el('span', { class: 'etiqueta' }, etiqueta),
    el('span', { class: 'valor' + (String(valor).length > 11 ? ' chico' : '') }, valor),
    el('span', { class: 'nota' }, nota));
}

function tarjetasProyectos(proyectos) {
  const contenedor = el('div', { class: 'col', estilo: { gap: '10px' } });
  for (const p of proyectos.slice(0, 8)) {
    const r = p.resumen || {};
    const avance = r.avance_pct || 0;
    contenedor.append(el('div', {
      class: 'panel',
      estilo: { cursor: 'pointer', boxShadow: 'none' },
      onclick: () => ir(`/proyecto/${p.id}/metrados`),
    },
      el('div', { class: 'panel-cuerpo', estilo: { padding: '13px 15px' } },
        el('div', { class: 'fila entre mb1' },
          el('div', { estilo: { minWidth: 0 } },
            el('div', { class: 'fuerte', estilo: { fontSize: '13.5px' } }, p.nombre),
            el('div', { class: 'chico apagado mono' },
              `${p.codigo} · ${p.tipo} · ${p.pisos} piso(s) · ${p.pais}`)),
          el('div', { estilo: { textAlign: 'right' } },
            el('div', { class: 'fuerte mono' }, moneda(r.costo_directo)),
            el('div', { class: 'chico apagado' }, haceCuanto(p.actualizado_en)))),
        el('div', { class: 'fila', estilo: { gap: '12px' } },
          el('div', { class: 'crecer' }, barra(avance)),
          el('span', { class: 'chico mono nowrap' }, `${pct(avance)} metrado`),
          chip(`${r.conteo?.partidas || 0} partidas`),
          (r.conteo?.observadas || 0) > 0 ? chip(`${r.conteo.observadas} observadas`, 'alerta') : null,
          (r.conteo?.incompletas || 0) > 0 ? chip(`${r.conteo.incompletas} incompletas`, 'peligro') : null))));
  }
  return contenedor;
}

function accesosRapidos(proyectos) {
  const ultimo = proyectos[0];
  const acciones = [
    ['mas', 'Crear proyecto', () => ir('/nuevo')],
    ultimo && ['plano', 'Importar planos', () => ir(`/proyecto/${ultimo.id}/planos`)],
    ultimo && ['planilla', 'Agregar partidas', () => ir(`/proyecto/${ultimo.id}/metrados`)],
    ultimo && ['calidad', 'Revisar calidad', () => ir(`/proyecto/${ultimo.id}/calidad`)],
    ['catalogo', 'Buscar en el catálogo', () => ir('/catalogo')],
  ].filter(Boolean);

  return el('div', { class: 'col', estilo: { gap: '6px' } },
    ...acciones.map(([ic, texto, accion]) => el('button', {
      class: 'btn', estilo: { justifyContent: 'flex-start', width: '100%' },
      onclick: accion,
    }, icono(ic), texto)));
}

function avanceEspecialidades(proyectos) {
  const acumulado = new Map();
  for (const p of proyectos) {
    for (const e of p.resumen?.por_especialidad || []) {
      const actual = acumulado.get(e.clave) || {
        ...e, partidas: 0, con_metrado: 0, costo: 0,
      };
      actual.partidas += e.partidas;
      actual.con_metrado += e.con_metrado;
      actual.costo += parseFloat(e.costo || 0);
      acumulado.set(e.clave, actual);
    }
  }
  const filas = [...acumulado.values()];
  if (!filas.length) {
    return el('p', { class: 'apagado chico', estilo: { margin: 0 } },
      'Cuando agregue partidas verá aquí el avance de cada especialidad.');
  }
  return el('div', { class: 'col', estilo: { gap: '11px' } },
    ...filas.map((e) => el('div', {},
      el('div', { class: 'fila entre chico mb1' },
        el('span', { class: 'fila', estilo: { gap: '7px' } },
          puntoEspecialidad(e.color), el('span', { class: 'fuerte' }, e.nombre)),
        el('span', { class: 'mono apagado' }, `${e.con_metrado}/${e.partidas}`)),
      barra(e.partidas ? (e.con_metrado / e.partidas) * 100 : 0, e.color))));
}
