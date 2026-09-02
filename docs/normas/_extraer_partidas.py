# -*- coding: utf-8 -*-
"""Extractor del catalogo de partidas de la Norma Tecnica de Metrados del Peru.

Fuente: R.D. N 073-2010-VIVIENDA/VMCS-DNC, PDF oficial SPIJ-MINJUS
        https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf

Uso:  python _extraer_partidas.py
      (requiere pymupdf; lee ./RD-073-2010-VIVIENDA-VMCS-DNC-SPIJ.pdf y
       reescribe ../investigacion/01-partidas-peru.json)

Los rangos IDX_RANGES / BODY_RANGES estan calibrados para ESE PDF exacto (154 pp.).
"""
import os, re, json, collections
import pymupdf

AQUI = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(AQUI, 'RD-073-2010-VIVIENDA-VMCS-DNC-SPIJ.pdf')
SALIDA = os.path.normpath(os.path.join(AQUI, '..', 'investigacion', '01-partidas-peru.json'))

_doc = pymupdf.open(PDF)
txt = ''.join('\n===== PAGINA %d =====\n' % (i + 1) + p.get_text()
              for i, p in enumerate(_doc))
lines = txt.split('\n')

CODE_RE = re.compile(r'^\s*((?:OE|HU)\.\d+(?:\.\d+)*)\s*\.?\s*$')
CODE_INLINE_RE = re.compile(r'^\s*((?:OE|HU)\.\d+(?:\.\d+)*)\s*\.?\s+(\S.*)$')


def clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def strip_pages(seq):
    return [l for l in seq if not l.startswith('===== PAGINA')]


def is_code_line(l):
    return bool(CODE_RE.match(l) or CODE_INLINE_RE.match(l))


# ------------------------------------------------------------------ 1) INDICE
IDX_RANGES = [(402, 1678), (7543, 7762)]

index_map, index_order = {}, []
for a, b in IDX_RANGES:
    cur = None
    for l in strip_pages(lines[a:b]):
        m, m2 = CODE_RE.match(l), CODE_INLINE_RE.match(l)
        if m:
            cur = {'c': m.group(1), 'd': []}
            if cur['c'] not in index_map:
                index_order.append(cur['c'])
                index_map[cur['c']] = cur['d']
            else:
                cur = None
        elif m2:
            cur = {'c': m2.group(1), 'd': [m2.group(2)]}
            if cur['c'] not in index_map:
                index_order.append(cur['c'])
                index_map[cur['c']] = cur['d']
            else:
                cur = None
        else:
            s = l.strip()
            if not s or s.upper().startswith('TITULO'):
                continue
            if cur is not None:
                index_map[cur['c']].append(s)

index_map = {k: clean(' '.join(v)).rstrip('.').strip() for k, v in index_map.items()}

# ------------------------------------------------------------------ 2) CUERPO
BODY_RANGES = [(1678, 7519), (7762, len(lines))]
body = []
for a, b in BODY_RANGES:
    body.extend(strip_pages(lines[a:b]))

TAIL_OK = re.compile(r'(unidad de medida|forma de medici|norma de medici|descripci[oó]n|'
                     r'\((?:m|m2|m3|kg|Und\.?|Glb\.?|Pto\.?|km|h)\)\s*\.?)\s*$', re.I)


def es_encabezado(seq, i):
    """Descarta codigos que son continuacion de una frase (texto justificado)."""
    if i == 0:
        return True
    prev = seq[i - 1].rstrip()
    if not prev.strip():
        return True
    if prev.endswith(('.', ':', ';', '!', '?')):
        return True
    if prev.strip().isupper():
        return True
    if TAIL_OK.search(prev):
        return True
    return False


positions = []
for i, l in enumerate(body):
    m, m2 = CODE_RE.match(l), CODE_INLINE_RE.match(l)
    if not (m or m2):
        continue
    if not es_encabezado(body, i):
        continue
    if m:
        positions.append((i, m.group(1), ''))
    else:
        positions.append((i, m2.group(1), m2.group(2)))


def is_desc(child, parent):
    return child.startswith(parent + '.')


