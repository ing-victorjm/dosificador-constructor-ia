// Hoja de metrados: árbol de partidas + planilla de sustento editable.
//
// La planilla es una rejilla tecleable: se navega con Tab y flechas, se pega un
// bloque copiado de Excel y se repiten filas a otros niveles y ejes. Es la
// diferencia entre una app que se usa y una que se abandona por una hoja de
// cálculo.

import { api } from '../core/api.js';
import { estado, puede, ubicacionesPlanas, nombreUbicacion, especialidad } from '../core/estado.js';
import { metrado, moneda, num, parsear, esc, fecha } from '../core/fmt.js';
import {
  el, vaciar, icono, cargando, vacio, chip, panel, campo, modal, confirmar,
  avisoCaja, cita, puntoEspecialidad, aviso, exito, error as avisoError,
} from '../ui/base.js';

const COLUMNAS = [
  { clave: 'descripcion', etiqueta: 'Descripción de la fila', ancho: '26%', texto: true },
  { clave: 'n', etiqueta: 'Cant.', ancho: '7%' },
  { clave: 'veces', etiqueta: 'N° veces', ancho: '7%' },
  { clave: 'largo', etiqueta: 'Largo', ancho: '8%' },
  { clave: 'ancho', etiqueta: 'Ancho', ancho: '8%' },
  { clave: 'alto', etiqueta: 'Alto', ancho: '8%' },
  { clave: 'lamina', etiqueta: 'Lámina', ancho: '8%', texto: true },
  { clave: 'eje', etiqueta: 'Eje / tramo', ancho: '9%', texto: true },
];

let hoja = null;
let itemActivo = null;
let filtroTexto = '';
let filtroEspecialidad = '';
let expandidos = new Set();
let seleccionadas = new Set();

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  if (!proyectoId) {
    contenedor.append(vacio({
      titulo: 'Abra un proyecto', mensaje: 'Elija un proyecto para ver su hoja de metrados.',
    }));
    return;
  }

  const taller = el('div', { class: 'taller sin-abajo' });
  const zonaIzq = el('div', { class: 'zona-izq' });
  const zonaCentro = el('div', { class: 'zona-centro', estilo: { overflow: 'auto' } });
  const zonaDer = el('div', { class: 'zona-der' });
  taller.append(zonaIzq, zonaCentro, zonaDer);
  contenedor.append(taller);
  contenedor.classList.add('sin-scroll');

  zonaCentro.append(cargando('Calculando el metrado…'));
  await cargarHoja(proyectoId);

  dibujarArbol(zonaIzq, proyectoId);
  if (!itemActivo) {
    const primera = partidasPlanas().find((n) => n.tipo === 'partida');
    itemActivo = primera ? primera.id : null;
  }
  await dibujarPartida(zonaCentro, zonaDer, proyectoId);
}

async function cargarHoja(proyectoId) {
  hoja = await api.obtener(
    `/proyectos/${proyectoId}/metrados?con_filas=true`
    + (estado.versionId ? `&version_id=${estado.versionId}` : ''));
  if (!expandidos.size) {
    for (const n of hoja.items) expandidos.add(n.id);
  }
}

function partidasPlanas(nodos = hoja?.items || [], salida = []) {
  for (const n of nodos) {
    salida.push(n);
    partidasPlanas(n.hijos || [], salida);
  }
  return salida;
}

function buscarNodo(id, nodos = hoja?.items || []) {
  for (const n of nodos) {
    if (n.id === id) return n;
    const encontrado = buscarNodo(id, n.hijos || []);
    if (encontrado) return encontrado;
  }
  return null;
}

// ------------------------------------------------------------------- Árbol

