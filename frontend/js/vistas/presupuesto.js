// Presupuesto por partidas, resumen por especialidad, insumos, curva S y
// control de adicionales y deductivos.

import { api } from '../core/api.js';
import { estado, puede } from '../core/estado.js';
import { moneda, metrado, num, pct, parsear } from '../core/fmt.js';
import {
  el, vaciar, icono, cargando, vacio, chip, panel, avisoCaja, barra,
  puntoEspecialidad, exito, error as avisoError,
} from '../ui/base.js';
import { ir } from '../app.js';

let pestana = 'presupuesto';

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);

  const zona = el('div');
  const pestanas = el('div', { class: 'pestanas mb2' },
    ...[
      ['presupuesto', 'Presupuesto', 'dinero'],
      ['especialidades', 'Por especialidad', 'panel'],
      ['insumos', 'Insumos', 'catalogo'],
      ['curva', 'Curva S', 'versiones'],
      ['adicionales', 'Adicionales y deductivos', 'balanza'],
    ].map(([clave, etiqueta, ic]) => el('button', {
      class: pestana === clave ? 'activo' : '',
      onclick: () => { pestana = clave; dibujar(); },
    }, icono(ic), etiqueta)));

  cuerpo.append(
    el('div', { class: 'fila entre mb2' },
      el('h1', { estilo: { margin: 0, fontSize: '20px', letterSpacing: '-.4px' } }, 'Presupuesto'),
      el('div', { class: 'fila' },
        el('button', {
          class: 'btn',
          onclick: () => api.descargar(`/proyectos/${proyectoId}/exportar/presupuesto?formato=xlsx`),
        }, icono('descargar'), 'Excel'),
        el('button', {
          class: 'btn',
          onclick: () => api.descargar(`/proyectos/${proyectoId}/exportar/presupuesto?formato=pdf`),
        }, icono('reporte'), 'PDF'))),
    pestanas, zona);

  async function dibujar() {
    [...pestanas.children].forEach((b, i) => b.classList.toggle('activo',
      ['presupuesto', 'especialidades', 'insumos', 'curva', 'adicionales'][i] === pestana));
    vaciar(zona).append(cargando());
    try {
      if (pestana === 'presupuesto') vaciar(zona).append(await vistaPresupuesto(proyectoId));
      if (pestana === 'especialidades') vaciar(zona).append(await vistaEspecialidades(proyectoId));
      if (pestana === 'insumos') vaciar(zona).append(await vistaInsumos(proyectoId));
      if (pestana === 'curva') vaciar(zona).append(await vistaCurva(proyectoId));
      if (pestana === 'adicionales') vaciar(zona).append(await vistaAdicionales(proyectoId));
    } catch (e) {
      vaciar(zona).append(avisoCaja('peligro', e.message));
    }
  }
  await dibujar();
}

async function vistaPresupuesto(proyectoId) {
  const datos = await api.obtener(`/proyectos/${proyectoId}/presupuesto`
    + (estado.versionId ? `?version_id=${estado.versionId}` : ''));
  const r = datos.resumen;

  const cuerpo = el('tbody');
  const recorrer = (nodos) => {
    for (const n of nodos) {
      const esTitulo = n.tipo === 'titulo';
      cuerpo.append(el('tr', { class: esTitulo ? 'fila-titulo' : '' },
        el('td', { class: 'codigo' }, n.item),
        el('td', { class: 'codigo' }, n.codigo || ''),
        el('td', { estilo: { paddingLeft: `${8 + (n.nivel - 1) * 14}px` } },
          esTitulo ? n.descripcion.toUpperCase() : n.descripcion),
        el('td', { class: 'centro' }, n.unidad || ''),
        el('td', { class: 'num' }, esTitulo ? '' : metrado(n.metrado)),
        el('td', { class: 'num' }, esTitulo ? '' : (n.precio_unitario
          ? num(n.precio_unitario) : el('span', { class: 'apagado' }, 'sin precio'))),
        el('td', { class: 'num fuerte' }, moneda(n.parcial)),
        el('td', { class: 'centro' }, esTitulo ? '' : el('button', {
          class: 'btn chico fantasma', title: 'Análisis de precios unitarios',
          onclick: () => ir(`/proyecto/${proyectoId}/apu/${n.id}`),
        }, icono('balanza')))));
      recorrer(n.hijos || []);
    }
  };
  recorrer(datos.items);

  const lineasResumen = [
    ['Costo directo', r.costo_directo, true],
    [`Gastos generales (${r.gastos_generales_pct}%)`, r.gastos_generales, false],
    [`Utilidad (${r.utilidad_pct}%)`, r.utilidad, false],
    ['Subtotal', r.subtotal, true],
    [`${r.nombre_impuesto} (${r.impuesto_pct}%)`, r.impuesto, false],
    ['TOTAL DEL PRESUPUESTO', r.total, true],
  ];

  return el('div', {},
    datos.total_sin_precio ? avisoCaja('alerta', el('div', {},
      el('strong', {}, `${datos.total_sin_precio} partida(s) sin precio unitario. `),
      'El presupuesto está incompleto: esas partidas suman cero. '
      + 'Asigne precios o genere sus análisis de precios unitarios.')) : null,

    el('div', { class: 'panel mt2' },
      el('div', { class: 'tabla-envoltura' },
        el('table', { class: 'tabla densa' },
          el('thead', {}, el('tr', {},
            el('th', {}, 'Ítem'), el('th', {}, 'Código'), el('th', {}, 'Descripción'),
            el('th', { class: 'centro' }, 'Und.'), el('th', { class: 'num' }, 'Metrado'),
            el('th', { class: 'num' }, `P.U. (${datos.proyecto.moneda})`),
            el('th', { class: 'num' }, 'Parcial'), el('th', {}))),
          cuerpo))),

    el('div', { class: 'panel mt2', estilo: { maxWidth: '460px', marginLeft: 'auto' } },
      el('div', { class: 'panel-cuerpo' },
        ...lineasResumen.map(([etiqueta, valor, fuerte]) => el('div', {
          class: 'fila entre',
          estilo: {
            padding: '7px 0',
            borderTop: fuerte ? '1px solid var(--panel-borde)' : 'none',
            fontWeight: fuerte ? 700 : 400,
          },
        },
          el('span', { class: fuerte ? '' : 'suave' }, etiqueta),
          el('span', {
            class: 'mono',
            estilo: etiqueta.startsWith('TOTAL') ? { color: 'var(--ok)', fontSize: '16px' } : {},
          }, moneda(valor)))))));
}

