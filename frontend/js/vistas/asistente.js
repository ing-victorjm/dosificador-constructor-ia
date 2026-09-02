// Asistente del proyecto. Nunca modifica sin confirmación explícita y siempre
// dice de dónde sale cada cantidad.

import { api } from '../core/api.js';
import { estado } from '../core/estado.js';
import { el, vaciar, icono, chip, cita, avisoCaja, exito, error as avisoError } from '../ui/base.js';
import { ir } from '../app.js';

let historial = [];

export async function render(contenedor, params) {
  const proyectoId = params.proyectoId || estado.proyectoId;
  const info = await api.obtener('/asistente/ejemplos');

  const mensajes = el('div', { class: 'chat-mensajes' });
  const entrada = el('textarea', {
    placeholder: 'Escriba lo que necesita. Por ejemplo: «busca las partidas sin metrar».',
    rows: 1,
  });

  const chat = el('div', { class: 'chat', estilo: { height: 'calc(100vh - var(--alto-topbar))' } },
    el('div', {
      estilo: {
        padding: '14px 18px', borderBottom: '1px solid var(--panel-borde)',
        display: 'flex', alignItems: 'center', gap: '10px',
      },
    },
      el('div', {
        class: 'marca-logo',
        estilo: { width: '30px', height: '30px', fontSize: '13px' },
      }, icono('chispa')),
      el('div', { class: 'crecer' },
        el('div', { class: 'fuerte' }, 'Asistente de METRA AI'),
        el('div', { class: 'chico apagado' }, info.aviso)),
      chip(info.modo === 'modelo' ? 'con modelo de lenguaje' : 'motor determinista')),
    mensajes,
    el('div', { class: 'chat-entrada' },
      entrada,
      el('button', {
        class: 'btn primario', onclick: () => enviar(entrada.value),
      }, icono('enviar'), 'Enviar')));

  contenedor.append(chat);
  contenedor.classList.add('sin-scroll');

  entrada.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviar(entrada.value);
    }
  });
  entrada.addEventListener('input', () => {
    entrada.style.height = 'auto';
    entrada.style.height = `${Math.min(entrada.scrollHeight, 130)}px`;
  });

  if (!historial.length) {
    burbujaAsistente({
      respuesta: 'Puedo revisar el metrado de este proyecto, explicar de dónde sale cada '
        + 'cantidad, comparar versiones y preparar exportaciones. Antes de modificar, '
        + 'eliminar o aprobar cualquier dato le pediré confirmación.',
      sugerencias: info.ejemplos,
    });
  } else {
    for (const h of historial) {
      if (h.usuario) burbujaUsuario(h.usuario);
      else burbujaAsistente(h.respuesta);
    }
  }

  function burbujaUsuario(texto) {
    mensajes.append(el('div', { class: 'burbuja usuario' }, texto));
    mensajes.scrollTop = mensajes.scrollHeight;
  }

  function burbujaAsistente(datos) {
    const burbuja = el('div', { class: 'burbuja asistente' });

    for (const parrafo of String(datos.respuesta || '').split('\n\n')) {
      burbuja.append(el('p', {}, parrafo));
    }

    if (datos.tabla?.filas?.length) {
      burbuja.append(el('div', { class: 'tabla-envoltura mt2', estilo: { maxHeight: '320px' } },
        el('table', { class: 'tabla densa' },
          el('thead', {}, el('tr', {}, ...datos.tabla.columnas.map((c) => el('th', {}, c)))),
          el('tbody', {}, ...datos.tabla.filas.map((f) =>
            el('tr', {}, ...f.map((c) => el('td', {}, c ?? '—'))))))));
    }

    for (const c of datos.citas || []) burbuja.append(cita(c));

    if (datos.acciones?.length) {
      burbuja.append(el('div', { class: 'fila envuelve mt2' },
        ...datos.acciones.map((a) => el('button', {
          class: `btn chico ${a.requiere_confirmacion ? 'primario' : ''}`,
          onclick: () => ejecutar(a),
        }, icono(a.tipo === 'descargar' ? 'descargar' : a.tipo === 'confirmar' ? 'check' : 'flecha'),
          a.descripcion))));
    }

    if (datos.sugerencias?.length) {
      burbuja.append(el('div', { class: 'fila envuelve mt2', estilo: { gap: '6px' } },
        ...datos.sugerencias.map((s) => el('button', {
          class: 'btn chico fantasma',
          estilo: { border: '1px solid var(--panel-borde)' },
          onclick: () => enviar(s),
        }, s))));
    }

    mensajes.append(burbuja);
    mensajes.scrollTop = mensajes.scrollHeight;
  }

  async function enviar(texto) {
    const limpio = (texto || '').trim();
    if (!limpio) return;
    entrada.value = '';
    entrada.style.height = 'auto';
    burbujaUsuario(limpio);
    historial.push({ usuario: limpio });

    const pensando = el('div', { class: 'burbuja asistente' },
      el('div', { class: 'fila' }, el('div', { class: 'girador' }), ' Revisando el proyecto…'));
    mensajes.append(pensando);
    mensajes.scrollTop = mensajes.scrollHeight;

    try {
      const r = await api.crear('/asistente', { texto: limpio, proyecto_id: proyectoId });
      pensando.remove();
      burbujaAsistente(r);
      historial.push({ respuesta: r });
    } catch (e) {
      pensando.remove();
      burbujaAsistente({ respuesta: `No pude responder: ${e.message}` });
    }
  }

  async function ejecutar(accion) {
    if (accion.tipo === 'ir') return ir(accion.ruta.replace('#', ''));
    if (accion.tipo === 'descargar') return api.descargar(accion.ruta.replace('/api', ''));
    if (accion.tipo === 'confirmar') {
      try {
        const r = await api.crear('/asistente/confirmar', {
          accion: accion.accion, proyecto_id: proyectoId, parametros: accion.parametros || {},
        });
        burbujaAsistente(r);
        historial.push({ respuesta: r });
        exito('Hecho.');
      } catch (e) { avisoError(e.message); }
    }
  }
}