function dibujarArbol(zona, proyectoId) {
  const lista = el('div', { class: 'arbol' });

  const coincide = (n) => {
    const texto = `${n.item} ${n.codigo || ''} ${n.descripcion}`.toLowerCase();
    const porTexto = !filtroTexto || texto.includes(filtroTexto.toLowerCase());
    const porEsp = !filtroEspecialidad || n.especialidad === filtroEspecialidad;
    return porTexto && porEsp;
  };

  const visible = (n) => {
    if (n.tipo === 'partida') return coincide(n);
    return coincide(n) || (n.hijos || []).some(visible);
  };

  const nodoDe = (n, nivel) => {
    const esTitulo = n.tipo === 'titulo';
    const abierto = expandidos.has(n.id);
    const fila = el('div', {
      class: `arbol-nodo ${abierto ? 'expandido' : ''} ${itemActivo === n.id ? 'activo' : ''}`,
      onclick: async () => {
        if (esTitulo) {
          if (abierto) expandidos.delete(n.id); else expandidos.add(n.id);
          dibujarArbol(zona, proyectoId);
        } else {
          itemActivo = n.id;
          seleccionadas.clear();
          dibujarArbol(zona, proyectoId);
          await dibujarPartida(
            document.querySelector('.zona-centro'),
            document.querySelector('.zona-der'), proyectoId);
        }
      },
    },
      esTitulo ? icono('flecha', 'flecha') : puntoEspecialidad(n.color),
      el('span', { class: 'etiqueta', title: n.descripcion },
        el('span', { class: 'mono chico apagado' }, n.item + '  '),
        n.descripcion),
      esTitulo
        ? el('span', { class: 'conteo' }, String(n.n_partidas || 0))
        : el('span', { class: 'conteo' },
            (n.resumen?.origen === 'vacio') ? '—' : metrado(n.metrado)),
    );

    if (n.resumen?.filas_incompletas) {
      fila.append(el('span', { class: 'punto-especialidad', estilo: { background: 'var(--alerta)' } }));
    }
    if (n.bloqueado) fila.append(icono('bloqueo', 'flecha'));

    const envoltura = el('div', {}, fila);
    if (esTitulo && abierto) {
      const hijos = (n.hijos || []).filter(visible);
      envoltura.append(el('div', { class: 'arbol-hijos' }, ...hijos.map((h) => nodoDe(h, nivel + 1))));
    }
    return envoltura;
  };

  const raiz = (hoja.items || []).filter(visible);
  if (raiz.length) {
    lista.append(...raiz.map((n) => nodoDe(n, 0)));
  } else {
    lista.append(el('p', { class: 'apagado chico', estilo: { padding: '16px' } },
      'Ninguna partida coincide con el filtro.'));
  }

  vaciar(zona).append(
    el('div', { class: 'zona-cabecera' },
      icono('planilla'), el('span', { class: 'crecer' }, 'Partidas'),
      puede('crear') ? el('button', {
        class: 'btn chico fantasma', title: 'Agregar partida',
        onclick: () => nuevaPartida(proyectoId),
      }, icono('mas')) : null),
    el('div', { estilo: { padding: '8px 10px', borderBottom: '1px solid var(--panel-borde)' } },
      el('input', {
        type: 'search', id: 'filtro-metrados', placeholder: 'Filtrar partidas…',
        value: filtroTexto, estilo: { fontSize: '12px', padding: '6px 9px' },
        oninput: (e) => { filtroTexto = e.target.value; dibujarArbol(zona, proyectoId); },
      }),
      el('select', {
        estilo: { fontSize: '12px', padding: '6px 9px', marginTop: '6px' },
        onchange: (e) => { filtroEspecialidad = e.target.value; dibujarArbol(zona, proyectoId); },
      },
        el('option', { value: '' }, 'Todas las especialidades'),
        ...(hoja.por_especialidad || []).map((e) => el('option', {
          value: e.clave, selected: e.clave === filtroEspecialidad,
        }, `${e.nombre} (${e.partidas})`)))),
    lista,
    el('div', {
      estilo: {
        padding: '10px 12px', borderTop: '1px solid var(--panel-borde)',
        position: 'sticky', bottom: 0, background: 'var(--panel)',
      },
    },
      el('div', { class: 'fila entre chico' },
        el('span', { class: 'suave' }, 'Partidas con metrado'),
        el('span', { class: 'mono fuerte' },
          `${hoja.conteo.con_metrado}/${hoja.conteo.partidas}`)),
      el('div', { class: 'fila entre chico mt1' },
        el('span', { class: 'suave' }, 'Costo directo'),
        el('span', { class: 'mono fuerte' }, moneda(hoja.costo_directo)))),
  );
}

// ---------------------------------------------------------------- Partida

async function dibujarPartida(zonaCentro, zonaDer, proyectoId) {
  if (!itemActivo) {
    vaciar(zonaCentro).append(vacio({
      icono: 'planilla', titulo: 'Elija una partida',
      mensaje: 'Seleccione una partida del árbol para ver y editar su planilla de sustento.',
    }));
    vaciar(zonaDer);
    return;
  }

  vaciar(zonaCentro).append(cargando());
  let datos;
  try {
    datos = await api.obtener(`/items/${itemActivo}`);
  } catch (e) {
    vaciar(zonaCentro).append(avisoCaja('peligro', e.message));
    return;
  }

  const { item, filas, resumen, familia } = datos;
  const editable = puede('editar') && !item.bloqueado;

  const tabla = construirPlanilla(item, filas, resumen, editable, proyectoId);

  vaciar(zonaCentro).append(
    el('div', {
      class: 'zona-cabecera',
      estilo: { position: 'sticky', top: 0, zIndex: 8, padding: '11px 14px' },
    },
      puntoEspecialidad(especialidad(item.especialidad).color),
      el('div', { class: 'crecer', estilo: { textTransform: 'none' } },
        el('div', {
          class: 'fuerte', estilo: { fontSize: '13.5px', color: 'var(--texto)', letterSpacing: 0 },
        }, item.descripcion),
        el('div', { class: 'chico apagado', estilo: { fontWeight: 400, letterSpacing: 0 } },
          [item.codigo, especialidad(item.especialidad).nombre,
           `unidad: ${item.unidad || '—'}`].filter(Boolean).join(' · '))),
      item.bloqueado ? chip('Aprobada y bloqueada', 'ok') : null,
    ),

    el('div', { estilo: { padding: '12px 14px' } },
      barraHerramientas(item, filas, editable, proyectoId),
      resumen.avisos?.length
        ? el('div', { class: 'col mt2', estilo: { gap: '6px' } },
            ...resumen.avisos.map((a) => avisoCaja(
              a.includes('inventan') || a.includes('error') ? 'alerta' : 'info', a)))
        : null,
      el('div', { class: 'mt2' }, tabla)),
  );

  dibujarPropiedades(zonaDer, item, resumen, familia, editable, proyectoId);
}

