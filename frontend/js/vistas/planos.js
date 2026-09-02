// Visor de planos: zoom, desplazamiento, calibración de escala y medición.
//
// Todas las coordenadas de calibración y de trazos se guardan en píxeles del
// render canónico del servidor. El zoom de pantalla es una transformación
// visual: una medición hecha al 400% vale exactamente lo mismo que al 100%.

import { api } from '../core/api.js';
import { estado, puede, ubicacionesPlanas, especialidad } from '../core/estado.js';
import { metrado, num, parsear, fecha } from '../core/fmt.js';
import {
  el, vaciar, icono, cargando, vacio, chip, campo, modal, confirmar,
  avisoCaja, exito, aviso, error as avisoError, puntoEspecialidad,
} from '../ui/base.js';

const HERRAMIENTAS = {
  mano: { icono: 'mano', etiqueta: 'Desplazar', puntos: 0 },
  longitud: { icono: 'regla', etiqueta: 'Medir longitud', puntos: -1 },
  area: { icono: 'poligono', etiqueta: 'Medir área', puntos: -1 },
  conteo: { icono: 'conteo', etiqueta: 'Contar elementos', puntos: -1 },
  calibrar: { icono: 'calibrar', etiqueta: 'Calibrar escala', puntos: 2 },
};

let planoActivo = null;
let herramienta = 'mano';
let zoom = 1;
let desplazamiento = { x: 0, y: 0 };
let puntos = [];
let marcados = [];
let planoDatos = null;

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const taller = el('div', { class: 'taller sin-abajo' });
  const zonaIzq = el('div', { class: 'zona-izq' });
  const zonaCentro = el('div', { class: 'zona-centro' });
  const zonaDer = el('div', { class: 'zona-der' });
  taller.append(zonaIzq, zonaCentro, zonaDer);
  contenedor.append(taller);
  contenedor.classList.add('sin-scroll');

  vaciar(zonaCentro).append(cargando());
  const [archivos, planos] = await Promise.all([
    api.obtener(`/proyectos/${proyectoId}/archivos`),
    api.obtener(`/proyectos/${proyectoId}/planos`),
  ]);

  dibujarLista(zonaIzq, proyectoId, archivos.archivos, planos.planos, () =>
    render(vaciar(contenedor), params));

  if (!planos.planos.length) {
    vaciar(zonaCentro).append(vacio({
      icono: 'plano',
      titulo: 'No hay planos cargados',
      mensaje: 'Suba un PDF, una imagen o un DXF. De los PDF se extrae cada página como '
        + 'un plano medible; de los DXF se leen capas y longitudes reales.',
      acciones: [el('button', {
        class: 'btn primario',
        onclick: () => subirArchivo(proyectoId, () => render(vaciar(contenedor), params)),
      }, icono('subir'), 'Subir archivo')],
    }));
    vaciar(zonaDer);
    return;
  }

  if (!planoActivo || !planos.planos.some((p) => p.id === planoActivo)) {
    planoActivo = planos.planos[0].id;
  }
  await abrirPlano(zonaCentro, zonaDer, proyectoId, planos.planos);
}

// ------------------------------------------------------------------- Lista