own_block, sub_block = {}, {}
for n, (i, code, rest) in enumerate(positions):
    end = positions[n + 1][0] if n + 1 < len(positions) else len(body)
    own = ([rest] if rest else []) + body[i + 1:end]
    j = n + 1
    while j < len(positions) and is_desc(positions[j][1], code):
        j += 1
    sub_end = positions[j][0] if j < len(positions) else len(body)
    sub = ([rest] if rest else []) + body[i + 1:sub_end]
    def score(blk):
        has = any(re.match(r'\s*(unidad de medida|forma de medici|norma de medici)', x, re.I)
                  for x in blk)
        return (1 if has else 0, len(blk))
    if code not in own_block or score(own) > score(own_block[code]):
        own_block[code] = own
        sub_block[code] = sub

# ------------------------------------------------------------------ 3) UNIDAD / REGLA
UM_LINE = re.compile(r'^\s*unidad\s+de\s+medida\s*[:.]?\s*(.*)$', re.I)
FM_LINE = re.compile(r'^\s*(?:forma|norma)\s+de\s+(?:medici[oó]n|medida)\s*[:.]?\s*(.*)$', re.I)
TABLE_HDR = re.compile(r'^\s*(descripci[oó]n|unidad de medida|c[oó]digo|partida)\s*\.?\s*$', re.I)
PAREN = re.compile(r'\(([^()]{1,12})\)')

UNIT_MAP = {'m2': 'm2', 'm2.': 'm2', 'm²': 'm2',
            'm3': 'm3', 'm3.': 'm3', 'm³': 'm3',
            'm': 'm', 'm.': 'm', 'ml': 'm', 'ml.': 'm',
            'kg': 'kg', 'kg.': 'kg',
            'und': 'und', 'und.': 'und', 'und..': 'und', 'unid': 'und', 'u': 'und',
            'glb': 'glb', 'glb.': 'glb', 'gbl': 'glb',
            'pto': 'pto', 'pto.': 'pto', 'pto..': 'pto',
            'km': 'km', 'km.': 'km',
            'h': 'h', 'hh': 'h', 'hm': 'h',
            'p2': 'p2', 'pza': 'pza'}


def units_in(text):
    out = []
    for m in PAREN.finditer(text):
        k = m.group(1).strip().lower()
        if k in UNIT_MAP and UNIT_MAP[k] not in out:
            out.append(UNIT_MAP[k])
    return out


def extract_unit(block):
    """(lista_unidades, literal). Busca la etiqueta 'Unidad de Medida'."""
    for i, l in enumerate(block):
        m = UM_LINE.match(l)
        if not m:
            continue
        seg = [m.group(1)] if m.group(1).strip() else []
        for l2 in block[i + 1:]:
            if FM_LINE.match(l2) or UM_LINE.match(l2):
                break
            s = l2.strip()
            if not s or TABLE_HDR.match(s):
                continue
            seg.append(s)
            if len(seg) >= 5:
                break
        seg_txt = ' '.join(seg)
        u = units_in(seg_txt)
        if u:
            # literal = primer fragmento con unidad
            lit = next((x for x in seg if units_in(x)), seg_txt)
            return u, clean(lit)[:200]
    # fallback: cualquier linea corta con token de unidad
    for l in block:
        s = l.strip()
        if 0 < len(s) < 160 and units_in(s):
            return units_in(s), clean(s)[:200]
    return [], None


def extract_forma(block):
    for i, l in enumerate(block):
        m = FM_LINE.match(l)
        if not m:
            continue
        out = [m.group(1)] if m.group(1).strip() else []
        for l2 in block[i + 1:]:
            if is_code_line(l2) or UM_LINE.match(l2) or FM_LINE.match(l2):
                break
            out.append(l2.strip())
        t = clean(' '.join(out))
        if len(t) > 12:
            return t
    return None


def extract_alcance(block):
    """Parrafo descriptivo posterior al titulo y previo a 'Unidad de Medida'."""
    out = []
    seen_title = False
    for l in block:
        if UM_LINE.match(l) or FM_LINE.match(l) or is_code_line(l):
            break
        s = l.strip()
        if not s:
            continue
        if TABLE_HDR.match(s) or s.lower() in ('descripcion', 'descripción'):
            continue
        if not seen_title:          # 1a linea util = nombre de la partida
            seen_title = True
            if s.isupper() or s.rstrip('.').isupper():
                continue
        out.append(s)
    t = clean(' '.join(out))
    return t if len(t) > 40 else None


