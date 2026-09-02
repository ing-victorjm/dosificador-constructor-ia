// Control de calidad: alertas con gravedad, explicación llana, cita normativa y
// cómo se corrigen. Una alerta que no dice qué hacer no sirve en obra.

import { api } from '../core/api.js';
import { estado, puede } from '../core/estado.js';
import { el, vaciar, icono, cargando, vacio, chip, confirmar, exito, error as avisoError, avisoCaja } from '../ui/base.js';
import { ir } from '../app.js';

let filtroGravedad = '';
let filtroTipo = '';

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);
  cuerpo.append(cargando('Revisando el metrado…'));

  const datos = await api.obtener(`/proyectos/${proyectoId}/calidad`
    + (estado.versionId ? `?version_id=${estado.versionId}` : ''));
  estado.alertas = datos.resumen.por_gravedad.alta || 0;

  const lista = el('div', { class: 'panel' });

  const dibujarLista = () => {
    const visibles = datos.alertas.filter((a) =>
      (!filtroGravedad || a.gravedad === filtroGravedad)
      && (!filtroTipo || a.tipo === filtroTipo));

    vaciar(lista);
    if (!visibles.length) {
      lista.append(vacio({
        icono: 'calidad',
        titulo: datos.alertas.length ? 'Nada con este filtro' : 'Sin incidencias',
        mensaje: datos.alertas.length
          ? 'Cambie el filtro para ver las demás alertas.'
          : `Se revisaron ${datos.revisadas.partidas} partidas, ${datos.revisadas.planos} planos `
            + `y ${datos.revisadas.elementos} elementos sin encontrar problemas.`,
      }));
      return;
    }
    for (const a of visibles) lista.append(tarjetaAlerta(a, proyectoId, () => render(vaciar(contenedor), params)));
  };

  const tipos = Object.entries(datos.resumen.por_tipo)
    .sort((x, y) => y[1] - x[1]);

  cuerpo.replaceChildren(
    el('div', { class: 'fila entre mb2 envuelve' },
      el('div', {},
        el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
          'Control de calidad'),
        el('p', { class: 'suave', estilo: { margin: 0 } },
          `${datos.resumen.total} incidencia(s) sobre ${datos.revisadas.partidas} partidas`
          + (datos.descartadas ? ` · ${datos.descartadas} alerta(s) descartadas` : ''))),
      el('button', {
        class: 'btn', onclick: () => api.descargar(
          `/proyectos/${proyectoId}/exportar/calidad?formato=xlsx`),
      }, icono('descargar'), 'Exportar informe')),

    el('div', { class: 'rejilla c3 mb2' },
      tarjetaGravedad('alta', 'Gravedad alta', datos.resumen.por_gravedad.alta,
        'Corrija antes de entregar el expediente'),
      tarjetaGravedad('media', 'Gravedad media', datos.resumen.por_gravedad.media,
        'Revise y justifique'),
      tarjetaGravedad('baja', 'Gravedad baja', datos.resumen.por_gravedad.baja,
        'Confirme que es correcto')),

    el('div', { class: 'fila envuelve mb2' },
      el('select', {
        estilo: { width: 'auto' },
        onchange: (e) => { filtroGravedad = e.target.value; dibujarLista(); },
      },
        el('option', { value: '' }, 'Todas las gravedades'),
        el('option', { value: 'alta' }, 'Solo alta'),
        el('option', { value: 'media' }, 'Solo media'),
        el('option', { value: 'baja' }, 'Solo baja')),
      el('select', {
        estilo: { width: 'auto' },
        onchange: (e) => { filtroTipo = e.target.value; dibujarLista(); },
      },
        el('option', { value: '' }, 'Todos los tipos'),
        ...tipos.map(([t, n]) => el('option', { value: t },
          `${t.replace(/_/g, ' ')} (${n})`)))),

    lista);

  dibujarLista();
}

function tarjetaGravedad(clave, etiqueta, cantidad, nota) {
  const tipo = clave === 'alta' ? 'peligro' : clave === 'media' ? 'alerta' : '';
  return el('div', { class: `kpi ${cantidad ? tipo : 'ok'}` },
    el('span', { class: 'etiqueta' }, etiqueta),
    el('span', { class: 'valor' }, String(cantidad || 0)),
    el('span', { class: 'nota' }, cantidad ? nota : 'Sin incidencias'));
}

function tarjetaAlerta(a, proyectoId, recargar) {
  return el('div', { class: `alerta-qa ${a.gravedad}` },
    el('div', { class: 'marca-gravedad' }),
    el('div', { class: 'cuerpo' },
      el('div', { class: 'fila entre' },
        el('div', { class: 'titulo' }, a.titulo),
        el('div', { class: 'fila' },
          chip(a.tipo.replace(/_/g, ' ')),
          chip(a.gravedad, a.gravedad === 'alta' ? 'peligro'
            : a.gravedad === 'media' ? 'alerta' : ''))),
      el('div', { class: 'detalle' }, a.detalle),
      el('div', { class: 'solucion' },
        el('strong', {}, 'Cómo se corrige: '), a.solucion),
      a.cita ? el('div', { class: 'cita' },
        a.referencia ? el('strong', {}, a.referencia + ' — ') : null, a.cita) : null,
      el('div', { class: 'fila mt1' },
        a.item_id ? el('button', {
          class: 'btn chico',
          onclick: () => ir(`/proyecto/${proyectoId}/metrados`),
        }, icono('planilla'), 'Ir a la partida') : null,
        a.plano_id ? el('button', {
          class: 'btn chico',
          onclick: () => ir(`/proyecto/${proyectoId}/planos`),
        }, icono('plano'), 'Ir al plano') : null,
        puede('revisar') ? el('button', {
          class: 'btn chico fantasma',
          onclick: async () => {
            const r = await confirmar({
              titulo: 'Descartar alerta',
              mensaje: `Se ocultará «${a.titulo}» de este proyecto.`,
              detalle: 'Queda registrado quién la descartó y por qué. Puede reactivarla después.',
              aceptar: 'Descartar', exigirMotivo: true,
            });
            if (!r?.ok) return;
            try {
              await api.crear(`/proyectos/${proyectoId}/calidad/descartar`,
                { clave: a.clave, motivo: r.motivo });
              exito('Alerta descartada.');
              recargar();
            } catch (e) { avisoError(e.message); }
          },
        }, 'Descartar') : null)));
}