function dibujarLista(zona, proyectoId, archivos, planos, recargar) {
  const porArchivo = new Map();
  for (const p of planos) {
    if (!porArchivo.has(p.archivo_id)) porArchivo.set(p.archivo_id, []);
    porArchivo.get(p.archivo_id).push(p);
  }

  const lista = el('div', { class: 'arbol' });
  for (const a of archivos) {
    const paginas = porArchivo.get(a.id) || [];
    lista.append(
      el('div', { class: 'arbol-nodo', estilo: { cursor: 'default' } },
        icono('archivo'),
        el('span', { class: 'etiqueta', title: a.nombre }, a.nombre),
        chip(a.tipo),
        el('button', {
          class: 'btn chico fantasma', title: 'Eliminar archivo',
          onclick: async (e) => {
            e.stopPropagation();
            const ok = await confirmar({
              titulo: 'Eliminar archivo',
              mensaje: `Se eliminará «${a.nombre}» y sus ${a.paginas} plano(s).`,
              detalle: 'Si alguna fila de metrado cita un plano de este archivo, la '
                + 'eliminación se bloquea para no dejar cantidades sin sustento.',
              aceptar: 'Eliminar', peligroso: true,
            });
            if (!ok) return;
            try {
              await api.borrar(`/archivos/${a.id}`);
              exito('Archivo eliminado.');
              recargar();
            } catch (err) { avisoError(err.message); }
          },
        }, icono('borrar'))),
      a.mensaje ? el('div', { class: 'chico apagado', estilo: { padding: '0 12px 6px 30px' } },
        a.mensaje) : null,
      el('div', { class: 'arbol-hijos' }, ...paginas.map((p) => el('div', {
        class: `arbol-nodo ${planoActivo === p.id ? 'activo' : ''}`,
        onclick: async () => {
          planoActivo = p.id;
          zoom = 1; desplazamiento = { x: 0, y: 0 }; puntos = [];
          await abrirPlano(document.querySelector('.zona-centro'),
            document.querySelector('.zona-der'), proyectoId, planos);
          dibujarLista(zona, proyectoId, archivos, planos, recargar);
        },
      },
        icono('plano'),
        el('span', { class: 'etiqueta' },
          el('span', { class: 'mono chico apagado' }, `p.${p.pagina}  `),
          p.codigo || p.titulo || `Página ${p.pagina}`),
        p.calibrado ? icono('check', 'flecha') : chip('sin escala', 'alerta')))));
  }

  vaciar(zona).append(
    el('div', { class: 'zona-cabecera' },
      icono('carpeta'), el('span', { class: 'crecer' }, 'Archivos y planos'),
      puede('crear') ? el('button', {
        class: 'btn chico fantasma', title: 'Subir archivo',
        onclick: () => subirArchivo(proyectoId, recargar),
      }, icono('subir')) : null),
    archivos.length ? lista : el('p', { class: 'apagado chico', estilo: { padding: '16px' } },
      'Todavía no hay archivos.'));
}

function subirArchivo(proyectoId, recargar) {
  const archivo = el('input', {
    type: 'file', accept: '.pdf,.png,.jpg,.jpeg,.webp,.dxf,.dwg,.ifc,.rvt,.xlsx,.csv',
  });
  const esp = el('select', {},
    el('option', { value: '' }, 'Sin especialidad'),
    ...estado.referencia.especialidades.map((e) => el('option', { value: e.clave }, e.nombre)));

  const control = modal({
    titulo: 'Subir archivo',
    cuerpo: el('div', {},
      avisoCaja('info', el('div', {},
        el('strong', {}, 'PDF, imágenes y DXF se pueden medir directamente. '),
        'DWG y RVT son formatos propietarios sin lector abierto: se guardan, pero para '
        + 'medirlos hay que exportarlos antes a DXF o IFC.')),
      el('div', { class: 'mt2' }, campo('Archivo', archivo)),
      campo('Especialidad', esp, 'Determina el color con el que se marcan sus mediciones.')),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async (e) => {
          if (!archivo.files.length) return aviso('Elija un archivo.', 'alerta');
          e.target.disabled = true;
          e.target.textContent = 'Procesando…';
          const datos = new FormData();
          datos.append('archivo', archivo.files[0]);
          datos.append('especialidad', esp.value);
          try {
            const r = await api.subir(`/proyectos/${proyectoId}/archivos`, datos);
            control.cerrar();
            if (r.repetido) aviso(r.mensaje, 'alerta');
            else exito(r.mensaje || `Archivo cargado: ${r.paginas} plano(s).`);
            recargar();
          } catch (err) {
            avisoError(err.message);
            e.target.disabled = false;
            e.target.textContent = 'Subir';
          }
        },
      }, icono('subir'), 'Subir'),
    ],
  });
}

// ------------------------------------------------------------------- Visor

