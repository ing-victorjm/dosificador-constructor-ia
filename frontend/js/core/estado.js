// Estado compartido de la aplicación: usuario, proyecto activo, referencia y
// preferencias. Un único objeto observable; las vistas se suscriben.

import { api, referencia } from './api.js';
import { configurarMoneda } from './fmt.js';

const suscriptores = new Set();

export const estado = {
  usuario: null,
  modoLocal: false,
  referencia: null,
  proyecto: null,          // proyecto abierto (objeto completo)
  proyectoId: null,
  rol: 'metrador',
  permisos: [],
  versionId: null,
  ubicaciones: [],
  versiones: [],
  resumen: null,
  alertas: 0,
  tema: localStorage.getItem('metra_tema') || 'claro',
};

export function suscribir(fn) {
  suscriptores.add(fn);
  return () => suscriptores.delete(fn);
}

export function notificar() {
  for (const fn of suscriptores) fn(estado);
}

export function puede(accion) {
  return estado.permisos.includes(accion);
}

export async function iniciar() {
  estado.referencia = await referencia();
  try {
    const sesion = await api.obtener('/sesion/yo');
    estado.usuario = sesion.usuario;
    estado.modoLocal = sesion.modo_local;
    if (sesion.usuario?.preferencias?.tema) {
      estado.tema = sesion.usuario.preferencias.tema;
    }
  } catch {
    estado.usuario = null;
  }
  aplicarTema(estado.tema);
  notificar();
  return estado;
}

export async function abrirProyecto(id) {
  if (!id) {
    estado.proyecto = null;
    estado.proyectoId = null;
    notificar();
    return null;
  }
  const datos = await api.obtener(`/proyectos/${id}`);
  estado.proyecto = datos.proyecto;
  estado.proyectoId = id;
  estado.rol = datos.rol;
  estado.permisos = datos.permisos;
  estado.ubicaciones = datos.ubicaciones;
  estado.versiones = datos.versiones;
  estado.versionId = datos.proyecto.version_actual_id;
  estado.resumen = datos.resumen;
  configurarMoneda(datos.proyecto.moneda_formato);
  notificar();
  return datos;
}

export async function refrescarProyecto() {
  if (estado.proyectoId) return abrirProyecto(estado.proyectoId);
  return null;
}

export function aplicarTema(tema) {
  estado.tema = tema;
  document.documentElement.setAttribute('data-theme', tema === 'oscuro' ? 'dark' : 'light');
  localStorage.setItem('metra_tema', tema);
}

export function alternarTema() {
  const nuevo = estado.tema === 'oscuro' ? 'claro' : 'oscuro';
  aplicarTema(nuevo);
  api.actualizar('/sesion/preferencias', { tema: nuevo }).catch(() => {});
  notificar();
}

/** Busca una especialidad en la referencia cargada. */
export function especialidad(clave) {
  return (estado.referencia?.especialidades || []).find((e) => e.clave === clave)
    || { clave, nombre: clave, color: '#8593ab', corto: clave };
}

export function nombreUbicacion(id) {
  const buscar = (nodos) => {
    for (const n of nodos) {
      if (n.id === id) return n.nombre;
      const encontrado = buscar(n.hijos || []);
      if (encontrado) return encontrado;
    }
    return null;
  };
  return buscar(estado.ubicaciones || []);
}

export function ubicacionesPlanas(tipos = null) {
  const salida = [];
  const recorrer = (nodos, nivel) => {
    for (const n of nodos) {
      if (!tipos || tipos.includes(n.tipo)) {
        salida.push({ ...n, nivel, etiqueta: ' '.repeat(nivel * 2) + n.nombre });
      }
      recorrer(n.hijos || [], nivel + 1);
    }
  };
  recorrer(estado.ubicaciones || [], 0);
  return salida;
}