function barraHerramientas(item, filas, editable, proyectoId) {
  if (!editable) {
    return avisoCaja('info', item.bloqueado
      ? 'La partida está aprobada y bloqueada. Un supervisor debe desbloquearla para editarla.'
      : 'Su rol no permite editar metrados. Puede consultar y exportar.');
  }
  return el('div', { class: 'fila envuelve' },
    el('button', {
      class: 'btn chico primario',
      onclick: () => agregarFila(item, proyectoId),
    }, icono('mas'), 'Agregar fila'),
    el('button', {
      class: 'btn chico',
      onclick: () => dialogoPegar(item, proyectoId),
    }, icono('pegar'), 'Pegar de Excel'),
    el('button', {
      class: 'btn chico', disabled: !seleccionadas.size,
      onclick: () => dialogoRepetir(item, proyectoId),
    }, icono('repetir'), `Repetir${seleccionadas.size ? ` (${seleccionadas.size})` : ''}`),
    el('button', {
      class: 'btn chico',
      onclick: () => dialogoVanos(item, proyectoId),
    }, icono('poligono'), 'Descontar vanos'),
    el('div', { class: 'crecer' }),
    el('button', {
      class: 'btn chico',
      onclick: () => verTrazabilidad(item),
    }, icono('ojo'), '¿De dónde sale?'),
    puede('revisar') || puede('aprobar')
      ? el('select', {
          estilo: { width: 'auto', padding: '4px 8px', fontSize: '11.5px' },
          onchange: (e) => cambiarEstado(item, e.target.value, proyectoId),
        },
          ...['borrador', 'revisado', 'observado', 'aprobado'].map((s) => el('option', {
            value: s, selected: item.estado === s,
          }, s.charAt(0).toUpperCase() + s.slice(1))))
      : chip(item.estado, item.estado === 'aprobado' ? 'ok'
        : item.estado === 'observado' ? 'alerta' : ''),
  );
}

function construirPlanilla(item, filas, resumen, editable, proyectoId) {
  const cuerpo = el('tbody');

  for (const f of filas) {
    const tr = el('tr', {
      class: [
        f.signo < 0 ? 'deduccion' : '',
        f.faltantes?.length ? 'incompleta' : '',
        f.error && !f.faltantes?.length ? 'con-error' : '',
        seleccionadas.has(f.id) ? 'seleccionada' : '',
      ].join(' '),
    });

    tr.append(el('td', { estilo: { width: '28px' } },
      el('input', {
        type: 'checkbox', checked: seleccionadas.has(f.id),
        estilo: { width: 'auto', cursor: 'pointer' },
        onchange: (e) => {
          if (e.target.checked) seleccionadas.add(f.id); else seleccionadas.delete(f.id);
          tr.classList.toggle('seleccionada', e.target.checked);
          const boton = document.querySelector('.zona-centro .btn.chico:nth-child(3)');
          if (boton) {
            boton.disabled = !seleccionadas.size;
            boton.lastChild.textContent = `Repetir${seleccionadas.size ? ` (${seleccionadas.size})` : ''}`;
          }
        },
      })));

    for (const col of COLUMNAS) {
      const entrada = el('input', {
        type: 'text',
        class: col.texto ? 'texto' : '',
        value: f[col.clave] ?? '',
        placeholder: col.texto ? '' : '—',
        disabled: !editable,
        datos: { campo: col.clave, fila: f.id },
      });
      entrada.addEventListener('keydown', (e) => navegar(e, entrada));
      entrada.addEventListener('change', () => guardarCelda(f.id, col.clave, entrada.value, item, proyectoId));
      tr.append(el('td', {}, entrada));
    }

    const celdaParcial = el('td', { class: 'parcial', title: f.sustento || '' },
      f.parcial !== null && f.parcial !== undefined
        ? metrado(f.parcial)
        : el('span', { class: 'apagado chico' }, f.faltantes?.length ? 'faltan datos' : '—'));
    tr.append(celdaParcial);

    tr.append(el('td', { class: 'centro', estilo: { width: '70px' } },
      el('button', {
        class: 'btn chico fantasma', title: 'Ver el cálculo de esta fila',
        onclick: () => verFila(f, item),
      }, icono('info')),
      editable ? el('button', {
        class: 'btn chico fantasma', title: 'Eliminar fila',
        onclick: async () => {
          const ok = await confirmar({
            titulo: 'Eliminar fila',
            mensaje: `Se eliminará «${f.descripcion || f.sustento || 'la fila'}» del sustento.`,
            aceptar: 'Eliminar', peligroso: true,
          });
          if (!ok) return;
          await api.borrar(`/mediciones/${f.id}`);
          exito('Fila eliminada.');
          await recargar(proyectoId);
        },
      }, icono('borrar')) : null));

    cuerpo.append(tr);
  }

  if (!filas.length) {
    cuerpo.append(el('tr', {}, el('td', { colspan: COLUMNAS.length + 3 },
      el('div', { class: 'vacio', estilo: { minHeight: '140px', padding: '26px' } },
        el('div', { class: 'icono' }, icono('planilla')),
        el('h3', {}, 'Esta partida no tiene sustento'),
        el('p', {}, 'Agregue filas con sus dimensiones, péguelas desde Excel o mídalas '
          + 'sobre el plano. METRA AI no inventa cantidades.')))));
  }

  const totalFila = el('tr', { class: 'total-partida' },
    el('td', { colspan: 7 }),
    el('td', { colspan: 2, estilo: { textAlign: 'right' } },
      `TOTAL (${item.unidad || '—'})`),
    el('td', { class: 'parcial' }, metrado(resumen.total)),
    el('td', {}));

  const tabla = el('table', { class: 'tabla densa planilla' },
    el('thead', {}, el('tr', {},
      el('th', { estilo: { width: '28px' } }),
      ...COLUMNAS.map((c) => el('th', {
        class: c.texto ? '' : 'num', estilo: { width: c.ancho },
      }, c.etiqueta)),
      el('th', { class: 'num' }, 'Parcial'),
      el('th', { class: 'centro' }, ''))),
    cuerpo,
    el('tfoot', {}, totalFila));

  // Pegado directo sobre la rejilla: es la vía rápida de verdad.
  if (editable) {
    tabla.addEventListener('paste', async (e) => {
      const texto = (e.clipboardData || window.clipboardData).getData('text');
      if (!texto || !texto.includes('\t')) return;   // una sola celda: comportamiento normal
      e.preventDefault();
      await pegarBloque(item, texto, false, proyectoId);
    });
  }

  const envoltura = el('div', { class: 'panel', estilo: { overflow: 'visible' } },
    el('div', { class: 'tabla-envoltura' }, tabla));

  if (resumen.cantidad_a_comprar) {
    envoltura.append(el('div', {
      class: 'panel-cuerpo',
      estilo: { borderTop: '1px solid var(--panel-borde)', padding: '11px 14px' },
    },
      avisoCaja('alerta', el('div', {},
        el('strong', {}, `Metrado de la partida: ${metrado(resumen.total)} ${item.unidad}. `),
        `Cantidad a comprar con ${resumen.desperdicio_pct}% de desperdicio: `,
        el('strong', {}, `${metrado(resumen.cantidad_a_comprar)} ${item.unidad}`),
        el('div', { class: 'chico mt1' },
          'El desperdicio no forma parte del metrado: se aplica en el análisis de '
          + 'precios unitarios. Si lo suma aquí, lo cobra dos veces.')))));
  }

  return envoltura;
}