async function abrirPlano(zonaCentro, zonaDer, proyectoId, planos) {
  vaciar(zonaCentro).append(cargando());
  const datos = await api.obtener(`/planos/${planoActivo}/marcados`);
  planoDatos = datos.plano;
  marcados = datos.marcados;

  const lienzo = el('div', { class: 'visor-lienzo' });
  const imagen = el('img', { src: `/api/planos/${planoActivo}/imagen`, alt: 'Plano' });
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'visor-svg');
  lienzo.append(imagen, svg);

  const visor = el('div', { class: 'visor' }, lienzo);

  if (!planoDatos.calibrado) {
    visor.append(el('div', { class: 'visor-aviso' },
      'Este plano no está calibrado: mida una distancia conocida antes de medir nada más.'));
  }

  const etiquetaZoom = el('span', { class: 'visor-zoom' }, '100%');
  const aplicar = () => {
    lienzo.style.transform =
      `translate(${desplazamiento.x}px, ${desplazamiento.y}px) scale(${zoom})`;
    etiquetaZoom.textContent = `${Math.round(zoom * 100)}%`;
    svg.setAttribute('width', planoDatos.ancho_px || 2000);
    svg.setAttribute('height', planoDatos.alto_px || 2000);
    redibujarTrazos(svg);
  };

  // --- Interacción
  let arrastrando = false;
  let inicio = { x: 0, y: 0 };

  visor.addEventListener('mousedown', (e) => {
    if (herramienta === 'mano' || e.button === 1) {
      arrastrando = true;
      inicio = { x: e.clientX - desplazamiento.x, y: e.clientY - desplazamiento.y };
      visor.classList.add('arrastrando');
    }
  });
  window.addEventListener('mousemove', (e) => {
    if (!arrastrando) return;
    desplazamiento = { x: e.clientX - inicio.x, y: e.clientY - inicio.y };
    aplicar();
  });
  window.addEventListener('mouseup', () => {
    arrastrando = false;
    visor.classList.remove('arrastrando');
  });

  visor.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = visor.getBoundingClientRect();
    const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    const nuevo = Math.max(0.08, Math.min(12, zoom * factor));
    // Zoom hacia el puntero: el punto bajo el cursor no se mueve.
    const cx = e.clientX - rect.left - desplazamiento.x;
    const cy = e.clientY - rect.top - desplazamiento.y;
    desplazamiento.x -= cx * (nuevo / zoom - 1);
    desplazamiento.y -= cy * (nuevo / zoom - 1);
    zoom = nuevo;
    aplicar();
  }, { passive: false });

  visor.addEventListener('click', async (e) => {
    if (herramienta === 'mano') return;
    const rect = lienzo.getBoundingClientRect();
    const punto = [(e.clientX - rect.left) / zoom, (e.clientY - rect.top) / zoom];
    puntos.push(punto);
    aplicar();

    if (herramienta === 'calibrar' && puntos.length === 2) {
      dialogoCalibrar(proyectoId, planos, zonaCentro, zonaDer);
    }
  });

  visor.addEventListener('dblclick', async () => {
    if (['longitud', 'area'].includes(herramienta) && puntos.length >= 2) {
      await guardarMarcado(proyectoId, zonaCentro, zonaDer, planos);
    }
  });

  const barra = el('div', { class: 'visor-barra' },
    ...Object.entries(HERRAMIENTAS).map(([clave, h]) => el('button', {
      class: `btn icono ${herramienta === clave ? 'activo' : ''}`,
      title: h.etiqueta,
      onclick: (ev) => {
        herramienta = clave;
        puntos = [];
        [...barra.querySelectorAll('.btn')].forEach((b) => b.classList.remove('activo'));
        ev.currentTarget.classList.add('activo');
        visor.classList.toggle('midiendo', clave !== 'mano');
        aplicar();
      },
    }, icono(h.icono))),
    el('div', { class: 'sep' }),
    el('button', {
      class: 'btn icono', title: 'Alejar',
      onclick: () => { zoom = Math.max(0.08, zoom / 1.25); aplicar(); },
    }, icono('zoommenos')),
    etiquetaZoom,
    el('button', {
      class: 'btn icono', title: 'Acercar',
      onclick: () => { zoom = Math.min(12, zoom * 1.25); aplicar(); },
    }, icono('zoommas')),
    el('button', {
      class: 'btn icono', title: 'Ajustar a la pantalla',
      onclick: () => {
        const rect = visor.getBoundingClientRect();
        zoom = Math.min(rect.width / (planoDatos.ancho_px || 1),
          rect.height / (planoDatos.alto_px || 1)) * 0.94;
        desplazamiento = {
          x: (rect.width - (planoDatos.ancho_px || 0) * zoom) / 2,
          y: (rect.height - (planoDatos.alto_px || 0) * zoom) / 2,
        };
        aplicar();
      },
    }, icono('ajustar')),
    el('div', { class: 'sep' }),
    el('button', {
      class: 'btn icono', title: 'Terminar la medición (o doble clic)',
      onclick: () => guardarMarcado(proyectoId, zonaCentro, zonaDer, planos),
    }, icono('check')),
    el('button', {
      class: 'btn icono', title: 'Descartar los puntos marcados',
      onclick: () => { puntos = []; aplicar(); },
    }, icono('cerrar')));

  visor.append(barra);
  vaciar(zonaCentro).append(visor);

  imagen.onload = () => {
    planoDatos.ancho_px = imagen.naturalWidth;
    planoDatos.alto_px = imagen.naturalHeight;
    const rect = visor.getBoundingClientRect();
    zoom = Math.min(rect.width / imagen.naturalWidth, rect.height / imagen.naturalHeight) * 0.94;
    desplazamiento = {
      x: (rect.width - imagen.naturalWidth * zoom) / 2,
      y: (rect.height - imagen.naturalHeight * zoom) / 2,
    };
    aplicar();
  };
  imagen.onerror = () => {
    vaciar(zonaCentro).append(avisoCaja('peligro',
      'No se pudo generar la imagen de este plano. Puede que el archivo original se haya movido.'));
  };

  dibujarPropiedades(zonaDer, proyectoId, planos, zonaCentro);
}