async function vistaEspecialidades(proyectoId) {
  const datos = await api.obtener(`/proyectos/${proyectoId}/presupuesto`);
  const total = datos.por_especialidad.reduce((s, e) => s + parseFloat(e.costo), 0) || 1;
  return el('div', { class: 'rejilla c2' },
    panel('Costo por especialidad', el('div', { class: 'col', estilo: { gap: '14px' } },
      ...datos.por_especialidad.map((e) => el('div', {},
        el('div', { class: 'fila entre mb1' },
          el('span', { class: 'fila', estilo: { gap: '8px' } },
            puntoEspecialidad(e.color), el('span', { class: 'fuerte' }, e.nombre)),
          el('span', { class: 'mono' }, moneda(e.costo))),
        barra((parseFloat(e.costo) / total) * 100, e.color),
        el('div', { class: 'chico apagado mt1' },
          `${e.con_metrado} de ${e.partidas} partidas metradas · `
          + `${pct((parseFloat(e.costo) / total) * 100)} del presupuesto`))))),
    panel('Avance del metrado', el('div', { class: 'col', estilo: { gap: '14px' } },
      ...datos.por_especialidad.map((e) => el('div', {},
        el('div', { class: 'fila entre mb1' },
          el('span', { class: 'fuerte chico' }, e.nombre),
          el('span', { class: 'mono chico' }, pct(e.avance_pct))),
        barra(e.avance_pct, e.avance_pct >= 100 ? 'var(--ok)' : e.color))))));
}

async function vistaInsumos(proyectoId) {
  const datos = await api.obtener(`/proyectos/${proyectoId}/insumos`);
  if (!datos.insumos.length) {
    return vacio({
      icono: 'catalogo', titulo: 'Todavía no hay insumos',
      mensaje: 'La lista de insumos se arma con los análisis de precios unitarios de cada '
        + 'partida. Genere al menos un APU para verla.',
    });
  }
  return el('div', {},
    el('div', { class: 'rejilla c4 mb2' },
      ...Object.entries(datos.por_tipo).map(([tipo, valor]) => el('div', { class: 'kpi' },
        el('span', { class: 'etiqueta' }, datos.nombres_tipo[tipo] || tipo),
        el('span', { class: 'valor chico mono' }, moneda(valor))))),
    el('div', { class: 'panel' }, el('div', { class: 'tabla-envoltura' },
      el('table', { class: 'tabla densa' },
        el('thead', {}, el('tr', {},
          el('th', {}, 'Tipo'), el('th', {}, 'Insumo'), el('th', { class: 'centro' }, 'Und.'),
          el('th', { class: 'num' }, 'Cantidad'), el('th', { class: 'num' }, 'Precio'),
          el('th', { class: 'num' }, 'Parcial'))),
        el('tbody', {}, ...datos.insumos.map((i) => el('tr', {},
          el('td', {}, chip(i.tipo)),
          el('td', {}, i.descripcion),
          el('td', { class: 'centro' }, i.unidad),
          el('td', { class: 'num' }, num(i.cantidad, 4)),
          el('td', { class: 'num' }, num(i.precio)),
          el('td', { class: 'num fuerte' }, moneda(i.parcial)))))))));
}