# ------------------------------------------------------------------ 4) ARMADO
ESPEC = {
    'OE.1': 'OE.1 Obras provisionales, trabajos preliminares, seguridad y salud',
    'OE.2': 'OE.2 Estructuras',
    'OE.3': 'OE.3 Arquitectura',
    'OE.4': 'OE.4 Instalaciones sanitarias',
    'OE.5': 'OE.5 Instalaciones electricas y mecanicas',
    'OE.6': 'OE.6 Instalaciones de comunicaciones',
    'OE.7': 'OE.7 Instalaciones de gas',
    'HU.1': 'HU.1 Obras provisionales, trabajos preliminares, seguridad y salud (HU)',
    'HU.2': 'HU.2 Pistas y veredas',
    'HU.3': 'HU.3 Infraestructura sanitaria',
    'HU.4': 'HU.4 Infraestructura electrica',
    'HU.5': 'HU.5 Infraestructura de comunicaciones',
    'HU.6': 'HU.6 Infraestructura de gas',
}
FUENTE = ('R.D. N 073-2010-VIVIENDA/VMCS-DNC - Norma Tecnica "Metrados para Obras de '
          'Edificacion y Habilitaciones Urbanas" (MVCS - Direccion Nacional de Construccion). '
          'PDF oficial SPIJ-MINJUS: '
          'https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf')

all_codes = set(index_map) | set(own_block)


def sort_key(c):
    return (0 if c.startswith('OE') else 1, [int(x) for x in c.split('.')[1:]])


all_codes = sorted(all_codes, key=sort_key)

info = {}
for c in all_codes:
    ob, sb = own_block.get(c, []), sub_block.get(c, [])
    u_own, lit_own = extract_unit(ob)
    f_own = extract_forma(ob)
    u_sub, lit_sub = extract_unit(sb)
    f_sub = extract_forma(sb)
    if c.count('.') <= 1:   # OE.1..OE.7 / HU.1..HU.6: capitulos, no partidas
        u_sub, lit_sub, f_sub = [], None, None
    info[c] = dict(u_own=u_own, lit_own=lit_own, f_own=f_own,
                   u_sub=u_sub, lit_sub=lit_sub, f_sub=f_sub,
                   alcance=extract_alcance(ob), en_cuerpo=c in own_block)

# Si la "forma de medicion" hallada en el subarbol de un padre es en realidad la de
# uno de sus hijos (caso HU.3 -> HU.3.2), se descarta para no contaminar hermanos.
children = collections.defaultdict(list)
for c in all_codes:
    par = c.rsplit('.', 1)[0]
    if par.count('.') >= 1 and par in info:
        children[par].append(c)
for par, kids in children.items():
    fs = info[par]['f_sub']
    # solo se descarta si el hijo duenno de esa regla tiene parrafo descriptivo propio
    # (partida real); si el hijo es solo un item de una lista enumerada, la regla es
    # del grupo y aplica tambien al padre.
    if fs and any(info[k]['f_own'] == fs and info[k]['alcance'] for k in kids):
        info[par]['f_sub'] = None

CROSSREF = re.compile(r'[^.]*(?:forma de medici[oó]n|unidad de medida)[^.]*\.', re.I)


def ancestors(c):
    p = c.split('.')
    for k in range(len(p) - 1, 2, -1):   # no se hereda del capitulo (nivel 1)
        yield '.'.join(p[:k])