function redibujarTrazos(svg) {
  vaciar(svg);
  const ns = 'http://www.w3.org/2000/svg';

  const dibujar = (lista, color, opacidad, etiqueta) => {
    for (const m of lista) {
      const pts = m.puntos || [];
      if (!pts.length) continue;
      if (m.tipo === 'conteo') {
        for (const [x, y] of pts) {
          const c = document.createElementNS(ns, 'circle');
          c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 7);
          c.setAttribute('fill', color); c.setAttribute('fill-opacity', opacidad);
          c.setAttribute('stroke', '#fff'); c.setAttribute('stroke-width', '2');
          svg.append(c);
        }
        continue;
      }
      const forma = document.createElementNS(ns, m.tipo === 'area' ? 'polygon' : 'polyline');
      forma.setAttribute('points', pts.map((p) => p.join(',')).join(' '));
      forma.setAttribute('fill', m.tipo === 'area' ? color : 'none');
      forma.setAttribute('fill-opacity', m.tipo === 'area' ? '0.22' : '0');
      forma.setAttribute('stroke', color);
      forma.setAttribute('stroke-width', '3');
      forma.setAttribute('stroke-linejoin', 'round');
      svg.append(forma);

      if (etiqueta && m.valor) {
        const t = document.createElementNS(ns, 'text');
        t.setAttribute('x', pts[0][0] + 10);
        t.setAttribute('y', pts[0][1] - 8);
        t.setAttribute('fill', color);
        t.setAttribute('font-size', '15');
        t.setAttribute('font-weight', '700');
        t.setAttribute('paint-order', 'stroke');
        t.setAttribute('stroke', '#fff');
        t.setAttribute('stroke-width', '4');
        t.textContent = `${m.valor} ${m.unidad || ''}`;
        svg.append(t);
      }
    }
  };

  dibujar(marcados, null, 0.22, true);
  // Los guardados usan su propio color; se repinta con el color de cada uno.
  vaciar(svg);
  for (const m of marcados) {
    dibujar([m], m.color || '#1d5bd8', 0.22, true);
  }
  if (puntos.length) {
    dibujar([{ tipo: herramienta === 'calibrar' ? 'longitud' : herramienta, puntos }],
      '#d6455d', 0.18, false);
    for (const [x, y] of puntos) {
      const c = document.createElementNS(ns, 'circle');
      c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 5);
      c.setAttribute('fill', '#d6455d'); c.setAttribute('stroke', '#fff');
      c.setAttribute('stroke-width', '2');
      svg.append(c);
    }
  }
}

