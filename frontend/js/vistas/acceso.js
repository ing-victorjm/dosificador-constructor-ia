// Inicio de sesión y registro.
//
// Nota de producto: en modo local se puede entrar sin cuenta. Obligar a
// registrarse antes de dejar metrar es el antipatrón que hace que la
// herramienta no se use.

import { api, guardarToken } from '../core/api.js';
import { estado, iniciar } from '../core/estado.js';
import { el, icono, campo, aviso, error as avisoError } from '../ui/base.js';

const VENTAJAS = [
  'Cada cantidad guarda su fórmula, su plano y quién la hizo.',
  'La norma de metrados aplicada con su cita literal, no de memoria.',
  'Nunca inventa un dato: si falta una medida, lo dice.',
  'Exporta a Excel con fórmulas vivas y a PDF listo para firmar.',
];

export async function render(contenedor) {
  let modo = 'acceso';

  const mensaje = el('div', { class: 'mb2' });
  const formulario = el('form', { class: 'col' });
  const pestanas = el('div', { class: 'acceso-pestanas' });

  const dibujar = () => {
    pestanas.replaceChildren(
      el('button', {
        type: 'button', class: modo === 'acceso' ? 'activo' : '',
        onclick: () => { modo = 'acceso'; dibujar(); },
      }, 'Iniciar sesión'),
      el('button', {
        type: 'button', class: modo === 'registro' ? 'activo' : '',
        onclick: () => { modo = 'registro'; dibujar(); },
      }, 'Crear cuenta'));

    const email = el('input', {
      type: 'email', required: true, autocomplete: 'email',
      placeholder: 'nombre@empresa.com',
    });
    const clave = el('input', {
      type: 'password', required: true, minlength: 8,
      autocomplete: modo === 'registro' ? 'new-password' : 'current-password',
      placeholder: modo === 'registro' ? 'Mínimo 8 caracteres' : '',
    });
    const nombre = el('input', { type: 'text', required: true, placeholder: 'Nombre y apellidos' });
    const empresa = el('input', { type: 'text', placeholder: 'Opcional' });

    formulario.replaceChildren(
      modo === 'registro' ? campo('Nombre completo', nombre) : null,
      campo('Correo electrónico', email),
      campo('Contraseña', clave,
        modo === 'registro' ? 'Combine letras y números. Se guarda cifrada con PBKDF2.' : null),
      modo === 'registro' ? campo('Empresa', empresa,
        'Los proyectos de una empresa se comparten con su equipo.') : null,
      el('button', { type: 'submit', class: 'btn primario', estilo: { width: '100%', padding: '10px' } },
        modo === 'registro' ? 'Crear cuenta y entrar' : 'Entrar'),
    );

    formulario.onsubmit = async (e) => {
      e.preventDefault();
      const boton = formulario.querySelector('button[type=submit]');
      boton.disabled = true;
      boton.textContent = 'Un momento…';
      mensaje.replaceChildren();
      try {
        const ruta = modo === 'registro' ? '/sesion/registro' : '/sesion/acceso';
        const cuerpo = modo === 'registro'
          ? { email: email.value, clave: clave.value, nombre: nombre.value, empresa: empresa.value || null }
          : { email: email.value, clave: clave.value };
        const datos = await api.crear(ruta, cuerpo);
        guardarToken(datos.token);
        await iniciar();
        aviso(`Bienvenido, ${datos.usuario.nombre}.`, 'ok');
        location.hash = '#/panel';
        location.reload();
      } catch (err) {
        mensaje.replaceChildren(
          el('div', { class: 'aviso-caja peligro' }, icono('alerta'), el('div', {}, err.message)));
        boton.disabled = false;
        boton.textContent = modo === 'registro' ? 'Crear cuenta y entrar' : 'Entrar';
      }
    };
  };

  dibujar();

  const entrarLocal = el('button', {
    class: 'btn', estilo: { width: '100%' },
    onclick: async () => {
      try {
        await iniciar();
        if (!estado.usuario) throw new Error('El modo local no está habilitado en este servidor.');
        location.hash = '#/panel';
        location.reload();
      } catch (err) { avisoError(err.message); }
    },
  }, icono('salir'), 'Entrar en este equipo sin cuenta');

  contenedor.append(
    el('div', { class: 'acceso' },
      el('div', { class: 'acceso-lado' },
        el('div', { class: 'fila', estilo: { gap: '12px' } },
          el('div', { class: 'marca-logo', estilo: { width: '38px', height: '38px', fontSize: '16px' } }, 'M'),
          el('span', { estilo: { fontSize: '19px', fontWeight: '750', letterSpacing: '-.4px' } }, 'METRA AI')),
        el('h1', {}, 'Metrados que se pueden defender ante una supervisión.'),
        el('p', {}, 'Calcule, revise y exporte cantidades de obra de todas las especialidades '
          + 'con la trazabilidad que exige un expediente técnico.'),
        el('div', { class: 'acceso-lista' },
          ...VENTAJAS.map((t) => el('div', {}, icono('check'), el('span', {}, t)))),
      ),
      el('div', { class: 'acceso-formulario' },
        el('h2', {}, modo === 'registro' ? 'Cree su cuenta' : 'Bienvenido de vuelta'),
        el('p', { class: 'sub' }, 'Acceda para continuar con sus proyectos.'),
        pestanas, mensaje, formulario,
        el('div', { class: 'sep' }),
        entrarLocal,
        el('p', { class: 'chico apagado centrado mt2', estilo: { lineHeight: '1.6' } },
          'El modo local guarda todo en este equipo. Cree una cuenta cuando necesite '
          + 'trabajar en equipo con roles de revisión y aprobación.'))),
  );
}
