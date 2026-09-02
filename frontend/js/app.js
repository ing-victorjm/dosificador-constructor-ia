// Arranque, shell y enrutador por hash.
//
// Cada vista exporta `render(contenedor, params)` y se vuelve a invocar en cada
// cambio de ruta. El estado de interfaz vive en el módulo de la vista.

import { api, ErrorApi } from './core/api.js';
import { estado, iniciar, abrirProyecto, alternarTema, notificar, puede } from './core/estado.js';
import { el, vaciar, icono, cargando, aviso, error as avisoError } from './ui/base.js';

const VISTAS = {
  acceso: () => import('./vistas/acceso.js'),
  panel: () => import('./vistas/panel.js'),
  proyectos: () => import('./vistas/proyectos.js'),
  nuevo: () => import('./vistas/nuevo.js'),
  metrados: () => import('./vistas/metrados.js'),
  planos: () => import('./vistas/planos.js'),
  elementos: () => import('./vistas/elementos.js'),
  catalogo: () => import('./vistas/catalogo.js'),
  presupuesto: () => import('./vistas/presupuesto.js'),
  apu: () => import('./vistas/apu.js'),
  calidad: () => import('./vistas/calidad.js'),
  versiones: () => import('./vistas/versiones.js'),
  reportes: () => import('./vistas/reportes.js'),
  historial: () => import('./vistas/historial.js'),
  configuracion: () => import('./vistas/configuracion.js'),
  usuarios: () => import('./vistas/usuarios.js'),
  asistente: () => import('./vistas/asistente.js'),
};

const TITULOS = {
  panel: 'Panel general', proyectos: 'Proyectos', nuevo: 'Nuevo proyecto',
  metrados: 'Hoja de metrados', planos: 'Planos y mediciones', elementos: 'Elementos',
  catalogo: 'Catálogo de partidas', presupuesto: 'Presupuesto', apu: 'Análisis de precios unitarios',
  calidad: 'Control de calidad', versiones: 'Versiones', reportes: 'Reportes',
  historial: 'Historial de cambios', configuracion: 'Configuración', usuarios: 'Usuarios',
  asistente: 'Asistente',
};

const MENU_GENERAL = [
  { vista: 'panel', etiqueta: 'Panel general', icono: 'panel' },
  { vista: 'proyectos', etiqueta: 'Proyectos', icono: 'proyectos' },
  { vista: 'catalogo', etiqueta: 'Catálogo de partidas', icono: 'catalogo' },
];

const MENU_PROYECTO = [
  { vista: 'metrados', etiqueta: 'Hoja de metrados', icono: 'planilla' },
  { vista: 'planos', etiqueta: 'Planos y mediciones', icono: 'plano' },
  { vista: 'elementos', etiqueta: 'Elementos', icono: 'edificio' },
  { vista: 'presupuesto', etiqueta: 'Presupuesto', icono: 'dinero' },
  { vista: 'calidad', etiqueta: 'Control de calidad', icono: 'calidad', insignia: 'alertas' },
  { vista: 'versiones', etiqueta: 'Versiones', icono: 'versiones' },
  { vista: 'reportes', etiqueta: 'Reportes', icono: 'reporte' },
  { vista: 'historial', etiqueta: 'Historial', icono: 'reloj' },
  { vista: 'asistente', etiqueta: 'Asistente', icono: 'chispa' },
];

const MENU_SISTEMA = [
  { vista: 'usuarios', etiqueta: 'Usuarios', icono: 'usuarios' },
  { vista: 'configuracion', etiqueta: 'Configuración', icono: 'config' },
];

let contenedorPrincipal = null;
let rutaActual = null;

// --------------------------------------------------------------------- Rutas

export function ir(ruta) {
  location.hash = ruta.startsWith('#') ? ruta : '#' + ruta;
}