function dialogoCalibrar(proyectoId, planos, zonaCentro, zonaDer) {
  const distancia = el('input', { type: 'text', placeholder: '5.00', class: 'num' });
  const unidad = el('select', {},
    ...['m', 'cm', 'mm', 'ft', 'in'].map((u) => el('option', { value: u }, u)));
  const escalaTexto = el('input', { type: 'text', placeholder: '1:50' });

  const px = Math.hypot(puntos[1][0] - puntos[0][0], puntos[1][1] - puntos[0][1]);

  const control = modal({
    titulo: 'Calibrar la escala del plano',
    ancho: 'angosto',
    cuerpo: el('div', {},
      avisoCaja('info', el('div', {},
        `Marcó una distancia de ${Math.round(px)} px sobre el plano. `,
        el('strong', {}, 'Escriba cuánto mide en la realidad.'),
        el('div', { class: 'chico mt1' },
          'Use una cota larga y conocida: mientras más larga, más exacta queda la escala.'))),
      el('div', { class: 'fila-campos mt2' },
        campo('Distancia real', distancia), campo('Unidad', unidad)),
      campo('Escala indicada en el plano', escalaTexto, 'Opcional, solo como referencia.')),
    pie: [
      el('button', {
        class: 'btn', onclick: () => { puntos = []; control.cerrar(); },
      }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          if (!distancia.value.trim()) return aviso('Escriba la distancia real.', 'alerta');
          try {
            const r = await api.actualizar(`/planos/${planoActivo}/calibrar`, {
              p1: puntos[0], p2: puntos[1],
              distancia_real: parsear(distancia.value),
              unidad: unidad.value,
              escala_texto: escalaTexto.value.trim() || null,
            });
            puntos = [];
            herramienta = 'mano';
            control.cerrar();
            exito(`Plano calibrado${r.escala_estimada ? ` (≈ ${r.escala_estimada})` : ''}.`);
            await abrirPlano(zonaCentro, zonaDer, proyectoId, planos);
          } catch (e) { avisoError(e.message); }
        },
      }, icono('check'), 'Calibrar'),
    ],
    alCerrar: () => { puntos = []; },
  });
}

async function guardarMarcado(proyectoId, zonaCentro, zonaDer, planos) {
  if (herramienta === 'mano' || herramienta === 'calibrar') return;
  if (!puntos.length) return aviso('Marque primero los puntos sobre el plano.', 'alerta');
  if (herramienta === 'area' && puntos.length < 3) {
    return aviso('Un área necesita al menos tres puntos.', 'alerta');
  }
  if (!planoDatos.calibrado) {
    return aviso('Calibre el plano antes de medir: sin escala la medición sería inventada.', 'alerta');
  }

  const etiqueta = el('input', { type: 'text', placeholder: 'Muros del eje A' });
  const esp = el('select', {},
    el('option', { value: '' }, 'Sin especialidad'),
    ...estado.referencia.especialidades.map((e) => el('option', { value: e.clave }, e.nombre)));
  const selectorPartida = el('select', {}, el('option', { value: '' }, 'Solo marcar, sin partida'));
  const selectorUbicacion = el('select', {},
    el('option', { value: '' }, 'Sin ubicación'),
    ...ubicacionesPlanas().map((u) => el('option', { value: u.id },
      `${'— '.repeat(u.nivel)}${u.nombre}`)));

  const hoja = await api.obtener(`/proyectos/${proyectoId}/metrados`);
  const aplanar = (nodos, salida = []) => {
    for (const n of nodos) {
      if (n.tipo === 'partida') salida.push(n);
      aplanar(n.hijos || [], salida);
    }
    return salida;
  };
  const unidadEsperada = { longitud: 'm', area: 'm2', conteo: 'und' }[herramienta];
  for (const p of aplanar(hoja.items)) {
    selectorPartida.append(el('option', { value: p.id },
      `${p.item}  ${p.descripcion}  (${p.unidad})`
      + (p.unidad === unidadEsperada ? '' : '  ⚠ unidad distinta')));
  }

  const control = modal({
    titulo: `Guardar medición (${HERRAMIENTAS[herramienta].etiqueta.toLowerCase()})`,
    cuerpo: el('div', {},
      avisoCaja('info', `Se medirá con la escala calibrada de este plano. `
        + `La fila que se cree quedará vinculada a «${planoDatos.codigo || planoDatos.titulo}».`),
      el('div', { class: 'mt2' }, campo('Etiqueta de la medición', etiqueta)),
      campo('Especialidad', esp, 'Define el color del trazo sobre el plano.'),
      campo('Agregar como fila de metrado en', selectorPartida,
        'Si elige una partida, se crea la fila de sustento con esta medición y su lámina.'),
      campo('Ubicación', selectorUbicacion)),
    pie: [
      el('button', { class: 'btn', onclick: () => { puntos = []; control.cerrar(); } }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          try {
            const r = await api.crear(`/planos/${planoActivo}/marcados`, {
              tipo: herramienta, puntos,
              etiqueta: etiqueta.value.trim() || null,
              especialidad: esp.value || null,
              item_id: selectorPartida.value || null,
              ubicacion_id: selectorUbicacion.value || null,
            });
            puntos = [];
            control.cerrar();
            exito(`Medición guardada: ${r.marcado.valor} ${r.marcado.unidad}`
              + (r.medicion_id ? ' y agregada a la partida.' : '.'));
            await abrirPlano(zonaCentro, zonaDer, proyectoId, planos);
          } catch (e) { avisoError(e.message); }
        },
      }, icono('guardar'), 'Guardar'),
    ],
    alCerrar: () => { puntos = []; },
  });
}