// --------------------------------------------------------------- Edición

function navegar(e, entrada) {
  const celda = entrada.closest('td');
  const fila = entrada.closest('tr');
  const indice = [...fila.children].indexOf(celda);

  const mover = (nuevaFila) => {
    const destino = nuevaFila?.children[indice]?.querySelector('input');
    if (destino) { destino.focus(); destino.select(); }
  };

  if (e.key === 'ArrowDown' || (e.key === 'Enter' && !e.shiftKey)) {
    e.preventDefault();
    mover(fila.nextElementSibling);
  } else if (e.key === 'ArrowUp' || (e.key === 'Enter' && e.shiftKey)) {
    e.preventDefault();
    mover(fila.previousElementSibling);
  }
}

async function guardarCelda(medicionId, campoClave, valor, item, proyectoId) {
  const limpio = ['descripcion', 'lamina', 'eje'].includes(campoClave)
    ? (valor.trim() || null)
    : (valor.trim() ? parsear(valor) : null);
  try {
    await api.actualizar(`/mediciones/${medicionId}`, { [campoClave]: limpio });
    await recargar(proyectoId);
  } catch (e) {
    avisoError(e.message);
  }
}

async function agregarFila(item, proyectoId) {
  try {
    await api.crear(`/items/${item.id}/mediciones`, { descripcion: '', origen: 'ingresado' });
    await recargar(proyectoId);
    setTimeout(() => {
      const filas = document.querySelectorAll('.planilla tbody tr');
      const ultima = filas[filas.length - 1];
      ultima?.querySelector('input.texto')?.focus();
    }, 120);
  } catch (e) { avisoError(e.message); }
}

async function recargar(proyectoId) {
  await cargarHoja(proyectoId);
  dibujarArbol(document.querySelector('.zona-izq'), proyectoId);
  await dibujarPartida(
    document.querySelector('.zona-centro'), document.querySelector('.zona-der'), proyectoId);
}

// ------------------------------------------------------------- Diálogos

async function pegarBloque(item, texto, reemplazar, proyectoId) {
  try {
    const r = await api.crear(`/items/${item.id}/mediciones/pegar`, { texto, reemplazar });
    await recargar(proyectoId);
    if (r.rechazadas.length) {
      aviso(`${r.creadas} fila(s) pegadas. ${r.rechazadas.length} rechazadas: `
        + r.rechazadas.slice(0, 2).map((x) => `línea ${x.linea} — ${x.motivo}`).join('; '), 'alerta', 9000);
    } else {
      exito(`${r.creadas} fila(s) pegadas.`);
    }
  } catch (e) { avisoError(e.message); }
}

