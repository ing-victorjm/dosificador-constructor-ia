// Elementos del proyecto: C-1, V-101, Z-1… con sus dimensiones reales.
// De un elemento salen sus partidas (concreto, encofrado, acero) sin volver a
// escribir la geometría.

import { api } from '../core/api.js';
import { estado, puede, ubicacionesPlanas, nombreUbicacion, especialidad } from '../core/estado.js';
import { metrado } from '../core/fmt.js';
import {
  el, vaciar, icono, cargando, vacio, chip, panel, campo, modal, confirmar,
  avisoCaja, puntoEspecialidad, exito, aviso, error as avisoError,
} from '../ui/base.js';

let filtroTipo = '';

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);
  cuerpo.append(cargando());

  const datos = await api.obtener(`/proyectos/${proyectoId}/elementos`);
  const tipos = datos.tipos;

  const lista = el('div');
  const dibujar = () => {
    const visibles = datos.elementos.filter((e) => !filtroTipo || e.tipo === filtroTipo);
    vaciar(lista);
    if (!visibles.length) {
      lista.append(vacio({
        icono: 'edificio',
        titulo: datos.elementos.length ? 'Ninguno de este tipo' : 'Todavía no hay elementos',
        mensaje: 'Registre los elementos con sus dimensiones (C-1, V-101, Z-1). De cada uno '
          + 'salen sus partidas de concreto, encofrado y acero sin repetir la geometría, '
          + 'y el control de calidad avisa si alguno queda sin metrar.',
        acciones: puede('crear') ? [el('button', {
          class: 'btn primario', onclick: () => dialogo(proyectoId, tipos, null, recargar),
        }, icono('mas'), 'Registrar elemento')] : [],
      }));
      return;
    }
    lista.append(el('div', { class: 'panel' }, el('div', { class: 'tabla-envoltura' },
      el('table', { class: 'tabla densa' },
        el('thead', {}, el('tr', {},
          el('th', {}, 'Marca'), el('th', {}, 'Tipo'), el('th', {}, 'Nombre'),
          el('th', {}, 'Ubicación'), el('th', { class: 'num' }, 'Cantidad'),
          el('th', {}, 'Dimensiones'), el('th', {}, 'Origen'),
          el('th', { class: 'centro' }, 'Metrado'), el('th', {}))),
        el('tbody', {}, ...visibles.map((e) => {
          const def = tipos.find((t) => t.clave === e.tipo);
          return el('tr', {},
            el('td', { class: 'fuerte mono' }, e.marca || '—'),
            el('td', {}, el('span', { class: 'fila', estilo: { gap: '6px' } },
              puntoEspecialidad(especialidad(e.especialidad).color),
              def?.nombre || e.tipo)),
            el('td', {}, e.nombre || '—'),
            el('td', { class: 'chico' }, nombreUbicacion(e.ubicacion_id) || '—'),
            el('td', { class: 'num mono' }, e.cantidad),
            el('td', { class: 'chico mono apagado' },
              Object.entries(e.propiedades || {})
                .map(([k, v]) => `${k}=${v}`).join('  ') || '—'),
            el('td', {}, chip(e.origen.replace('_', ' '),
              e.origen === 'detectado_ia' ? 'info' : '')),
            el('td', { class: 'centro' },
              e.metrado ? chip('sí', 'ok') : chip('pendiente', 'alerta')),
            el('td', { class: 'centro' },
              puede('editar') ? el('button', {
                class: 'btn chico fantasma',
                onclick: () => dialogo(proyectoId, tipos, e, recargar),
              }, icono('editar')) : null,
              puede('eliminar') ? el('button', {
                class: 'btn chico fantasma',
                onclick: async () => {
                  const ok = await confirmar({
                    titulo: 'Eliminar elemento',
                    mensaje: `Se eliminará ${e.marca || e.tipo}.`,
                    aceptar: 'Eliminar', peligroso: true,
                  });
                  if (!ok) return;
                  await api.borrar(`/proyectos/${proyectoId}/elementos/${e.id}`);
                  exito('Elemento eliminado.');
                  recargar();
                },
              }, icono('borrar')) : null));
        }))))));
  };

  const recargar = () => render(vaciar(contenedor), params);

  cuerpo.replaceChildren(
    el('div', { class: 'fila entre mb2 envuelve' },
      el('div', {},
        el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
          'Elementos'),
        el('p', { class: 'suave', estilo: { margin: 0 } },
          `${datos.elementos.length} elemento(s) registrados · `
          + `${datos.elementos.filter((e) => !e.metrado).length} sin metrar`)),
      el('div', { class: 'fila' },
        el('select', {
          estilo: { width: 'auto' },
          onchange: (ev) => { filtroTipo = ev.target.value; dibujar(); },
        },
          el('option', { value: '' }, 'Todos los tipos'),
          ...tipos.map((t) => el('option', { value: t.clave }, t.nombre))),
        puede('crear') ? el('button', {
          class: 'btn primario', onclick: () => dialogo(proyectoId, tipos, null, recargar),
        }, icono('mas'), 'Registrar elemento') : null)),
    lista);

  dibujar();
}