function dibujarPropiedades(zona, proyectoId, planos, zonaCentro) {
  const p = planoDatos;
  const guardar = async (campoClave, valor) => {
    try {
      await api.actualizar(`/planos/${planoActivo}`, { [campoClave]: valor });
      exito('Plano actualizado.');
    } catch (e) { avisoError(e.message); }
  };

  const codigo = el('input', { type: 'text', value: p.codigo || '' });
  codigo.onchange = () => guardar('codigo', codigo.value.trim() || null);
  const titulo = el('input', { type: 'text', value: p.titulo || '' });
  titulo.onchange = () => guardar('titulo', titulo.value.trim() || null);

  vaciar(zona).append(
    el('div', { class: 'zona-cabecera' }, icono('config'), 'Plano'),
    el('div', { estilo: { padding: '14px' } },
      campo('Código de lámina', codigo),
      campo('Título', titulo),

      p.calibrado
        ? el('div', { class: 'aviso-caja ok' }, icono('check'), el('div', {},
            el('strong', {}, 'Plano calibrado. '),
            el('div', { class: 'chico mt1' },
              `${p.calibracion?.distancia_real} ${p.calibracion?.unidad} = `
              + `${Math.round(p.calibracion?.distancia_px || 0)} px`),
            el('div', { class: 'chico' },
              `Por ${p.calibracion?.por || '—'} · ${fecha(p.calibracion?.fecha)}`)))
        : el('div', { class: 'aviso-caja alerta' }, icono('alerta'), el('div', {},
            el('strong', {}, 'Sin calibrar. '),
            'Use la herramienta de calibración y marque una distancia conocida. '
            + 'Sin escala, cualquier medición sobre este plano sería inventada.')),

      el('div', { class: 'sep' }),
      el('div', { class: 'chico fuerte mb1' }, `Mediciones sobre este plano (${marcados.length})`),
      marcados.length
        ? el('div', { class: 'col', estilo: { gap: '5px' } },
            ...marcados.map((m) => el('div', {
              class: 'fila', estilo: { padding: '6px 8px', borderRadius: '6px', background: 'var(--fondo-3)' },
            },
              puntoEspecialidad(m.color),
              el('div', { class: 'crecer', estilo: { minWidth: 0 } },
                el('div', { class: 'chico fuerte' }, m.etiqueta || m.tipo),
                el('div', { class: 'chico apagado mono' }, `${m.valor} ${m.unidad}`)),
              m.medicion_id ? chip('en partida', 'ok') : null,
              el('button', {
                class: 'btn chico fantasma',
                onclick: async () => {
                  const ok = await confirmar({
                    titulo: 'Eliminar medición',
                    mensaje: `Se eliminará «${m.etiqueta || m.tipo}» (${m.valor} ${m.unidad}).`,
                    detalle: m.medicion_id
                      ? 'Esta medición alimenta una fila de metrado. Se eliminará también esa fila.'
                      : null,
                    aceptar: 'Eliminar', peligroso: true,
                  });
                  if (!ok) return;
                  await api.borrar(`/marcados/${m.id}?borrar_medicion=${!!m.medicion_id}`);
                  exito('Medición eliminada.');
                  await abrirPlano(zonaCentro, zona, proyectoId, planos);
                },
              }, icono('borrar')))))
        : el('p', { class: 'apagado chico' }, 'Todavía no hay mediciones en este plano.')));
}
