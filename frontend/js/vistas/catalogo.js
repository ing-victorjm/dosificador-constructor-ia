// Catálogo de partidas: biblioteca normativa + biblioteca propia.

import { api } from '../core/api.js';
import { estado } from '../core/estado.js';
import {
  el, vaciar, icono, cargando, vacio, chip, panel, campo, modal, cita,
  puntoEspecialidad, avisoCaja, exito, error as avisoError, aviso,
} from '../ui/base.js';

let consulta = '';
let especialidadActiva = '';
let soloVerificadas = false;
let pagina = 1;

export async function render(contenedor) {
  const cuerpo = el('div', { class: 'contenido ancho' });
  contenedor.append(cuerpo);

  const resumen = await api.obtener('/catalogo/resumen');
  const lista = el('div', { class: 'panel' });
  const paginador = el('div', { class: 'fila', estilo: { justifyContent: 'center', padding: '12px' } });

  const cargar = async () => {
    vaciar(lista).append(cargando());
    const parametros = new URLSearchParams({ pagina, por_pagina: 40 });
    if (consulta) parametros.set('q', consulta);
    if (especialidadActiva) parametros.set('especialidad', especialidadActiva);
    if (soloVerificadas) parametros.set('solo_verificadas', 'true');
    const datos = await api.obtener(`/catalogo/partidas?${parametros}`);

    vaciar(lista);
    if (!datos.partidas.length) {
      lista.append(vacio({
        icono: 'buscar', titulo: 'Ninguna partida coincide',
        mensaje: `No se encontró «${consulta}». Pruebe con otra palabra o con el código de norma.`,
      }));
      vaciar(paginador);
      return;
    }

    lista.append(el('div', { class: 'tabla-envoltura' },
      el('table', { class: 'tabla densa' },
        el('thead', {}, el('tr', {},
          el('th', {}, 'Código'), el('th', {}, 'Descripción'),
          el('th', { class: 'centro' }, 'Und.'), el('th', {}, 'Especialidad'),
          el('th', {}, 'Procedencia'), el('th', {}))),
        el('tbody', {}, ...datos.partidas.map((p) => el('tr', {},
          el('td', { class: 'codigo' }, p.codigo),
          el('td', {}, p.descripcion),
          el('td', { class: 'centro mono' }, p.unidad),
          el('td', {}, el('span', { class: 'fila', estilo: { gap: '6px' } },
            puntoEspecialidad(p.color), el('span', { class: 'chico' }, p.capitulo || p.especialidad))),
          el('td', {}, p.verificado
            ? chip('Verificada en la norma', 'ok')
            : chip(p.propia ? 'Propia' : 'Sin verificar', p.propia ? 'info' : 'alerta')),
          el('td', { class: 'centro' },
            el('button', {
              class: 'btn chico fantasma', title: 'Ver regla de medición',
              onclick: () => verPartida(p),
            }, icono('ojo'))))))));

    const paginas = Math.ceil(datos.total / datos.por_pagina);
    vaciar(paginador).append(
      el('button', {
        class: 'btn chico', disabled: pagina <= 1,
        onclick: () => { pagina--; cargar(); },
      }, 'Anterior'),
      el('span', { class: 'chico apagado mono' },
        ` ${datos.total} partidas · página ${pagina} de ${paginas || 1} `),
      el('button', {
        class: 'btn chico', disabled: pagina >= paginas,
        onclick: () => { pagina++; cargar(); },
      }, 'Siguiente'));
  };

  let temporizador;
  cuerpo.append(
    el('div', { class: 'fila entre mb2 envuelve' },
      el('div', {},
        el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } },
          'Catálogo de partidas'),
        el('p', { class: 'suave', estilo: { margin: 0 } },
          `${resumen.total} partidas · ${resumen.verificadas} verificadas contra el texto de la norma`)),
      el('div', { class: 'fila' },
        el('button', { class: 'btn', onclick: () => importar(cargar) },
          icono('subir'), 'Importar catálogo'),
        el('button', { class: 'btn primario', onclick: () => nuevaPartida(cargar) },
          icono('mas'), 'Nueva partida'))),

    avisoCaja('info', el('div', {},
      el('strong', {}, 'Las partidas del catálogo normativo no se editan: '),
      'su texto es el de la norma. Si necesita una variante, duplíquela y edite la copia. '
      + 'Así el catálogo sigue siendo citable ante una supervisión.')),

    el('div', { class: 'fila envuelve mt2 mb2' },
      el('input', {
        type: 'search', id: 'buscar-catalogo', placeholder: 'Buscar por descripción o código…',
        estilo: { maxWidth: '360px' },
        oninput: (e) => {
          clearTimeout(temporizador);
          consulta = e.target.value;
          pagina = 1;
          temporizador = setTimeout(cargar, 260);
        },
      }),
      el('select', {
        estilo: { width: 'auto' },
        onchange: (e) => { especialidadActiva = e.target.value; pagina = 1; cargar(); },
      },
        el('option', { value: '' }, 'Todas las especialidades'),
        ...resumen.por_especialidad.map((e) => el('option', { value: e.clave },
          `${e.nombre} (${e.total})`))),
      el('label', { class: 'interruptor' },
        el('input', {
          type: 'checkbox',
          onchange: (e) => { soloVerificadas = e.target.checked; pagina = 1; cargar(); },
        }),
        el('span', { class: 'pista' }),
        el('span', { class: 'chico' }, 'Solo verificadas'))),

    lista, paginador);

  await cargar();
}