async function vistaCurva(proyectoId) {
  const meses = 12;
  const datos = await api.obtener(`/proyectos/${proyectoId}/curva-s?meses=${meses}`);
  const maximo = Math.max(...datos.meses.map((m) => parseFloat(m.valorizacion)), 1);

  const grafico = el('div', {
    estilo: {
      display: 'flex', alignItems: 'flex-end', gap: '6px', height: '220px',
      padding: '16px 0', borderBottom: '1px solid var(--panel-borde)',
    },
  });
  for (const m of datos.meses) {
    const altura = (parseFloat(m.valorizacion) / maximo) * 100;
    grafico.append(el('div', {
      class: 'crecer',
      estilo: { display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', height: '100%' },
      title: `Mes ${m.mes}: ${moneda(m.valorizacion)} (acumulado ${pct(m.avance_pct)})`,
    },
      el('div', {
        estilo: {
          height: `${altura}%`, background: 'var(--acento)', borderRadius: '4px 4px 0 0',
          minHeight: '2px', position: 'relative',
        },
      },
        el('div', {
          estilo: {
            position: 'absolute', top: '-18px', left: 0, right: 0, textAlign: 'center',
            fontSize: '9.5px', color: 'var(--texto-3)', fontFamily: 'var(--mono)',
          },
        }, pct(m.avance_pct, 0))),
      el('div', { class: 'centrado chico apagado', estilo: { marginTop: '5px' } }, `M${m.mes}`)));
  }

  return el('div', {},
    avisoCaja('info', datos.nota),
    panel('Cronograma valorizado', el('div', {}, grafico,
      el('div', { class: 'tabla-envoltura mt2' },
        el('table', { class: 'tabla densa' },
          el('thead', {}, el('tr', {},
            el('th', {}, 'Mes'), el('th', { class: 'num' }, 'Valorización'),
            el('th', { class: 'num' }, 'Acumulado'), el('th', { class: 'num' }, 'Avance'))),
          el('tbody', {}, ...datos.meses.map((m) => el('tr', {},
            el('td', {}, `Mes ${m.mes}`),
            el('td', { class: 'num' }, moneda(m.valorizacion)),
            el('td', { class: 'num' }, moneda(m.acumulado)),
            el('td', { class: 'num' }, pct(m.avance_pct))))))))));
}

async function vistaAdicionales(proyectoId) {
  const datos = await api.obtener(`/proyectos/${proyectoId}/adicionales`);
  if (!datos.filas.length) {
    return vacio({
      icono: 'balanza', titulo: 'Sin adicionales ni deductivos',
      mensaje: 'Registre la cantidad contratada en las partidas para comparar contra el '
        + 'metrado previsto y ver aquí las diferencias.',
    });
  }
  return el('div', {},
    el('div', { class: 'rejilla c3 mb2' },
      el('div', { class: 'kpi alerta' },
        el('span', { class: 'etiqueta' }, 'Adicionales'),
        el('span', { class: 'valor chico mono' }, moneda(datos.total_adicional))),
      el('div', { class: 'kpi ok' },
        el('span', { class: 'etiqueta' }, 'Deductivos'),
        el('span', { class: 'valor chico mono' }, moneda(datos.total_deductivo))),
      el('div', { class: 'kpi' },
        el('span', { class: 'etiqueta' }, 'Neto'),
        el('span', { class: 'valor chico mono' }, moneda(datos.neto)))),
    el('div', { class: 'panel' }, el('div', { class: 'tabla-envoltura' },
      el('table', { class: 'tabla densa' },
        el('thead', {}, el('tr', {},
          el('th', {}, 'Ítem'), el('th', {}, 'Partida'), el('th', { class: 'centro' }, 'Und.'),
          el('th', { class: 'num' }, 'Contratada'), el('th', { class: 'num' }, 'Prevista'),
          el('th', { class: 'num' }, 'Diferencia'), el('th', { class: 'num' }, 'Monto'),
          el('th', {}, 'Clase'))),
        el('tbody', {}, ...datos.filas.map((f) => el('tr', {},
          el('td', { class: 'codigo' }, f.item),
          el('td', {}, f.descripcion),
          el('td', { class: 'centro' }, f.unidad),
          el('td', { class: 'num' }, metrado(f.contratada)),
          el('td', { class: 'num' }, metrado(f.prevista)),
          el('td', { class: 'num' }, metrado(f.diferencia)),
          el('td', { class: 'num fuerte' }, moneda(f.monto)),
          el('td', {}, chip(f.clase, f.clase === 'adicional' ? 'alerta' : 'ok')))))))));
}
