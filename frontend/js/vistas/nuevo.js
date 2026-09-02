// Creación de proyecto: país, normativa, moneda, unidades y estructura física.

import { api } from '../core/api.js';
import { estado } from '../core/estado.js';
import { hoy } from '../core/fmt.js';
import { el, icono, campo, avisoCaja, exito, error as avisoError } from '../ui/base.js';
import { ir } from '../app.js';

export async function render(contenedor) {
  const ref = estado.referencia;
  const cuerpo = el('div', { class: 'contenido', estilo: { maxWidth: '980px' } });
  contenedor.append(cuerpo);

  const campos = {};
  const nota = el('div', { class: 'mb2' });

  const entrada = (clave, atributos = {}) => {
    const nodo = el('input', { type: 'text', ...atributos });
    campos[clave] = nodo;
    return nodo;
  };
  const seleccion = (clave, opciones, valor) => {
    const nodo = el('select', {},
      ...opciones.map((o) => el('option', {
        value: o.valor, selected: o.valor === valor,
      }, o.texto)));
    campos[clave] = nodo;
    return nodo;
  };

  const paises = ref.paises.map((p) => ({ valor: p.codigo_iso, texto: p.pais }));
  const monedas = ref.monedas.map((m) => ({ valor: m.iso, texto: `${m.simbolo}  ${m.nombre} (${m.iso})` }));

  const infoNorma = el('div', { class: 'mt1' });
  const actualizarNorma = () => {
    const p = ref.paises.find((x) => x.codigo_iso === campos.pais.value);
    if (!p) return infoNorma.replaceChildren();
    const norma = (p.normas || [])[0];
    campos.moneda.value = p.moneda?.iso || 'PEN';
    campos.sistema_unidades.value = p.sistema_unidades || 'metrico';
    infoNorma.replaceChildren(avisoCaja('info', el('div', {},
      el('strong', {}, 'Normativa que se aplicará: '),
      norma ? `${norma.nombre}${norma.anio ? ` (${norma.anio})` : ''}` : 'Sin norma registrada para este país.',
      el('div', { class: 'chico mt1' },
        `Impuesto: ${p.impuesto?.nombre || '—'} ${p.impuesto?.tasa || 0}% · `
        + `Sistema: ${p.sistema_unidades === 'metrico' ? 'métrico' : 'imperial'}`),
      p.verificado === false
        ? el('div', { class: 'chico mt1' }, 'Datos de este país sin verificar: revíselos en Configuración.')
        : null)));
  };

  const formulario = el('form', { class: 'col', estilo: { gap: '0' } },
    seccion('Identificación del proyecto',
      el('div', { class: 'fila-campos' },
        campo('Nombre del proyecto *', entrada('nombre', {
          required: true, placeholder: 'Edificio multifamiliar Los Álamos',
        })),
        campo('Código', entrada('codigo', { placeholder: 'Se genera solo si lo deja vacío' }))),
      el('div', { class: 'fila-campos' },
        campo('Cliente', entrada('cliente', { placeholder: 'Nombre o razón social' })),
        campo('Ubicación', entrada('ubicacion_texto', { placeholder: 'Distrito, provincia, región' })),
        campo('Responsable', entrada('responsable', {
          placeholder: estado.usuario?.nombre || 'Ingeniero responsable',
        })))),

    seccion('Tipo y dimensiones',
      el('div', { class: 'fila-campos' },
        campo('Tipo de proyecto', seleccion('tipo',
          ref.tipos_proyecto.map((t) => ({ valor: t.clave, texto: t.nombre })), 'edificio')),
        campo('Etapa', seleccion('etapa',
          ref.etapas.map((t) => ({ valor: t.clave, texto: t.nombre })), 'expediente')),
        campo('Fecha', (campos.fecha = el('input', { type: 'date', value: hoy() })))),
      el('div', { class: 'fila-campos' },
        campo('Pisos', (campos.pisos = el('input', { type: 'number', min: 0, max: 200, value: 3 })),
          'Sobre el nivel del terreno'),
        campo('Sótanos', (campos.sotanos = el('input', { type: 'number', min: 0, max: 20, value: 0 }))),
        campo('Sectores', (campos.sectores = el('input', { type: 'number', min: 1, max: 100, value: 1 })),
          'Bloques o frentes de trabajo independientes'))),

    seccion('Normativa, moneda y unidades',
      el('div', { class: 'fila-campos' },
        campo('País', (() => {
          const s = seleccion('pais', paises, 'PE');
          s.onchange = actualizarNorma;
          return s;
        })(), 'Define la norma de medición aplicable'),
        campo('Moneda', seleccion('moneda', monedas, 'PEN')),
        campo('Sistema de unidades', seleccion('sistema_unidades', [
          { valor: 'metrico', texto: 'Métrico (m, m², m³, kg)' },
          { valor: 'imperial', texto: 'Imperial (ft, sf, cy, lb)' },
        ], 'metrico'))),
      infoNorma),

    seccion('Contenido inicial',
      el('label', { class: 'interruptor mb2' },
        (campos.generar_estructura = el('input', { type: 'checkbox', checked: true })),
        el('span', { class: 'pista' }),
        el('span', {}, 'Generar la estructura física (edificio → sectores → niveles → azotea)')),
      campo('Plantilla de partidas', seleccion('plantilla', [
        { valor: 'edificacion', texto: 'Edificación completa — preliminares, tierras, estructuras, arquitectura e instalaciones' },
        { valor: 'estructuras', texto: 'Solo estructuras' },
        { valor: 'acabados', texto: 'Solo acabados (arquitectura)' },
        { valor: '', texto: 'Empezar en blanco' },
      ], 'edificacion'),
        'Las partidas se enlazan a los códigos reales de la norma. Puede agregar, quitar o renombrar después.'),
      el('textarea', { placeholder: 'Notas del proyecto (opcional)', id: 'notas-proyecto' })),

    nota,
    el('div', { class: 'fila', estilo: { justifyContent: 'flex-end', gap: '9px', paddingTop: '6px' } },
      el('button', { type: 'button', class: 'btn', onclick: () => ir('/proyectos') }, 'Cancelar'),
      el('button', { type: 'submit', class: 'btn primario' }, icono('check'), 'Crear proyecto')),
  );

  formulario.onsubmit = async (e) => {
    e.preventDefault();
    const boton = formulario.querySelector('button[type=submit]');
    boton.disabled = true;
    nota.replaceChildren();
    try {
      const datos = {
        nombre: campos.nombre.value.trim(),
        codigo: campos.codigo.value.trim() || null,
        cliente: campos.cliente.value.trim() || null,
        ubicacion_texto: campos.ubicacion_texto.value.trim() || null,
        responsable: campos.responsable.value.trim() || null,
        tipo: campos.tipo.value,
        etapa: campos.etapa.value,
        fecha: campos.fecha.value || null,
        pisos: parseInt(campos.pisos.value || 1, 10),
        sotanos: parseInt(campos.sotanos.value || 0, 10),
        sectores: parseInt(campos.sectores.value || 1, 10),
        pais: campos.pais.value,
        moneda: campos.moneda.value,
        sistema_unidades: campos.sistema_unidades.value,
        notas: document.getElementById('notas-proyecto').value.trim() || null,
        generar_estructura: campos.generar_estructura.checked,
      };
      const { proyecto } = await api.crear('/proyectos', datos);

      const plantilla = campos.plantilla.value;
      if (plantilla) {
        const r = await api.crear('/asistente/confirmar', {
          accion: 'aplicar_plantilla', proyecto_id: proyecto.id, parametros: { clave: plantilla },
        });
        exito(r.respuesta);
      } else {
        exito('Proyecto creado.');
      }
      ir(`/proyecto/${proyecto.id}/metrados`);
    } catch (err) {
      nota.replaceChildren(avisoCaja('peligro', err.message));
      boton.disabled = false;
    }
  };

  cuerpo.append(
    el('h1', { estilo: { margin: '0 0 3px', fontSize: '20px', letterSpacing: '-.4px' } }, 'Nuevo proyecto'),
    el('p', { class: 'suave mb2', estilo: { marginTop: 0 } },
      'El país determina la norma de medición, la moneda y las reglas de descuento por defecto. '
      + 'Todo se puede cambiar después en Configuración.'),
    formulario);

  actualizarNorma();
}

function seccion(titulo, ...contenido) {
  return el('div', { class: 'panel mb2' },
    el('div', { class: 'panel-cabecera' }, el('h2', {}, titulo)),
    el('div', { class: 'panel-cuerpo' }, ...contenido));
}