function verPartida(p) {
  modal({
    titulo: p.descripcion,
    ancho: 'ancho',
    cuerpo: el('div', {},
      el('div', { class: 'fila envuelve mb2' },
        chip(p.codigo, 'acento'), chip(`Unidad: ${p.unidad}`),
        chip(p.capitulo || p.especialidad),
        p.verificado ? chip('Verificada', 'ok') : chip('Sin verificar', 'alerta')),
      p.regla_medicion
        ? el('div', {},
            el('div', { class: 'chico fuerte mb1' }, 'Forma de medición según la norma'),
            cita({ texto: p.regla_medicion, codigo: p.codigo, etiqueta: p.norma }))
        : avisoCaja('alerta', 'Esta partida no declara forma de medición en el texto de la norma. '
          + 'Se marca así en vez de inventar una regla.'),
      p.formula ? el('div', { class: 'mt2' },
        el('div', { class: 'chico fuerte mb1' }, 'Fórmula sugerida'),
        el('code', { class: 'mono' }, p.formula)) : null,
      p.fuente ? el('div', { class: 'chico apagado mt2' },
        'Fuente: ', el('a', { href: p.fuente, target: '_blank', rel: 'noopener' }, p.fuente)) : null,
      p.etiquetas?.length ? el('div', { class: 'fila envuelve mt2', estilo: { gap: '5px' } },
        ...p.etiquetas.map((t) => chip(t))) : null),
    pie: [
      el('button', {
        class: 'btn',
        onclick: async (e) => {
          try {
            await api.crear(`/catalogo/partidas/${p.id}/duplicar`, {});
            exito('Copia editable creada en su catálogo propio.');
            e.target.closest('.velo').remove();
          } catch (err) { avisoError(err.message); }
        },
      }, icono('copiar'), 'Duplicar para editar'),
      el('button', {
        class: 'btn primario', onclick: (e) => e.target.closest('.velo').remove(),
      }, 'Cerrar'),
    ],
  });
}

function nuevaPartida(recargar) {
  const codigo = el('input', { type: 'text', placeholder: 'PROP-001' });
  const descripcion = el('input', { type: 'text', placeholder: 'Descripción de la partida' });
  const unidad = el('input', { type: 'text', value: 'm2' });
  const esp = el('select', {}, ...estado.referencia.especialidades.map((e) =>
    el('option', { value: e.clave }, e.nombre)));
  const regla = el('textarea', { placeholder: 'Cómo se mide esta partida' });

  const control = modal({
    titulo: 'Nueva partida propia',
    cuerpo: el('div', {},
      el('div', { class: 'fila-campos' },
        campo('Código', codigo), campo('Unidad', unidad)),
      campo('Descripción', descripcion),
      campo('Especialidad', esp),
      campo('Forma de medición', regla,
        'Escriba el criterio con el que se mide. Se mostrará junto a cada partida que la use.')),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          if (!codigo.value.trim() || !descripcion.value.trim()) {
            return aviso('El código y la descripción son obligatorios.', 'alerta');
          }
          try {
            await api.crear('/catalogo/partidas', {
              codigo: codigo.value.trim(), descripcion: descripcion.value.trim(),
              unidad: unidad.value.trim(), especialidad: esp.value,
              regla_medicion: regla.value.trim() || null,
            });
            control.cerrar();
            exito('Partida creada en su catálogo.');
            recargar();
          } catch (e) { avisoError(e.message); }
        },
      }, icono('check'), 'Crear'),
    ],
  });
}

function importar(recargar) {
  const archivo = el('input', { type: 'file', accept: '.csv,.xlsx,.xls' });
  const control = modal({
    titulo: 'Importar catálogo',
    cuerpo: el('div', {},
      avisoCaja('info', el('div', {},
        el('strong', {}, 'Columnas obligatorias: '), 'codigo, descripcion, unidad. ',
        el('div', { class: 'chico mt1' },
          'Opcionales: especialidad, formula, regla_medicion, desperdicio, rendimiento, cuadrilla. '
          + 'Las partidas importadas se marcan como no verificadas hasta que usted las revise.'))),
      el('div', { class: 'mt2' }, campo('Archivo CSV o Excel', archivo))),
    pie: [
      el('button', { class: 'btn', onclick: () => control.cerrar() }, 'Cancelar'),
      el('button', {
        class: 'btn primario',
        onclick: async () => {
          if (!archivo.files.length) return aviso('Elija un archivo.', 'alerta');
          const datos = new FormData();
          datos.append('archivo', archivo.files[0]);
          try {
            const r = await api.subir('/catalogo/importar', datos);
            control.cerrar();
            exito(`${r.creadas} partida(s) importadas.`
              + (r.total_errores ? ` ${r.total_errores} fila(s) con problemas.` : ''));
            recargar();
          } catch (e) { avisoError(e.message); }
        },
      }, icono('subir'), 'Importar'),
    ],
  });
}