function analizarRuta() {
  const bruto = location.hash.replace(/^#\/?/, '');
  const partes = bruto.split('/').filter(Boolean);
  if (!partes.length) return { vista: 'panel', params: {} };
  if (partes[0] === 'proyecto' && partes[1]) {
    return { vista: partes[2] || 'metrados', params: { proyectoId: partes[1], resto: partes.slice(3) } };
  }
  return { vista: partes[0], params: { resto: partes.slice(1) } };
}

async function enrutar() {
  const { vista, params } = analizarRuta();

  if (!estado.usuario) {
    return montarAcceso();
  }

  if (params.proyectoId && params.proyectoId !== estado.proyectoId) {
    try {
      await abrirProyecto(params.proyectoId);
    } catch (e) {
      avisoError(e.message);
      return ir('/proyectos');
    }
  }

  const cargador = VISTAS[vista];
  if (!cargador) return ir('/panel');

  rutaActual = vista;
  dibujarShell();
  vaciar(contenedorPrincipal).append(cargando());

  try {
    const modulo = await cargador();
    vaciar(contenedorPrincipal);
    await modulo.render(contenedorPrincipal, params);
  } catch (e) {
    console.error(e);
    vaciar(contenedorPrincipal).append(
      el('div', { class: 'contenido' },
        el('div', { class: 'aviso-caja peligro' }, icono('alerta'),
          el('div', {},
            el('strong', {}, 'No se pudo mostrar esta pantalla. '),
            e instanceof ErrorApi ? e.message : (e.message || String(e))))));
  }
}

// --------------------------------------------------------------------- Shell

function dibujarShell() {
  const app = document.getElementById('app');
  if (app.dataset.shell === 'principal') {
    actualizarShell();
    return;
  }
  app.dataset.shell = 'principal';
  app.className = '';
  vaciar(app);

  const sidebar = el('aside', { class: 'sidebar', id: 'sidebar' });
  const topbar = el('header', { class: 'topbar', id: 'topbar' });
  contenedorPrincipal = el('main', { class: 'principal', id: 'principal' });

  app.append(sidebar, topbar, contenedorPrincipal);
  actualizarShell();
}

function enlaceMenu(entrada, prefijo) {
  const ruta = prefijo ? `#/proyecto/${estado.proyectoId}/${entrada.vista}` : `#/${entrada.vista}`;
  const nodo = el('a', {
    href: ruta,
    class: rutaActual === entrada.vista ? 'activo' : '',
  }, icono(entrada.icono), el('span', { class: 'crecer' }, entrada.etiqueta));

  if (entrada.insignia === 'alertas' && estado.alertas > 0) {
    nodo.append(el('span', { class: 'insignia peligro' }, String(estado.alertas)));
  }
  return nodo;
}

function actualizarShell() {
  const sidebar = document.getElementById('sidebar');
  const topbar = document.getElementById('topbar');
  if (!sidebar || !topbar) return;

  // `append` convierte null en el texto "null"; `el()` sí los filtra. Se usa
  // este ayudante en todo lo que se cuelga directamente de un contenedor.
  const poner = (destino, ...hijos) => {
    for (const h of hijos.flat(3)) {
      if (h === null || h === undefined || h === false) continue;
      destino.append(h);
    }
    return destino;
  };

  // --- Barra lateral
  poner(vaciar(sidebar),
    el('div', { class: 'marca' },
      el('div', { class: 'marca-logo' }, 'M'),
      el('div', { class: 'marca-texto' },
        el('span', { class: 'marca-nombre' }, 'METRA AI'),
        el('span', { class: 'marca-sub' }, 'Metrados de obra'))),
    el('nav', { class: 'nav' },
      el('div', { class: 'nav-grupo' },
        el('div', { class: 'nav-titulo' }, 'General'),
        ...MENU_GENERAL.map((e) => enlaceMenu(e, false))),
      estado.proyecto ? el('div', { class: 'nav-grupo' },
        el('div', { class: 'nav-titulo' }, 'Proyecto activo'),
        ...MENU_PROYECTO.map((e) => enlaceMenu(e, true))) : null,
      el('div', { class: 'nav-grupo' },
        el('div', { class: 'nav-titulo' }, 'Sistema'),
        ...MENU_SISTEMA.map((e) => enlaceMenu(e, false)))),
    el('div', { class: 'sidebar-pie' },
      el('div', { class: 'avatar' }, (estado.usuario?.nombre || '?').slice(0, 1).toUpperCase()),
      el('div', { class: 'datos' },
        el('div', { class: 'nombre' }, estado.usuario?.nombre || 'Invitado'),
        el('div', { class: 'rol' }, estado.usuario?.rol || '—')),
      el('button', {
        class: 'btn fantasma icono', title: 'Cambiar tema',
        onclick: () => { alternarTema(); actualizarShell(); },
      }, icono(estado.tema === 'oscuro' ? 'sol' : 'luna'))),
  );

  // --- Barra superior
  const migas = el('div', { class: 'migas' });
  if (estado.proyecto) {
    migas.append(
      el('a', { href: '#/proyectos' }, 'Proyectos'),
      el('span', {}, '/'),
      el('a', { href: `#/proyecto/${estado.proyectoId}/metrados` }, estado.proyecto.nombre),
      el('span', {}, '/'),
      el('span', { class: 'fuerte', estilo: { color: 'var(--texto)' } }, TITULOS[rutaActual] || ''));
  } else {
    migas.append(el('span', { class: 'titulo-vista' }, TITULOS[rutaActual] || 'METRA AI'));
  }

  const selectorVersion = estado.proyecto && estado.versiones.length
    ? el('select', {
        estilo: { width: 'auto', padding: '5px 9px', fontSize: '12px' },
        title: 'Versión activa',
        onchange: (e) => { estado.versionId = e.target.value; notificar(); enrutar(); },
      }, ...estado.versiones.map((v) => el('option', {
        value: v.id, selected: v.id === estado.versionId,
      }, `${v.nombre}${v.estado === 'congelada' ? ' · congelada' : ''}`)))
    : null;

  poner(vaciar(topbar),
    el('button', {
      class: 'btn fantasma icono', title: 'Menú',
      onclick: () => document.getElementById('app').classList.toggle('menu-abierto'),
    }, icono('menu')),
    migas,
    el('div', { class: 'crecer' }),
    selectorVersion,
    estado.proyecto ? el('div', { class: 'separador' }) : null,
    el('div', { class: 'buscador-global' },
      icono('buscar'),
      el('input', {
        type: 'search', placeholder: 'Buscar partida, código o plano…',
        id: 'busqueda-global',
        onkeydown: (e) => { if (e.key === 'Enter') buscarGlobal(e.target.value); },
      }),
      el('kbd', {}, '/')),
    estado.proyecto && puede('exportar') ? el('button', {
      class: 'btn', onclick: () => ir(`/proyecto/${estado.proyectoId}/reportes`),
    }, icono('descargar'), 'Exportar') : null,
    el('button', {
      class: 'btn primario',
      onclick: () => ir('/nuevo'),
    }, icono('mas'), 'Nuevo proyecto'),
  );
}

function buscarGlobal(texto) {
  if (!texto?.trim()) return;
  if (estado.proyectoId) {
    ir(`/proyecto/${estado.proyectoId}/metrados`);
    setTimeout(() => {
      const filtro = document.getElementById('filtro-metrados');
      if (filtro) { filtro.value = texto; filtro.dispatchEvent(new Event('input')); }
    }, 300);
  } else {
    ir('/catalogo');
    setTimeout(() => {
      const filtro = document.getElementById('buscar-catalogo');
      if (filtro) { filtro.value = texto; filtro.dispatchEvent(new Event('input')); }
    }, 300);
  }
}

async function montarAcceso() {
  const app = document.getElementById('app');
  app.dataset.shell = 'acceso';
  app.className = '';
  app.removeAttribute('style');
  vaciar(app);
  const modulo = await VISTAS.acceso();
  await modulo.render(app);
}

// ------------------------------------------------------------------ Atajos

function atajos(e) {
  const enCampo = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);
  if (e.key === '/' && !enCampo) {
    e.preventDefault();
    document.getElementById('busqueda-global')?.focus();
  }
  if (e.key === 'Escape' && enCampo) e.target.blur();
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    document.getElementById('busqueda-global')?.focus();
  }
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'd') {
    e.preventDefault();
    alternarTema();
    actualizarShell();
  }
}

// ------------------------------------------------------------------ Arranque

window.addEventListener('hashchange', enrutar);
document.addEventListener('keydown', atajos);
window.addEventListener('unhandledrejection', (e) => {
  console.error(e.reason);
  if (e.reason instanceof ErrorApi) avisoError(e.reason.message);
});

(async function arrancar() {
  try {
    await iniciar();
  } catch (e) {
    document.getElementById('app').innerHTML =
      `<div style="padding:40px;font-family:system-ui;max-width:560px;margin:auto">
         <h2 style="margin:0 0 8px">No se pudo iniciar METRA AI</h2>
         <p style="color:#51607a;line-height:1.6">${e.message}</p>
         <p style="color:#8593ab;font-size:13px">Verifique que el servidor esté en ejecución
         y vuelva a cargar la página.</p>
       </div>`;
    return;
  }
  await enrutar();
})();

export { enrutar, actualizarShell };