function dialogoPegar(item, proyectoId) {
  const area = el('textarea', {
    estilo: { minHeight: '180px', fontFamily: 'var(--mono)', fontSize: '12px' },
    placeholder: 'Pegue aquí (Ctrl+V) el bloque copiado de Excel.\n\n'
      + 'Muros eje A\t1\t\t12.40\t\t2.60\nMuros eje B\t1\t\t8.20\t\t2.60',
  });
  const reemplazar = el('input', { type: 'checkbox' });

  const control = modal({
    titulo: 'Pegar filas desde Excel',
    ancho: 'ancho',
    cuerpo: el('div', {},
      avisoCaja('info', el('div', {},
        el('strong', {}, 'Orden de columnas: '),
        'Descripción · Cantidad · N° veces · Largo · Ancho · Alto · Lámina · Eje.',
        el('div', { class: 'chico mt1' },
          'Las celdas vacías se dejan VACÍAS, no en cero: así el parcial las omite del '
          + 'producto en lugar de anularlo.'))),
      el('div', { class: 'mt2' }, area),
      el('label', { class: 'interruptor mt2' }, reemplazar, el('span', { class: 'pista' }),
        el('span', {}, 'Reemplazar las filas actuales en vez de agregar'))),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          const texto = area.value.trim();
          if (!texto) return aviso('Pegue el contenido primero.', 'alerta');
          control.cerrar();
          await pegarBloque(item, texto, reemplazar.checked, proyectoId);
        },
      }, icono('pegar'), 'Pegar filas'),
    ],
  });
  setTimeout(() => area.focus(), 80);
}

function dialogoRepetir(item, proyectoId) {
  const niveles = ubicacionesPlanas(['nivel', 'sector', 'ambiente', 'bloque']);
  const seleccionNiveles = el('select', { multiple: true, estilo: { height: '150px' } },
    ...niveles.map((u) => el('option', { value: u.id }, `${'— '.repeat(u.nivel)}${u.nombre}`)));
  const ejes = el('input', { type: 'text', placeholder: 'A, B, C   (separados por coma)' });
  const prefijo = el('input', { type: 'text', placeholder: 'Texto que se agrega a la descripción' });

  const control = modal({
    titulo: `Repetir ${seleccionadas.size} fila(s)`,
    cuerpo: el('div', {},
      avisoCaja('info', 'Metre el piso típico una vez y replíquelo. Cada copia conserva su '
        + 'propia trazabilidad, con el nivel y el eje anotados en la descripción.'),
      el('div', { class: 'mt2' },
        campo('Repetir en estos niveles o sectores', seleccionNiveles,
          'Mantenga Ctrl para elegir varios. Si no elige ninguno, se repite en el mismo sitio.')),
      campo('Repetir por ejes', ejes, 'Opcional. Se genera una copia por cada eje.'),
      campo('Prefijo de descripción', prefijo)),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          const datos = {
            medicion_ids: [...seleccionadas],
            ubicacion_ids: [...seleccionNiveles.selectedOptions].map((o) => o.value),
            ejes: ejes.value.split(',').map((x) => x.trim()).filter(Boolean),
            prefijo_descripcion: prefijo.value.trim() || null,
          };
          control.cerrar();
          try {
            const r = await api.crear(`/items/${item.id}/mediciones/repetir`, datos);
            seleccionadas.clear();
            await recargar(proyectoId);
            exito(`${r.creadas} fila(s) creadas.`);
          } catch (e) { avisoError(e.message); }
        },
      }, icono('repetir'), 'Repetir'),
    ],
  });
}

