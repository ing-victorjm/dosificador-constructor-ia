// Formato y parseo de números. La app trabaja con cadenas decimales de extremo
// a extremo (el backend calcula en Decimal); aquí solo se formatea para mostrar.

let config = { sep_decimal: '.', sep_miles: ',', simbolo: 'S/', decimales: 2 };

export function configurarMoneda(m) {
  if (m) config = { ...config, ...m };
}

export function num(valor, decimales = 2) {
  if (valor === null || valor === undefined || valor === '') return '';
  const n = typeof valor === 'number' ? valor : parseFloat(String(valor).replace(',', '.'));
  if (!isFinite(n)) return String(valor);
  const partes = Math.abs(n).toFixed(decimales).split('.');
  partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, config.sep_miles);
  const texto = partes.join(config.sep_decimal);
  return (n < 0 ? '-' : '') + texto;
}

export function moneda(valor, decimales = 2) {
  if (valor === null || valor === undefined || valor === '') return '—';
  return `${config.simbolo} ${num(valor, decimales)}`;
}

export function metrado(valor, decimales = 2) {
  if (valor === null || valor === undefined || valor === '') return '—';
  return num(valor, decimales);
}

export function pct(valor, decimales = 1) {
  if (valor === null || valor === undefined || valor === '') return '—';
  return `${num(valor, decimales)}%`;
}

/** Acepta "1,234.56" y "1.234,56" y devuelve una cadena decimal canónica. */
export function parsear(texto) {
  if (texto === null || texto === undefined) return '';
  let t = String(texto).trim().replace(/\s/g, '');
  if (!t) return '';
  if (t.includes(',') && t.includes('.')) {
    t = t.lastIndexOf(',') > t.lastIndexOf('.')
      ? t.replace(/\./g, '').replace(',', '.')
      : t.replace(/,/g, '');
  } else if (t.includes(',')) {
    t = t.replace(',', '.');
  }
  return t;
}

export function esNumero(texto) {
  const t = parsear(texto);
  return t !== '' && isFinite(parseFloat(t));
}

export function fecha(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

export function fechaHora(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleString('es-PE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function haceCuanto(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  const seg = (Date.now() - d.getTime()) / 1000;
  if (seg < 60) return 'hace un momento';
  if (seg < 3600) return `hace ${Math.floor(seg / 60)} min`;
  if (seg < 86400) return `hace ${Math.floor(seg / 3600)} h`;
  if (seg < 604800) return `hace ${Math.floor(seg / 86400)} d`;
  return fecha(iso);
}

export function truncar(texto, largo = 60) {
  const t = String(texto || '');
  return t.length > largo ? t.slice(0, largo - 1) + '…' : t;
}

/** Escapa texto para insertarlo en HTML. Todo dato del usuario pasa por aquí. */
export function esc(texto) {
  if (texto === null || texto === undefined) return '';
  return String(texto)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

export function hoy() {
  return new Date().toISOString().slice(0, 10);
}
