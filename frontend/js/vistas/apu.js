// Análisis de precios unitarios de una partida.

import { api } from '../core/api.js';
import { estado, puede } from '../core/estado.js';
import { moneda, num, metrado, parsear } from '../core/fmt.js';
import {
  el, vaciar, icono, cargando, vacio, chip, panel, avisoCaja,
  exito, aviso, error as avisoError,
} from '../ui/base.js';
import { ir } from '../app.js';

const TIPOS = { MO: 'Mano de obra', MAT: 'Materiales', EQ: 'Equipos', SC: 'Subcontratos' };

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const itemId = (params.resto || [])[0];
  const cuerpo = el('div', { class: 'contenido', estilo: { maxWidth: '1100px' } });
  contenedor.append(cuerpo);

  if (!itemId) {
    cuerpo.append(vacio({
      icono: 'balanza', titulo: 'Elija una partida',
      mensaje: 'Abra el presupuesto y pulse el icono de análisis en la partida que quiera detallar.',
      acciones: [el('button', {
        class: 'btn primario', onclick: () => ir(`/proyecto/${proyectoId}/presupuesto`),
      }, icono('dinero'), 'Ir al presupuesto')],
    }));
    return;
  }

  cuerpo.append(cargando());
  const datos = await api.obtener(`/items/${itemId}/apu`);
  const editable = puede('editar');
  let lineas = datos.apu.lineas.map((l) => ({ ...l }));
  if (!lineas.length) {
    lineas = [
      { tipo: 'MO', descripcion: 'Operario', unidad: 'hh', cuadrilla: '1', cantidad: '0', precio: '0', rendimiento: '' },
      { tipo: 'MAT', descripcion: '', unidad: 'und', cantidad: '0', precio: '0' },
      { tipo: 'EQ', descripcion: 'Herramientas manuales', unidad: 'pct', cantidad: '3', precio: '0' },
    ];
  }

  const zonaTabla = el('div');
  const zonaResumen = el('div');

  const rendimiento = el('input', {
    type: 'text', class: 'num', value: datos.apu.rendimiento || '',
    placeholder: 'p. ej. 25', disabled: !editable,
    estilo: { width: '110px' },
  });

  const dibujar = () => {
    const cuerpoTabla = el('tbody');
    for (const [i, l] of lineas.entries()) {
      const entrada = (clave, opciones = {}) => {
        const n = el('input', {
          type: 'text', value: l[clave] ?? '', disabled: !editable,
          class: opciones.texto ? 'texto' : '', placeholder: opciones.placeholder || '',
        });
        n.onchange = () => { l[clave] = n.value.trim(); dibujar(); };
        return n;
      };
      const selectorTipo = el('select', { disabled: !editable },
        ...Object.entries(TIPOS).map(([v, t]) => el('option', {
          value: v, selected: v === l.tipo,
        }, t)));
      selectorTipo.onchange = () => { l.tipo = selectorTipo.value; dibujar(); };

      cuerpoTabla.append(el('tr', {},
        el('td', { estilo: { width: '130px' } }, selectorTipo),
        el('td', {}, entrada('descripcion', { texto: true, placeholder: 'Insumo' })),
        el('td', { estilo: { width: '70px' } }, entrada('unidad')),
        el('td', { estilo: { width: '80px' } }, entrada('cuadrilla')),
        el('td', { estilo: { width: '95px' } }, entrada('cantidad')),
        el('td', { estilo: { width: '95px' } }, entrada('precio')),
        el('td', { class: 'parcial' }, num(l.parcial || 0)),
        el('td', { class: 'centro', estilo: { width: '40px' } },
          editable ? el('button', {
            class: 'btn chico fantasma',
            onclick: () => { lineas.splice(i, 1); dibujar(); },
          }, icono('borrar')) : null)));
    }

    vaciar(zonaTabla).append(
      el('div', { class: 'panel' },
        el('div', { class: 'tabla-envoltura' },
          el('table', { class: 'tabla densa planilla' },
            el('thead', {}, el('tr', {},
              el('th', {}, 'Tipo'), el('th', {}, 'Descripción'),
              el('th', {}, 'Und.'), el('th', {}, 'Cuadrilla'),
              el('th', { class: 'num' }, 'Cantidad'), el('th', { class: 'num' }, 'Precio'),
              el('th', { class: 'num' }, 'Parcial'), el('th', {}))),
            cuerpoTabla)),
        editable ? el('div', { class: 'panel-cuerpo' },
          el('button', {
            class: 'btn chico',
            onclick: () => {
              lineas.push({ tipo: 'MAT', descripcion: '', unidad: 'und', cantidad: '0', precio: '0' });
              dibujar();
            },
          }, icono('mas'), 'Agregar insumo')) : null));
  };

  const recalcular = async (guardar) => {
    try {
      const cuerpoEnvio = {
        lineas: lineas.map((l) => ({
          tipo: l.tipo, descripcion: l.descripcion || '(sin nombre)',
          unidad: l.unidad || 'und',
          cuadrilla: l.cuadrilla || null,
          cantidad: parsear(l.cantidad || '0'),
          precio: parsear(l.precio || '0'),
          rendimiento: rendimiento.value ? parsear(rendimiento.value) : null,
        })),
        aplicar_pu: true,
      };
      const r = await api.actualizar(`/items/${itemId}/apu`, cuerpoEnvio);
      lineas = r.apu.lineas.map((l) => ({ ...l }));
      dibujar();
      dibujarResumen(r.apu, r.precio_unitario);
      if (guardar) exito(`Precio unitario: ${moneda(r.precio_unitario)}`);
    } catch (e) { avisoError(e.message); }
  };

  const dibujarResumen = (apu, pu) => {
    const total = parseFloat(pu || 0);
    vaciar(zonaResumen).append(
      el('div', { class: 'rejilla c4 mb2' },
        ...Object.entries(TIPOS).map(([clave, nombre]) => el('div', { class: 'kpi' },
          el('span', { class: 'etiqueta' }, nombre),
          el('span', { class: 'valor chico mono' }, moneda(apu.por_tipo[clave] || 0)),
          el('span', { class: 'nota' },
            total ? `${((parseFloat(apu.por_tipo[clave] || 0) / total) * 100).toFixed(1)}% del PU` : '—')))),
      el('div', { class: 'panel' }, el('div', { class: 'panel-cuerpo' },
        el('div', { class: 'fila entre' },
          el('div', {},
            el('div', { class: 'chico apagado' }, 'Precio unitario'),
            el('div', { class: 'mono fuerte', estilo: { fontSize: '22px' } }, moneda(pu))),
          el('div', { estilo: { textAlign: 'right' } },
            el('div', { class: 'chico apagado' },
              `Metrado ${metrado(datos.item.metrado)} ${datos.item.unidad}`),
            el('div', { class: 'mono fuerte', estilo: { fontSize: '18px', color: 'var(--ok)' } },
              moneda(parseFloat(pu || 0) * parseFloat(datos.item.metrado || 0))))))));
  };

  cuerpo.replaceChildren(
    el('div', { class: 'fila entre mb2' },
      el('div', {},
        el('h1', { estilo: { margin: '0 0 3px', fontSize: '19px', letterSpacing: '-.4px' } },
          datos.item.descripcion),
        el('p', { class: 'suave', estilo: { margin: 0 } },
          `${datos.item.codigo || ''} · unidad ${datos.item.unidad} · `
          + `metrado ${metrado(datos.item.metrado)}`)),
      el('div', { class: 'fila' },
        el('button', { class: 'btn', onclick: () => ir(`/proyecto/${proyectoId}/presupuesto`) },
          icono('flecha'), 'Volver al presupuesto'),
        editable ? el('button', { class: 'btn primario', onclick: () => recalcular(true) },
          icono('guardar'), 'Guardar APU') : null)),

    avisoCaja('info', el('div', {},
      el('strong', {}, 'Convención S10: '),
      'la cantidad de mano de obra y equipo sale de cuadrilla × 8 h / rendimiento. '
      + 'El precio unitario se redondea antes de multiplicar por el metrado, para que el '
      + 'presupuesto impreso cuadre línea a línea.')),

    el('div', { class: 'fila mt2 mb2' },
      el('label', { class: 'chico fuerte' }, 'Rendimiento por jornada: '),
      rendimiento,
      el('span', { class: 'chico apagado' }, `${datos.item.unidad} / día`),
      el('button', { class: 'btn chico', onclick: () => recalcular(false) },
        icono('rehacer'), 'Recalcular')),

    zonaTabla, el('div', { class: 'mt2' }, zonaResumen));

  dibujar();
  dibujarResumen(datos.apu, datos.item.precio_unitario || datos.apu.pu);
}
