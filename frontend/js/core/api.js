// Cliente de la API. Un único punto de salida a la red: aquí viven el manejo
// de errores, la sesión y la caché de datos de referencia.

const BASE = '/api';

export class ErrorApi extends Error {
  constructor(mensaje, estado, detalle) {
    super(mensaje);
    this.estado = estado;
    this.detalle = detalle;
  }
}

let token = localStorage.getItem('metra_token') || null;

export function guardarToken(t) {
  token = t;
  if (t) localStorage.setItem('metra_token', t);
  else localStorage.removeItem('metra_token');
}

async function pedir(ruta, opciones = {}) {
  const cabeceras = { ...(opciones.headers || {}) };
  if (token) cabeceras['Authorization'] = `Bearer ${token}`;
  if (opciones.body && !(opciones.body instanceof FormData)) {
    cabeceras['Content-Type'] = 'application/json';
    opciones.body = JSON.stringify(opciones.body);
  }

  let respuesta;
  try {
    respuesta = await fetch(BASE + ruta, { ...opciones, headers: cabeceras });
  } catch (e) {
    throw new ErrorApi(
      'No se pudo conectar con el servidor. Revise que METRA AI siga en ejecución.',
      0, e.message);
  }

  if (respuesta.status === 204) return null;

  const tipo = respuesta.headers.get('content-type') || '';
  if (!tipo.includes('application/json')) {
    if (!respuesta.ok) throw new ErrorApi(`Error ${respuesta.status}`, respuesta.status);
    return respuesta;
  }

  const datos = await respuesta.json();
  if (!respuesta.ok) {
    const mensaje = datos.detail || datos.mensaje || `Error ${respuesta.status}`;
    throw new ErrorApi(
      typeof mensaje === 'string' ? mensaje : JSON.stringify(mensaje),
      respuesta.status, datos);
  }
  return datos;
}

export const api = {
  obtener: (ruta) => pedir(ruta),
  crear: (ruta, body) => pedir(ruta, { method: 'POST', body }),
  actualizar: (ruta, body) => pedir(ruta, { method: 'PUT', body }),
  borrar: (ruta) => pedir(ruta, { method: 'DELETE' }),
  subir: (ruta, formData) => pedir(ruta, { method: 'POST', body: formData }),

  descargar(ruta, nombreSugerido) {
    // Se abre en una pestaña para que el navegador gestione la descarga con su
    // propio diálogo; así funciona igual con archivos grandes.
    const url = BASE + ruta + (ruta.includes('?') ? '&' : '?') +
      (token ? `token=${encodeURIComponent(token)}` : '');
    const a = document.createElement('a');
    a.href = url;
    if (nombreSugerido) a.download = nombreSugerido;
    a.target = '_blank';
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    a.remove();
  },
};

// --- Caché de referencia -----------------------------------------------------
// Unidades, especialidades, reglas normativas y países no cambian durante la
// sesión: se piden una vez.

let _referencia = null;

export async function referencia() {
  if (!_referencia) _referencia = await api.obtener('/referencia');
  return _referencia;
}

export function referenciaSync() {
  return _referencia;
}

export function limpiarCache() {
  _referencia = null;
}
