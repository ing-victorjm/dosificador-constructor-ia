// Gestión de usuarios y roles.

import { api } from '../core/api.js';
import { estado } from '../core/estado.js';
import { fechaHora } from '../core/fmt.js';
import { el, vaciar, icono, cargando, chip, panel, avisoCaja, exito, error as avisoError } from '../ui/base.js';

export async function render(contenedor) {
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);
  cuerpo.append(cargando());

  const datos = await api.obtener('/usuarios');
  const esAdmin = estado.usuario?.rol === 'administrador';

  cuerpo.replaceChildren(
    el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
      'Usuarios y roles'),
    el('p', { class: 'suave mb2', estilo: { marginTop: 0 } },
      `${datos.usuarios.length} usuario(s) registrados`),

    el('div', { class: 'rejilla auto mb2' },
      ...Object.entries(datos.roles).map(([rol, descripcion]) => el('div', { class: 'panel' },
        el('div', { class: 'panel-cuerpo' },
          el('div', { class: 'fila mb1' },
            icono('usuarios'),
            el('span', { class: 'fuerte', estilo: { textTransform: 'capitalize' } }, rol)),
          el('p', { class: 'chico suave', estilo: { margin: 0, lineHeight: '1.55' } },
            descripcion))))),

    esAdmin ? null : avisoCaja('info',
      'Solo un administrador puede cambiar roles. Puede consultar la lista.'),

    panel('Equipo', el('div', { class: 'tabla-envoltura' },
      el('table', { class: 'tabla' },
        el('thead', {}, el('tr', {},
          el('th', {}, 'Usuario'), el('th', {}, 'Correo'), el('th', {}, 'Rol'),
          el('th', {}, 'Permisos'), el('th', {}, 'Último acceso'), el('th', { class: 'centro' }, 'Activo'))),
        el('tbody', {}, ...datos.usuarios.map((u) => el('tr', {},
          el('td', {}, el('div', { class: 'fila' },
            el('div', {
              class: 'avatar',
              estilo: { width: '26px', height: '26px', fontSize: '11px' },
            }, (u.nombre || '?').slice(0, 1).toUpperCase()),
            el('div', {},
              el('div', { class: 'fuerte' }, u.nombre),
              u.profesion ? el('div', { class: 'chico apagado' }, u.profesion) : null))),
          el('td', { class: 'chico mono' }, u.email),
          el('td', {}, esAdmin
            ? (() => {
                const s = el('select', {
                  estilo: { width: 'auto', padding: '4px 8px', fontSize: '12px' },
                });
                for (const rol of Object.keys(datos.roles)) {
                  s.append(el('option', { value: rol, selected: rol === u.rol },
                    rol.charAt(0).toUpperCase() + rol.slice(1)));
                }
                s.onchange = async () => {
                  try {
                    await api.actualizar(`/usuarios/${u.id}`, { rol: s.value });
                    exito(`${u.nombre} ahora es ${s.value}.`);
                  } catch (e) { avisoError(e.message); s.value = u.rol; }
                };
                return s;
              })()
            : chip(u.rol)),
          el('td', {}, el('div', { class: 'fila envuelve', estilo: { gap: '4px' } },
            ...(u.permisos || []).map((p) => chip(p)))),
          el('td', { class: 'chico apagado' }, u.ultimo_acceso ? fechaHora(u.ultimo_acceso) : 'nunca'),
          el('td', { class: 'centro' },
            u.activo ? chip('activo', 'ok') : chip('inactivo', 'peligro'))))))));
}