partidas = []
for c in all_codes:
    d = info[c]
    desc = index_map.get(c) or ''
    if not desc and d['en_cuerpo']:
        desc = clean(next((x for x in own_block[c] if x.strip()), '')).rstrip('.')
    desc = re.sub(r'\s*\(\*+\)\s*$', '', desc).strip()
    if len(desc) < 2:
        continue

    # unidad
    if d['u_own']:
        u, lit, u_src = d['u_own'], d['lit_own'], 'propia'
    elif d['u_sub']:
        u, lit, u_src = d['u_sub'], d['lit_sub'], 'subpartidas'
    else:
        u, lit, u_src = [], None, None
        for a in ancestors(c):
            if info.get(a, {}).get('u_own'):
                u, lit, u_src = info[a]['u_own'], info[a]['lit_own'], 'heredada de ' + a
                break
            if info.get(a, {}).get('u_sub'):
                u, lit, u_src = info[a]['u_sub'], info[a]['lit_sub'], 'heredada de ' + a
                break

    # regla
    if d['f_own']:
        f, f_src = d['f_own'], 'propia'
    elif d['f_sub']:
        f, f_src = d['f_sub'], 'subpartidas'
    else:
        f, f_src = None, None
        if d['alcance']:
            m = CROSSREF.search(d['alcance'])
            if m:
                f, f_src = clean(m.group(0)), 'referencia cruzada en el texto de la partida'
        for a in ancestors(c):
            if f:
                break
            if info.get(a, {}).get('f_own'):
                f, f_src = info[a]['f_own'], 'heredada de ' + a
                break
            if info.get(a, {}).get('f_sub'):
                f, f_src = info[a]['f_sub'], 'heredada de ' + a
                break

    esp = ESPEC.get('.'.join(c.split('.')[:2]), '')
    verificado = bool(u_src == 'propia' and f_src == 'propia')
    partidas.append({
        'codigo': c,
        'descripcion': desc,
        'unidad': u[0] if u else None,
        'unidades_alternativas': u[1:],
        'unidad_literal_norma': lit,
        'especialidad': esp,
        'nivel': c.count('.'),
        'alcance': d['alcance'],
        'regla_medicion': f,
        'origen_unidad': u_src or 'no declarada en la norma',
        'origen_regla': f_src or 'no declarada en la norma',
        'fuente': FUENTE,
        'verificado': verificado,
    })

# --------- resolucion de referencias cruzadas: "Todo lo indicado en OE.x.y"
REF = re.compile(r'todo lo indicado en\s+((?:OE|HU)\.\d+(?:\.\d+)*)', re.I)
byc = {p['codigo']: p for p in partidas}
for _ in range(3):
    for p in partidas:
        if p['regla_medicion']:
            continue
        base = ' '.join(filter(None, [p.get('alcance') or '']))
        m = REF.search(base)
        if m and m.group(1) in byc and byc[m.group(1)]['regla_medicion']:
            p['regla_medicion'] = byc[m.group(1)]['regla_medicion']
            p['origen_regla'] = 'referencia expresa a ' + m.group(1)
            if not p['unidad'] and byc[m.group(1)]['unidad']:
                p['unidad'] = byc[m.group(1)]['unidad']
                p['origen_unidad'] = 'referencia expresa a ' + m.group(1)

for p in partidas:
    p['verificado'] = bool(p['unidad'] and p['regla_medicion']
                           and p['origen_unidad'] == 'propia'
                           and p['origen_regla'] == 'propia')

# ---------------------------------------------------------------- 5) EXPORTACION
URL = 'https://spij.minjus.gob.pe/Graficos/Peru/2011/Mayo/18/RD-073-2010-VIVIENDA-VMCS-DNC.pdf'
FUENTE_TXT = ('R.D. N° 073-2010-VIVIENDA/VMCS-DNC — Norma Técnica '
              '«Metrados para Obras de Edificación y Habilitaciones Urbanas» '
              '(MVCS, Dirección Nacional de Construcción, 2010)')

export = [{
    'codigo': x['codigo'],
    'descripcion': x['descripcion'],
    'unidad': x['unidad'],
    'especialidad': x['especialidad'],
    'regla_medicion': x['regla_medicion'],
    'fuente': FUENTE_TXT,
    'url_fuente': URL,
    'nivel': x['nivel'],
    'partida_padre': x['codigo'].rsplit('.', 1)[0] if x['nivel'] > 1 else None,
    'unidades_alternativas': x['unidades_alternativas'],
    'unidad_literal_norma': x['unidad_literal_norma'],
    'alcance': x['alcance'],
    'origen_unidad': x['origen_unidad'],
    'origen_regla': x['origen_regla'],
    'verificado': x['verificado'],
} for x in partidas]

json.dump(export, open(SALIDA, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('escrito:', SALIDA)

print('total:', len(partidas))
print('con unidad:', sum(1 for p in partidas if p['unidad']))
print('con regla:', sum(1 for p in partidas if p['regla_medicion']))
print('verificadas (unidad+regla propias):', sum(1 for p in partidas if p['verificado']))
print(collections.Counter(p['unidad'] for p in partidas))
print(collections.Counter(p['especialidad'] for p in partidas))
print(collections.Counter(p['origen_regla'].split(' de ')[0] for p in partidas))