function dialogoVanos(item, proyectoId) {
  const filas = [];
  const cuerpoTabla = el('tbody');

  const agregar = (datos = {}) => {
    const d = el('input', { type: 'text', value: datos.descripcion || '', placeholder: 'Puerta P-1' });
    const n = el('input', { type: 'text', value: datos.n || '1', class: 'num' });
    const a = el('input', { type: 'text', value: datos.ancho || '', placeholder: '0.90', class: 'num' });
    const h = el('input', { type: 'text', value: datos.alto || '', placeholder: '2.10', class: 'num' });
    const fila = { d, n, a, h };
    filas.push(fila);
    cuerpoTabla.append(el('tr', {},
      el('td', {}, d), el('td', {}, n), el('td', {}, a), el('td', {}, h),
      el('td', {}, el('button', {
        class: 'btn chico fantasma',
        onclick: (e) => { e.target.closest('tr').remove(); fila.borrada = true; },
      }, icono('borrar')))));
  };
  agregar({ descripcion: 'Puerta P-1', n: '1', ancho: '0.90', alto: '2.10' });
  agregar({ descripcion: 'Ventana V-1', n: '1', ancho: '1.50', alto: '1.20' });

  const resultado = el('div', { class: 'mt2' });
  const familias = estado.referencia.reglas.familias;
  const selectorFamilia = el('select', {},
    ...familias.map((f) => el('option', {
      value: f.clave, selected: f.clave === item.familia_descuento,
    }, `${f.nombre} — ${f.umbral_m2 === '0' ? 'descuenta todo vano' : `desde ${f.umbral_m2} m²`}`)));

  const explicacion = el('div', { class: 'mt1' });
  const actualizarExplicacion = () => {
    const f = familias.find((x) => x.clave === selectorFamilia.value);
    explicacion.replaceChildren(f ? cita({
      texto: f.cita, codigo: f.codigo, etiqueta: f.etiqueta,
    }) : null);
    if (f?.nota) explicacion.append(el('div', { class: 'chico apagado mt1' }, f.nota));
  };
  selectorFamilia.onchange = actualizarExplicacion;
  actualizarExplicacion();

  const evaluar = async (insertar) => {
    const vanos = filas.filter((f) => !f.borrada).map((f) => ({
      descripcion: f.d.value.trim() || 'Vano',
      n: parsear(f.n.value) || '1',
      ancho: parsear(f.a.value),
      alto: parsear(f.h.value),
    })).filter((v) => v.ancho && v.alto);

    if (!vanos.length) return aviso('Escriba al menos un vano con ancho y alto.', 'alerta');
    try {
      const r = await api.crear(`/items/${item.id}/vanos`, {
        vanos, familia: selectorFamilia.value, insertar,
      });
      resultado.replaceChildren(
        el('div', { class: 'panel mt2' },
          el('div', { class: 'panel-cuerpo compacto' },
            el('table', { class: 'tabla densa' },
              el('thead', {}, el('tr', {},
                el('th', {}, 'Vano'), el('th', { class: 'num' }, 'Área unit.'),
                el('th', {}, '¿Se descuenta?'), el('th', {}, 'Motivo'))),
              el('tbody', {}, ...r.evaluados.map((v) => el('tr', {},
                el('td', {}, `${v.n} × ${v.descripcion}`),
                el('td', { class: 'num' }, `${v.area_unitaria} m²`),
                el('td', {}, v.aplica ? chip('Sí', 'ok') : chip('No', 'alerta')),
                el('td', { class: 'chico suave' }, v.motivo))))))));
      if (insertar) {
        control.cerrar();
        await recargar(proyectoId);
        exito(`${r.creadas} deducción(es) agregadas al sustento.`);
      }
    } catch (e) { avisoError(e.message); }
  };

  const control = modal({
    titulo: 'Descontar vanos',
    ancho: 'ancho',
    cuerpo: el('div', {},
      avisoCaja('info', 'El umbral de descuento depende de la familia normativa de la partida, '
        + 'no de un interruptor global. Los vanos que NO se descuentan también quedan listados, '
        + 'con el motivo: es lo que el revisor busca.'),
      el('div', { class: 'mt2' }, campo('Familia normativa', selectorFamilia)),
      explicacion,
      el('div', { class: 'panel mt2' },
        el('div', { class: 'panel-cuerpo compacto' },
          el('table', { class: 'tabla densa' },
            el('thead', {}, el('tr', {},
              el('th', {}, 'Descripción'), el('th', {}, 'Cantidad'),
              el('th', {}, 'Ancho (m)'), el('th', {}, 'Alto (m)'), el('th', {}))),
            cuerpoTabla)),
        el('div', { class: 'panel-cuerpo' },
          el('button', { class: 'btn chico', onclick: () => agregar() }, icono('mas'), 'Agregar vano'))),
      resultado),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', { class: 'btn', onclick: () => evaluar(false) }, icono('calidad'), 'Solo evaluar'),
      el('button', { class: 'btn primario', onclick: () => evaluar(true) },
        icono('check'), 'Aplicar descuentos'),
    ],
  });
}

async function verTrazabilidad(item) {
  const t = await api.obtener(`/items/${item.id}/trazabilidad`);
  modal({
    titulo: `¿De dónde sale este metrado?`,
    ancho: 'ancho',
    cuerpo: el('div', {},
      el('div', { class: 'fila entre mb2' },
        el('div', {},
          el('div', { class: 'fuerte' }, t.item.descripcion),
          el('div', { class: 'chico apagado mono' }, t.item.codigo || '')),
        el('div', { estilo: { textAlign: 'right' } },
          el('div', { class: 'valor mono fuerte', estilo: { fontSize: '22px' } },
            metrado(t.resumen.total)),
          el('div', { class: 'chico apagado' }, t.item.unidad))),

      t.regla_medicion ? cita({
        texto: t.regla_medicion, codigo: t.item.codigo, etiqueta: t.etiqueta_fuente,
      }) : null,

      el('div', { class: 'fila envuelve mt2', estilo: { gap: '6px' } },
        ...Object.entries(t.origenes).map(([o, n]) => chip(`${n} ${o.replace('_', ' ')}`,
          o === 'supuesto' ? 'alerta' : o === 'detectado_ia' ? 'info' : ''))),

      el('div', { class: 'panel mt2' },
        el('div', { class: 'panel-cuerpo compacto' },
          el('table', { class: 'tabla densa' },
            el('thead', {}, el('tr', {},
              el('th', {}, 'Fila'), el('th', {}, 'Ubicación'), el('th', {}, 'Cálculo'),
              el('th', { class: 'num' }, 'Parcial'), el('th', {}, 'Origen'),
              el('th', {}, 'Lámina'), el('th', {}, 'Fecha'))),
            el('tbody', {}, ...t.detalle.map((d) => el('tr', {},
              el('td', {}, d.descripcion || '—'),
              el('td', { class: 'chico' }, d.ubicacion || '—'),
              el('td', { class: 'mono chico' }, d.sustento || d.error || '—'),
              el('td', { class: 'num mono' }, d.parcial ?? '—'),
              el('td', {}, chip(d.origen.replace('_', ' '),
                d.origen === 'supuesto' ? 'alerta' : '')),
              el('td', { class: 'mono chico' }, d.lamina || '—'),
              el('td', { class: 'chico apagado' }, d.fecha || '—'))))))),

      ...t.detalle.filter((d) => d.supuesto).map((d) => avisoCaja('alerta', el('div', {},
        el('strong', {}, `Supuesto en «${d.descripcion}»: `), d.supuesto))),

      t.nota_desperdicio ? avisoCaja('info', el('div', { class: 'mt2' },
        el('strong', {}, 'Sobre el desperdicio: '), t.nota_desperdicio.explicacion)) : null),
    pie: [el('button', { class: 'btn primario', onclick: (e) => e.target.closest('.velo').remove() }, 'Cerrar')],
  });
}

