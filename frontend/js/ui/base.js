// Piezas de interfaz compartidas: construcción de nodos, iconos, modales,
// avisos y confirmaciones. Sin dependencias externas.

import { esc } from '../core/fmt.js';

// --- Construcción de nodos ---------------------------------------------------

export function el(etiqueta, atributos = {}, ...hijos) {
  const nodo = document.createElement(etiqueta);
  for (const [k, v] of Object.entries(atributos || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') nodo.className = v;
    else if (k === 'html') nodo.innerHTML = v;
    else if (k === 'texto') nodo.textContent = v;
    else if (k === 'estilo') Object.assign(nodo.style, v);
    else if (k.startsWith('on') && typeof v === 'function') {
      nodo.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (k === 'datos') {
      for (const [dk, dv] of Object.entries(v)) nodo.dataset[dk] = dv;
    } else nodo.setAttribute(k, v === true ? '' : v);
  }
  for (const hijo of hijos.flat(4)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    nodo.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
  return nodo;
}

export function vaciar(nodo) {
  while (nodo.firstChild) nodo.removeChild(nodo.firstChild);
  return nodo;
}

// --- Iconos ------------------------------------------------------------------
// Trazos de 24×24, stroke currentColor. Uno por concepto, sin librería externa.

const TRAZOS = {
  panel: '<path d="M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z"/>',
  proyectos: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  plano: '<path d="M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2z"/><path d="M9 3v16M15 5v16"/>',
  planilla: '<path d="M3 4h18v16H3z"/><path d="M3 9h18M3 14h18M9 4v16M15 4v16"/>',
  catalogo: '<path d="M4 4h7v16H4zM13 4h7v16h-7z"/><path d="M6.5 8h2M15.5 8h2"/>',
  dinero: '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5h5M9.5 14.5h5"/>',
  calidad: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
  versiones: '<circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="12" r="2.5"/><path d="M6 8.5v7M8.5 6h4a3 3 0 0 1 3 3v.5M8.5 18h4a3 3 0 0 0 3-3v-.5"/>',
  reporte: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
  config: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 9 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.6 9a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z"/>',
  usuarios: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9"/>',
  chispa: '<path d="M12 3l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4z"/><path d="M18.5 16.5l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/>',
  buscar: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
  mas: '<path d="M12 5v14M5 12h14"/>',
  editar: '<path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5z"/>',
  borrar: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/>',
  guardar: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
  descargar: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/>',
  subir: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5M12 3v12"/>',
  cerrar: '<path d="M18 6L6 18M6 6l12 12"/>',
  flecha: '<path d="M9 6l6 6-6 6"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  alerta: '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
  regla: '<path d="M2 12l10-10 10 10-10 10z"/><path d="M7 12l1.5 1.5M10 9l1.5 1.5M13 6l1.5 1.5"/>',
  poligono: '<path d="M12 2l9 6.5-3.5 11h-11L3 8.5z"/>',
  conteo: '<circle cx="7" cy="7" r="2"/><circle cx="17" cy="7" r="2"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/><circle cx="12" cy="12" r="2"/>',
  mano: '<path d="M18 11V7a2 2 0 0 0-4 0M14 10V5a2 2 0 0 0-4 0v5M10 10V6a2 2 0 0 0-4 0v9"/><path d="M18 11a2 2 0 0 1 4 0v3a8 8 0 0 1-8 8h-2a8 8 0 0 1-8-8v-1"/>',
  zoommas: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5M11 8v6M8 11h6"/>',
  zoommenos: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5M8 11h6"/>',
  ajustar: '<path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/>',
  calibrar: '<path d="M3 17l6-6 4 4 8-8"/><path d="M3 21h18"/><circle cx="9" cy="11" r="1.5"/><circle cx="13" cy="15" r="1.5"/>',
  capas: '<path d="M12 2l10 6-10 6L2 8z"/><path d="M2 14l10 6 10-6"/>',
  deshacer: '<path d="M3 10h11a5 5 0 0 1 0 10h-3"/><path d="M7 6l-4 4 4 4"/>',
  rehacer: '<path d="M21 10H10a5 5 0 0 0 0 10h3"/><path d="M17 6l4 4-4 4"/>',
  sol: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  luna: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  menu: '<path d="M3 6h18M3 12h18M3 18h18"/>',
  filtro: '<path d="M3 4h18l-7 8v7l-4 2v-9z"/>',
  copiar: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  pegar: '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/>',
  repetir: '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
  bloqueo: '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  ojo: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
  archivo: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
  carpeta: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  edificio: '<path d="M4 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16M14 21V10h4a2 2 0 0 1 2 2v9"/><path d="M8 7h2M8 11h2M8 15h2M2 21h20"/>',
  reloj: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  enviar: '<path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>',
  libro: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  balanza: '<path d="M12 3v18M7 21h10M12 6l7 2-3.5 6h7L19 8M12 6L5 8l3.5 6h-7L5 8"/>',
  salir: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5M21 12H9"/>',
};

export function icono(nombre, clase = '') {
  const trazo = TRAZOS[nombre] || TRAZOS.info;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '1.8');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  if (clase) svg.setAttribute('class', clase);
  svg.innerHTML = trazo;
  return svg;
}

export function iconoHtml(nombre) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
    stroke-linecap="round" stroke-linejoin="round">${TRAZOS[nombre] || TRAZOS.info}</svg>`;
}

// --- Avisos ------------------------------------------------------------------

let contenedorAvisos = null;

export function aviso(mensaje, tipo = 'info', duracion = 4600) {
  if (!contenedorAvisos) {
    contenedorAvisos = el('div', { class: 'avisos' });
    document.body.append(contenedorAvisos);
  }
  const iconos = { ok: 'check', error: 'alerta', alerta: 'alerta', info: 'info' };
  const nodo = el('div', { class: `aviso ${tipo}` },
    icono(iconos[tipo] || 'info'),
    el('div', { class: 'crecer' }, mensaje));
  contenedorAvisos.append(nodo);
  const quitar = () => {
    nodo.style.opacity = '0';
    nodo.style.transform = 'translateX(24px)';
    nodo.style.transition = 'all 180ms';
    setTimeout(() => nodo.remove(), 200);
  };
  nodo.addEventListener('click', quitar);
  if (duracion) setTimeout(quitar, duracion);
  return nodo;
}

export const exito = (m) => aviso(m, 'ok');
export const error = (m) => aviso(m, 'error', 7000);

// --- Modal -------------------------------------------------------------------

export function modal({ titulo, cuerpo, pie, ancho = '', alCerrar }) {
  const velo = el('div', { class: 'velo' });
  const contenedor = el('div', { class: `modal ${ancho}` });

  const cerrar = (valor) => {
    velo.remove();
    document.removeEventListener('keydown', tecla);
    if (alCerrar) alCerrar(valor);
  };
  const tecla = (e) => { if (e.key === 'Escape') cerrar(null); };

  contenedor.append(
    el('div', { class: 'modal-cabecera' },
      el('h3', {}, titulo),
      el('div', { class: 'crecer' }),
      el('button', { class: 'btn fantasma icono', onclick: () => cerrar(null) }, icono('cerrar'))),
    el('div', { class: 'modal-cuerpo' }, cuerpo),
    pie ? el('div', { class: 'modal-pie' }, pie) : null,
  );

  velo.append(contenedor);
  velo.addEventListener('mousedown', (e) => { if (e.target === velo) cerrar(null); });
  document.addEventListener('keydown', tecla);
  document.body.append(velo);

  const primerCampo = contenedor.querySelector('input, textarea, select');
  if (primerCampo) setTimeout(() => primerCampo.focus(), 60);

  return { cerrar, contenedor };
}

export function confirmar({ titulo = '¿Confirma la acción?', mensaje, detalle,
                            aceptar = 'Confirmar', cancelar = 'Cancelar',
                            peligroso = false, exigirMotivo = false }) {
  return new Promise((resolver) => {
    let campoMotivo = null;
    const cuerpo = el('div', {},
      el('p', { class: 'mb1', estilo: { margin: '0 0 10px', lineHeight: '1.6' } }, mensaje),
      detalle ? el('div', { class: 'aviso-caja alerta mb2' }, icono('alerta'), el('div', {}, detalle)) : null,
    );
    if (exigirMotivo) {
      campoMotivo = el('textarea', {
        placeholder: 'Explique el motivo. Queda registrado en el historial.',
      });
      cuerpo.append(el('div', { class: 'campo' },
        el('label', {}, 'Motivo'), campoMotivo));
    }

    const btnAceptar = el('button', {
      class: `btn ${peligroso ? 'peligro' : 'primario'}`,
      onclick: () => {
        if (exigirMotivo && (campoMotivo.value || '').trim().length < 5) {
          campoMotivo.focus();
          aviso('Escriba el motivo (al menos 5 caracteres).', 'alerta');
          return;
        }
        control.cerrar(null);
        resolver(exigirMotivo ? { ok: true, motivo: campoMotivo.value.trim() } : true);
      },
    }, aceptar);

    const control = modal({
      titulo, cuerpo, ancho: 'angosto',
      pie: [
        el('button', { class: 'btn', onclick: () => { control.cerrar(null); } }, cancelar),
        btnAceptar,
      ],
      alCerrar: () => resolver(exigirMotivo ? { ok: false } : false),
    });
  });
}

// --- Piezas reutilizables ----------------------------------------------------

export function cargando(texto = 'Cargando…') {
  return el('div', { class: 'cargando' }, el('div', { class: 'girador' }), texto);
}

export function vacio({ icono: nombreIcono = 'carpeta', titulo, mensaje, acciones = [] }) {
  return el('div', { class: 'vacio' },
    el('div', { class: 'icono' }, icono(nombreIcono)),
    el('h3', {}, titulo),
    mensaje ? el('p', {}, mensaje) : null,
    acciones.length ? el('div', { class: 'acciones' }, ...acciones) : null);
}

export function chip(texto, tipo = '') {
  return el('span', { class: `chip ${tipo}` }, texto);
}

export function puntoEspecialidad(color) {
  return el('span', { class: 'punto-especialidad', estilo: { background: color || '#8593ab' } });
}

export function barra(porcentaje, color) {
  return el('div', { class: 'barra-progreso' },
    el('div', { estilo: { width: `${Math.max(0, Math.min(100, porcentaje))}%`, background: color } }));
}

export function panel(titulo, contenido, acciones = []) {
  return el('div', { class: 'panel' },
    titulo ? el('div', { class: 'panel-cabecera' },
      el('h2', {}, titulo),
      el('div', { class: 'crecer' }),
      ...acciones) : null,
    el('div', { class: 'panel-cuerpo' }, contenido));
}

export function campo(etiqueta, control, ayuda) {
  return el('div', { class: 'campo' },
    el('label', {}, etiqueta),
    control,
    ayuda ? el('div', { class: 'ayuda' }, ayuda) : null);
}

export function tabla(encabezados, filas, opciones = {}) {
  const { densa = false, alineacionNum = [] } = opciones;
  return el('div', { class: 'tabla-envoltura' },
    el('table', { class: `tabla ${densa ? 'densa' : ''}` },
      el('thead', {}, el('tr', {}, ...encabezados.map((h, i) =>
        el('th', { class: alineacionNum.includes(i) ? 'num' : '' }, h)))),
      el('tbody', {}, ...filas.map((f) =>
        el('tr', {}, ...f.map((c, i) =>
          el('td', { class: alineacionNum.includes(i) ? 'num' : '' },
            c instanceof Node ? c : String(c ?? ''))))))));
}

/** Cita normativa: se muestra junto a cada regla que la app aplica. */
export function cita({ texto, codigo, etiqueta }) {
  return el('div', { class: 'cita-fuente' },
    codigo ? el('span', { class: 'codigo-norma' }, codigo + ' ') : null,
    texto,
    etiqueta ? el('div', { class: 'chico apagado mt1' }, `Fuente: ${etiqueta}`) : null);
}

export function avisoCaja(tipo, contenido, nombreIcono) {
  const iconos = { info: 'info', ok: 'check', alerta: 'alerta', peligro: 'alerta' };
  return el('div', { class: `aviso-caja ${tipo}` },
    icono(nombreIcono || iconos[tipo] || 'info'),
    el('div', {}, contenido));
}

export { esc };