function dialogo(proyectoId, tipos, existente, recargar) {
  const tipo = el('select', {}, ...tipos.map((t) => el('option', {
    value: t.clave, selected: existente?.tipo === t.clave,
  }, t.nombre)));
  const marca = el('input', { type: 'text', value: existente?.marca || '', placeholder: 'C-1' });
  const nombre = el('input', { type: 'text', value: existente?.nombre || '' });
  const cantidad = el('input', { type: 'text', value: existente?.cantidad || '1', class: 'num' });
  const ubicacion = el('select', {},
    el('option', { value: '' }, 'Sin ubicación'),
    ...ubicacionesPlanas().map((u) => el('option', {
      value: u.id, selected: existente?.ubicacion_id === u.id,
    }, `${'— '.repeat(u.nivel)}${u.nombre}`)));

  const zonaDimensiones = el('div', { class: 'fila-campos' });
  const entradasDim = {};

  const dibujarDimensiones = () => {
    const def = tipos.find((t) => t.clave === tipo.value);
    vaciar(zonaDimensiones);
    Object.keys(entradasDim).forEach((k) => delete entradasDim[k]);
    for (const d of def?.dimensiones || []) {
      const entrada = el('input', {
        type: 'text', class: 'num',
        value: existente?.propiedades?.[d] || '',
        placeholder: '0.00',
      });
      entradasDim[d] = entrada;
      zonaDimensiones.append(campo(d.replace(/_/g, ' '), entrada));
    }
    if (!def?.dimensiones?.length) {
      zonaDimensiones.append(el('p', { class: 'chico apagado' },
        'Este tipo no requiere dimensiones: se cuenta por unidad.'));
    }
    partidasInfo.replaceChildren(def?.partidas?.length
      ? avisoCaja('info', el('div', {},
          el('strong', {}, 'Partidas que genera este elemento: '),
          def.partidas.join(', '), '.'))
      : null);
  };
  const partidasInfo = el('div', { class: 'mt2' });
  tipo.onchange = dibujarDimensiones;

  const control = modal({
    titulo: existente ? `Editar ${existente.marca || existente.tipo}` : 'Registrar elemento',
    ancho: 'ancho',
    cuerpo: el('div', {},
      el('div', { class: 'fila-campos' },
        campo('Tipo', tipo), campo('Marca', marca), campo('Cantidad', cantidad)),
      el('div', { class: 'fila-campos' },
        campo('Nombre descriptivo', nombre), campo('Ubicación', ubicacion)),
      el('div', { class: 'sep' }),
      el('div', { class: 'chico fuerte mb1' }, 'Dimensiones (en metros)'),
      zonaDimensiones,
      partidasInfo),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          const propiedades = {};
          for (const [k, entrada] of Object.entries(entradasDim)) {
            if (entrada.value.trim()) propiedades[k] = entrada.value.trim();
          }
          const datos = {
            tipo: tipo.value,
            marca: marca.value.trim() || null,
            nombre: nombre.value.trim() || null,
            cantidad: cantidad.value.trim() || '1',
            ubicacion_id: ubicacion.value || null,
            especialidad: tipos.find((t) => t.clave === tipo.value)?.especialidad || 'estructuras',
            propiedades,
          };
          try {
            if (existente) {
              await api.actualizar(`/proyectos/${proyectoId}/elementos/${existente.id}`, datos);
            } else {
              await api.crear(`/proyectos/${proyectoId}/elementos`, datos);
            }
            control.cerrar();
            exito(existente ? 'Elemento actualizado.' : 'Elemento registrado.');
            recargar();
          } catch (e) { avisoError(e.message); }
        },
      }, icono('check'), existente ? 'Guardar' : 'Registrar'),
    ],
  });

  dibujarDimensiones();
}