function verFila(f, item) {
  modal({
    titulo: 'Cálculo de la fila',
    cuerpo: el('div', {},
      el('div', { class: 'fuerte mb1' }, f.descripcion || 'Fila sin descripción'),
      el('div', { class: 'panel' }, el('div', { class: 'panel-cuerpo' },
        el('div', { class: 'mono', estilo: { fontSize: '13px', lineHeight: '2' } },
          ...(f.pasos?.length ? f.pasos.map((p) => el('div', {}, p))
            : [el('div', { class: 'apagado' }, 'Sin pasos: la fila no se pudo calcular.')])))),
      el('div', { class: 'fila entre mt2' },
        el('span', { class: 'suave' }, 'Parcial'),
        el('span', { class: 'mono fuerte', estilo: { fontSize: '17px' } },
          `${f.parcial ?? '—'} ${item.unidad || ''}`)),
      f.aviso ? avisoCaja('alerta', f.aviso) : null,
      f.error ? avisoCaja('peligro', f.error) : null,
      f.faltantes?.length
        ? avisoCaja('alerta', `Faltan estos datos: ${f.faltantes.join(', ')}. `
          + 'La fila queda fuera del total; METRA AI no la completa con ceros.')
        : null,
      f.supuesto ? avisoCaja('alerta', el('div', {}, el('strong', {}, 'Supuesto: '), f.supuesto)) : null,
      el('div', { class: 'chico apagado mt2' },
        `Origen: ${f.origen} · Lámina: ${f.lamina || '—'} · Fecha: ${f.fecha || '—'}`)),
    pie: [el('button', { class: 'btn primario', onclick: (e) => e.target.closest('.velo').remove() }, 'Cerrar')],
  });
}

// ------------------------------------------------------------ Propiedades

function dibujarPropiedades(zona, item, resumen, familia, editable, proyectoId) {
  const guardar = async (campoClave, valor) => {
    try {
      await api.actualizar(`/items/${item.id}`, { [campoClave]: valor });
      await recargar(proyectoId);
    } catch (e) { avisoError(e.message); }
  };

  const entradaTexto = (valor, alGuardar, atributos = {}) => {
    const nodo = el('input', { type: 'text', value: valor ?? '', disabled: !editable, ...atributos });
    nodo.onchange = () => alGuardar(nodo.value.trim() || null);
    return nodo;
  };

  vaciar(zona).append(
    el('div', { class: 'zona-cabecera' }, icono('config'), 'Propiedades de la partida'),
    el('div', { estilo: { padding: '14px' } },

      el('div', { class: 'kpi mb2', estilo: { padding: '12px' } },
        el('span', { class: 'etiqueta' }, 'Metrado total'),
        el('span', { class: 'valor mono' }, `${metrado(resumen.total)}`),
        el('span', { class: 'nota' },
          `${item.unidad || '—'} · ${resumen.filas_ok} fila(s) de sustento`)),

      resumen.deducciones && parseFloat(resumen.deducciones) !== 0
        ? el('div', { class: 'fila entre chico mb2' },
            el('span', { class: 'suave' }, 'Bruto / deducciones'),
            el('span', { class: 'mono' },
              `${metrado(resumen.bruto)} / ${metrado(resumen.deducciones)}`))
        : null,

      campo('Descripción', entradaTexto(item.descripcion, (v) => guardar('descripcion', v))),
      el('div', { class: 'fila-campos' },
        campo('Unidad', entradaTexto(item.unidad, (v) => guardar('unidad', v))),
        campo('Código de norma', entradaTexto(item.codigo, (v) => guardar('codigo', v)))),

      campo('Familia de descuento de vanos',
        (() => {
          const s = el('select', { disabled: !editable },
            ...estado.referencia.reglas.familias.map((f) => el('option', {
              value: f.clave, selected: f.clave === item.familia_descuento,
            }, f.nombre)));
          s.onchange = () => guardar('familia_descuento', s.value);
          return s;
        })()),

      familia ? cita({
        texto: familia.cita, codigo: familia.codigo,
        etiqueta: `umbral ${familia.umbral_m2} m²`,
      }) : null,

      el('div', { class: 'sep' }),

      el('div', { class: 'fila-campos' },
        campo('Precio unitario',
          entradaTexto(item.precio_unitario, (v) => guardar('precio_unitario', v ? parsear(v) : null),
            { class: 'num' })),
        campo('Desperdicio %',
          entradaTexto(item.desperdicio_pct, (v) => guardar('desperdicio_pct', v ? parsear(v) : null),
            { class: 'num' }))),
      el('div', { class: 'chico apagado', estilo: { marginTop: '-8px', marginBottom: '14px' } },
        'El desperdicio no altera el metrado: solo la cantidad a comprar.'),

      el('div', { class: 'fila-campos' },
        campo('Cantidad contratada',
          entradaTexto(item.cantidad_contratada, (v) => guardar('cantidad_contratada', v ? parsear(v) : null),
            { class: 'num' })),
        campo('Cantidad ejecutada',
          entradaTexto(item.cantidad_ejecutada, (v) => guardar('cantidad_ejecutada', v ? parsear(v) : null),
            { class: 'num' }))),

      item.regla_medicion ? el('div', { class: 'mt2' },
        el('div', { class: 'chico fuerte mb1' }, 'Regla de medición de la norma'),
        cita({ texto: item.regla_medicion, codigo: item.codigo, etiqueta: item.etiqueta_fuente })) : null,

      el('div', { class: 'sep' }),
      campo('Observaciones',
        (() => {
          const t = el('textarea', { disabled: !editable, value: item.observaciones || '' });
          t.onchange = () => guardar('observaciones', t.value.trim() || null);
          return t;
        })()),
    ));
}

async function cambiarEstado(item, nuevoEstado, proyectoId) {
  try {
    if (nuevoEstado === 'aprobado') {
      const ok = await confirmar({
        titulo: 'Aprobar partida',
        mensaje: `Se aprobará «${item.descripcion}» y quedará bloqueada.`,
        detalle: 'Una partida aprobada no se puede editar ni eliminar hasta que un '
          + 'supervisor la desbloquee. Queda registrado quién aprobó y cuándo.',
        aceptar: 'Aprobar',
      });
      if (!ok) return recargar(proyectoId);
    }
    await api.crear(`/items/${item.id}/estado`, { estado: nuevoEstado });
    exito(`Partida marcada como ${nuevoEstado}.`);
    await recargar(proyectoId);
  } catch (e) {
    avisoError(e.message);
    await recargar(proyectoId);
  }
}

function nuevaPartida(proyectoId) {
  const descripcion = el('input', { type: 'text', placeholder: 'Descripción de la partida' });
  const unidad = el('input', { type: 'text', placeholder: 'm2', value: 'm2' });
  const tipo = el('select', {},
    el('option', { value: 'partida' }, 'Partida'),
    el('option', { value: 'titulo' }, 'Título / capítulo'));
  const esp = el('select', {},
    ...estado.referencia.especialidades.map((e) => el('option', { value: e.clave }, e.nombre)));
  const buscador = el('input', { type: 'search', placeholder: 'Buscar en el catálogo normativo…' });
  const resultados = el('div', { estilo: { maxHeight: '220px', overflow: 'auto' } });
  let catalogoId = null;

  let temporizador;
  buscador.oninput = () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(async () => {
      const q = buscador.value.trim();
      if (q.length < 2) return resultados.replaceChildren();
      const r = await api.obtener(`/catalogo/partidas?q=${encodeURIComponent(q)}&por_pagina=25`);
      resultados.replaceChildren(...r.partidas.map((p) => el('div', {
        class: 'arbol-nodo',
        onclick: () => {
          catalogoId = p.id;
          descripcion.value = p.descripcion;
          unidad.value = p.unidad;
          esp.value = p.especialidad;
          [...resultados.children].forEach((c) => c.classList.remove('activo'));
          resultados.querySelector(`[data-id="${p.id}"]`)?.classList.add('activo');
        },
        datos: { id: p.id },
      },
        puntoEspecialidad(p.color),
        el('span', { class: 'etiqueta' },
          el('span', { class: 'mono chico apagado' }, p.codigo + '  '), p.descripcion),
        chip(p.unidad),
        p.verificado ? chip('norma', 'ok') : null)));
    }, 250);
  };

  const control = modal({
    titulo: 'Agregar partida',
    ancho: 'ancho',
    cuerpo: el('div', {},
      campo('Buscar en el catálogo de la norma', buscador,
        'Elegir del catálogo trae el código, la unidad y la regla de medición literal.'),
      resultados,
      el('div', { class: 'sep' }),
      el('div', { class: 'fila-campos' },
        campo('Tipo', tipo), campo('Unidad', unidad), campo('Especialidad', esp)),
      campo('Descripción', descripcion)),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          if (!descripcion.value.trim()) return aviso('Escriba la descripción.', 'alerta');
          try {
            const r = await api.crear(`/proyectos/${proyectoId}/items`, {
              tipo: tipo.value,
              descripcion: descripcion.value.trim(),
              unidad: tipo.value === 'partida' ? unidad.value.trim() : null,
              especialidad: esp.value,
              catalogo_id: catalogoId,
            });
            control.cerrar();
            itemActivo = r.item.id;
            await recargar(proyectoId);
            exito('Partida agregada.');
          } catch (e) { avisoError(e.message); }
        },
      }, icono('mas'), 'Agregar'),
    ],
  });
}
