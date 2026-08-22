#!/usr/bin/env python3
"""
Deterministic auditor for an autonomous agent fleet.

Runs every night against the fleet's own rulebook, prompts and journal, and
exits with a list of concrete failures or the word LIMPIO (clean).

The idea: rules written in prose are not enforced, they are aspirational.
Every rule that can be expressed as a check belongs here instead.

Set <WORKSPACE> to your own paths before running.
"""
# Auditoria determinista de 10 dimensiones sobre los 3 crons del job hunt.
# Creado 2026-08-12 (L147). El auditor lo ejecuta cada noche: python3 <WORKSPACE>/JobHunt/audit_10d.py
# Salida: "LIMPIO" o lista de fallos. Un fallo = incidencia que el auditor corrige en el mismo run.
import re, sys, json, os

BASE = '<WORKSPACE>'
rb = open(f'{BASE}/JobHunt/Rulebook_Vigente.md', encoding='utf-8').read()
_ini = rb.index("## A0.") if "## A0." in rb else rb.index("## A. PROTOCOLO")
body = rb[_ini:]
idx = rb[rb.index("## INDICE"):_ini]
fails = []

def rule_exists(c):
    base = re.match(r"([A-F]\d+(?:\.\d+)?(?:-[A-Z]+)?)", c)
    if not base: return True
    b = base.group(1)
    if b == "A0": return "## A0. PROACTIVIDAD" in rb
    if re.search(r"^" + re.escape(b) + r"[ .\[]", body, re.M): return True
    # sub-referencia tipo E14.1: valida si la seccion padre existe y contiene el punto numerado
    m = re.match(r"([A-F]\d+(?:-[A-Z]+)?)\.(\d+)$", b)
    if m:
        parent, sub = m.group(1), m.group(2)
        sec = re.search(r"^" + re.escape(parent) + r"[ .\[].*?(?=^[A-F]\d|\Z)", body, re.M | re.S)
        if sec and re.search(r"^" + sub + r"\.", sec.group(0), re.M): return True
    return False

for task in ['job-hunt-daily', 'linkedin-engagement-daily', 'job-hunt-audit']:
    pr = open(f'{BASE}/Scheduled/{task}/SKILL.md', encoding='utf-8').read()
    # 1 reglas fantasma
    for c in sorted(set(re.findall(r"\b([A-F]\d+(?:\.\d+)?(?:-[A-Z]+)?)\b", pr))):
        if not rule_exists(c): fails.append(f"{task}: cita regla inexistente {c}")
    # 2 presupuesto de tiempo
    m = re.search(r"(\d+)-(\d+) min\b", pr)
    if m and int(m.group(2)) > 60 and 'void' not in pr: fails.append(f"{task}: presupuesto {m.group(0)} contradice E14.2 (60 min buffer)")
    # 3 parametros muertos
    if re.findall(r"f_E=|f_JT=|f_WT=|sortBy=", pr): fails.append(f"{task}: parametros muertos en prompt")
    # 4 frontmatter modelo
    if "model: opus" not in pr.split("---")[1]: fails.append(f"{task}: sin model: opus (hard norm E13)")
    # 5 horas literales (A5b)
    if re.search(r"0?7:45|20:30|21:45|07:54|20:34|21:53", pr): fails.append(f"{task}: horas literales")
    # 6 segmentos E4 copiados (A5b)
    if re.search(r"Respuestas / Engagement|Gmail / Notificaciones", pr): fails.append(f"{task}: segmentos E4 copiados")

# 7 contradiccion cupo no-EA vs E3.0
if re.search(r"o 3 no-EA(?!.*ANULADO)", rb): fails.append("Rulebook: cupo no-EA vivo contra E3.0")
# 8 COHERENCIA DE CANAL ENTRE E3.0 Y E3-BIS.5 (MODERNIZADA 2026-08-19, L198).
# Hasta hoy esta dimension exigia LO CONTRARIO: que E3-BIS.5 llevase f_AL=true en los tres pases.
# Nacio el 12-08, cuando E3.0 prohibia los ATS externos y Easy Apply era el canal unico, asi que el
# invariante correcto entonces era "no te dejes f_AL". El 19-08 OWNER derogo esa prohibicion (L191)
# y E3.0(f) ordeno explicitamente lanzar los pases SIN f_AL y modernizar esta dimension. Durante ese
# intervalo el guarda estaba DEFENDIENDO LA NORMA DEROGADA: daba LIMPIO justo porque el Rulebook
# conservaba el filtro que ya no debia aplicarse, es decir que el script habria bloqueado la correccion
# en vez de detectar el fallo. Es el peor modo de fallo de un guarda y por eso se deja escrito.
# INVARIANTE VIGENTE: E3.0 y E3-BIS.5 tienen que decir lo MISMO sobre el canal. Si E3.0 declara
# derogada la prohibicion de ATS externos, E3-BIS.5 no puede seguir prescribiendo f_AL en sus pases.
e30 = re.search(r"^E3\.0 .*$", body, re.M)
p5 = re.search(r"^5\. TRES PASES.*$", body, re.M)
if e30 and p5:
    derogada = re.search(r"prohibicion de ATS externos.*?DEROGADA|DEROGADA", e30.group(0))
    # se miran solo las RECETAS de los pases (a), (b) y (c), no la prosa historica que cita el pasado
    recetas = re.findall(r"\([abc]\) [A-ZÑ ]+:[^.]*", p5.group(0))
    con_fal = [r for r in recetas if 'f_AL' in r]
    if derogada and con_fal:
        fails.append(f"Rulebook: E3.0 deroga el canal unico pero E3-BIS.5 sigue prescribiendo f_AL en {len(con_fal)} pase(s) -> {con_fal[0][:80]}")
    if not derogada and len(recetas) - len(con_fal) > 0:
        fails.append("Rulebook: E3.0 mantiene el canal unico Easy Apply pero E3-BIS.5 tiene pases sin f_AL")
# 9 huerfanas del indice (exentas las solo-auditor declaradas)
rules = set(re.findall(r"^((?:[A-F]\d+(?:\.\d+)?(?:-[A-Z]+)?)|C0)\.", body, re.M))
work = idx.split("- **job-hunt-audit**")[0]
cited = set(re.findall(r"\b((?:[A-F]\d+(?:\.\d+)?(?:-[A-Z]+)?)|C0)\b", work))
for sec in re.findall(r"\b([A-F]) \(toda", work):
    ex = set()
    mm = re.search(r"\b" + sec + r" \(toda SALVO ([^)]*)\)", work)
    if mm: ex = set(re.findall(r"[A-F]\d+", mm.group(1)))
    cited |= {r for r in rules if r.startswith(sec) and r not in ex}
exempt = set(re.findall(r"SOLO DEL AUDITOR[^:]*: ([^.]+)\.", idx))
exempt_rules = set(re.findall(r"[A-F]\d+(?:-[A-Z]+)?", " ".join(exempt))) | {'E6','E8','E15','F9-HISTORICO'}
orphans = [r for r in sorted(rules) if r not in cited and r not in exempt_rules]
if orphans: fails.append(f"Rulebook: huerfanas {orphans}")
# 10 colisiones de numeracion en el diario
j = open(f'{BASE}/JobHunt/Job_Search_Learnings.md', encoding='utf-8').read()
nums = re.findall(r"^## (L\d+)", j, re.M)
dup = sorted({n for n in nums if nums.count(n) > 1})
if dup: fails.append(f"Diario: colisiones {dup}")

# 11 citas fantasma al diario (auditoria 2026-08-12, L149): el Rulebook y los prompts citan
# entradas del diario como prueba de origen. Una cita a una entrada que no existe es
# trazabilidad aparente: parecia que la norma estaba documentada y no lo estaba (caso E3.0 -> L140).
# El diario mezcla dos formatos de cabecera: "## L134 | ..." y "- L119 (2026-08-10): ...".
have = set(re.findall(r"^(?:## |- )(L\d+)", j, re.M))
sources = {'Rulebook': rb}
for task in ['job-hunt-daily', 'linkedin-engagement-daily', 'job-hunt-audit']:
    sources[task] = open(f'{BASE}/Scheduled/{task}/SKILL.md', encoding='utf-8').read()
for name, txt in sources.items():
    ghosts = sorted({m for m in re.findall(r"\bL\d+\b", txt) if m not in have}, key=lambda x: int(x[1:]))
    if ghosts: fails.append(f"{name}: cita entradas de diario inexistentes {ghosts}")

# 12 AMPLIFY TEST bandas de palabras del ultimo comentario publicado (25-40 o 60-75; prohibido 45-56)
led=open(f'{BASE}/JobHunt/Engagement_Ledger.md',encoding='utf-8').read()
pubs=re.findall(r'COMENTARIO PUBLICADO[^"]*"([^"]{40,})"',led)
if pubs:
    wc=len(pubs[-1].split())
    ok=(25<=wc<=40) or (60<=wc<=75)
    # solo aplica a comentarios posteriores a la norma (13-08); heuristica: falla solo si la entrada es de fecha >=2026-08-13
    tail=led[led.rfind(pubs[-1][:30])-2500:led.rfind(pubs[-1][:30])]
    post_norma=re.search(r'2026-08-1[3-9]|2026-08-[2-3]\d|2026-09',tail)
    if post_norma and not ok:
        fails.append(f"Ledger: ultimo comentario {wc} palabras, fuera de bandas AMPLIFY (25-40 o 60-75)")

# 13 COBERTURA EXPLICITA DEL INDICE (anadida 2026-08-13, L154).
# Defecto que la origina: F10 no estaba NI en "lee integras" NI en "NO necesita" de la fila de
# linkedin-engagement-daily, asi que cuando ese run leyo y ADEMAS reescribio F10 nadie lo detecto.
# La dimension 9 solo veia huerfanas globales (seccion que ninguna fila menciona), y F10 si estaba
# en la fila del daily, luego pasaba limpia. Una seccion no mencionada en la fila de una tarea es
# un silencio, y un silencio no es una decision: cada fila debe DECIDIR sobre cada seccion.
AUDIT_ONLY = {'E6', 'E8', 'E15', 'F9-HISTORICO'}
secs = set()
for m in re.finditer(r"^((?:C|E|F)\d+(?:\.0)?(?:-[A-Z]+)?)[ .]", body, re.M):
    s = m.group(1)
    if s not in AUDIT_ONLY: secs.add(s)
rows = {}
for line in idx.splitlines():
    m = re.match(r"\s*-\s+\*\*(job-hunt-daily|linkedin-engagement-daily)\*\*", line)
    if m: rows[m.group(1)] = line
for task, line in rows.items():
    for s in sorted(secs):
        # token exacto: F1 no debe darse por cubierto por F12, ni E1 por E1-BIS
        if not re.search(r"(?<![A-Z0-9.-])" + re.escape(s) + r"(?![A-Z0-9]|-[A-Z]|\.\d)", line):
            fails.append(f"{task}: la fila del indice no decide sobre {s} (ni la lee ni la excluye)")

# 14 DERIVA DEL CANAL DE INFORME E4 (anadida 2026-08-17, L179).
# Defecto que la origina: E4 cambio a Gmail como canal primario la tarde del 17-08 y el prompt del
# AUDITOR siguio ordenando "send ONE line to WhatsApp 660 92 59 33". La dimension 6 ya vigilaba que
# los prompts no COPIASEN la lista de segmentos de E4, pero no que no contradijesen su CANAL, que es
# justo la parte de E4 que OWNER cambia por orden directa. Un prompt que manda informar por un canal
# retirado es una copia obsoleta de manual (A5b y A5c) y ademas rompe el informe de verdad, porque el
# clasificador de WhatsApp lo bloquea (F16). Regla: si E4 declara Gmail canal primario, ninguna mencion
# de WhatsApp en un prompt puede ir asociada al informe rutinario; solo vale para avisos urgentes.
m_e4 = re.search(r"^E4\.[^\n]*", body, re.M)
if m_e4 and 'GMAIL' in m_e4.group(0).upper() and 'PRIMARIO' in m_e4.group(0).upper():
    for task, txt in sources.items():
        if task == 'Rulebook': continue
        for sent in re.split(r"(?<=[.!?])\s+", txt):
            if not re.search(r"whatsapp|660 ?92 ?59 ?33", sent, re.I): continue
            habla_de_informe = re.search(r"informe|report|send ONE line|enviar? ?(el)? ?informe", sent, re.I)
            es_urgente = re.search(r"urgent|urgente|aviso|alert", sent, re.I)
            if habla_de_informe and not es_urgente:
                fails.append(f"{task}: manda informar por WhatsApp pese a que E4 fija Gmail como canal primario -> '{sent.strip()[:110]}'")

# 15 COLISIONES DE NUMERACION DE SECCION EN EL RULEBOOK (anadida 2026-08-18, L187).
# Defecto que la origina: el Rulebook tuvo del 14 al 18 de agosto DOS secciones numeradas F12, la de
# Easy Apply (13-08, L150) y la del enlace de Drive (14-08, L153). Toda cita a "F12" resolvia a las dos
# a la vez: E3.0 y F10 apuntaban a una, el indice y F13.3 a la otra, y la fila de fin de semana citaba
# la equivocada. La dimension 10 ya vigilaba colisiones en el DIARIO y nadie habia mirado el sitio donde
# de verdad duelen, que es el registro de normas. Precedente que lo demuestra: F17 nacio como F16 y hubo
# que renumerarla en el acto el 17-08 por la misma causa, y aquello se arreglo a mano sin dejar guarda.
secnums = re.findall(r"^((?:[A-F]\d+(?:\.\d+)?(?:-[A-Z]+)?))[ .]", body, re.M)
dupsec = sorted({s for s in secnums if secnums.count(s) > 1})
if dupsec: fails.append(f"Rulebook: numeros de seccion duplicados {dupsec} (cada cita a ese numero resuelve a dos normas)")

# 16 CUADRE DE LA FASE DE APLICACIONES (anadida 2026-08-18, L187, con E3-TER.4).
# Defecto que la origina: el daily del 18-08 declaro 19 resultados, envio 3 candidaturas y registro 15
# descartes. 3+15=18, y la tarjeta que faltaba (Head Of B2C, Madrid hibrido, Easy Apply) era elegible por
# modalidad. Ninguna norma exigia que las cifras SUMASEN, asi que el hueco no era detectable. E3-TER.4
# obliga desde hoy a escribir la igualdad literal "N resultados = X aplicadas + Y descartadas"; esta
# dimension comprueba que existe y que ademas es cierta. Solo aplica a entradas de diario del 19-08 en
# adelante: A1 prohibe juzgar lo pasado con una regla que aun no existia.
for m in re.finditer(r"^## (L\d+) \| (2026-\d\d-\d\d) \|([^\n]*)\n(.*?)(?=^## L|\Z)", j, re.M | re.S):
    fecha, titulo, cuerpo = m.group(2), m.group(3), m.group(4)
    if fecha < '2026-08-19': continue
    if 'job-hunt-daily' not in titulo and 'job-hunt-daily' not in cuerpo[:2000]: continue
    if not re.search(r"resultados", cuerpo): continue
    # Corregido 2026-08-19 (L189): la version original solo admitia "X aplicadas + Y descartadas" y dio
    # falso positivo con el L188 real ("2 aplicadas + 1 guardada sin enviar + 6 descartadas"). Ahora se
    # admiten terminos intermedios y se comprueba que TODOS los sumandos del lado derecho suman N.
    eq = re.search(r"(\d+)\s*resultados?\s*=\s*([^\n.]+)", cuerpo)
    if not eq or 'aplicada' not in eq.group(2) or 'descartada' not in eq.group(2):
        fails.append(f"Diario {m.group(1)}: fase de aplicaciones sin la igualdad de cuadre que exige E3-TER.4")
    else:
        sumandos = [int(x) for x in re.findall(r"\d+", eq.group(2))]
        if int(eq.group(1)) != sum(sumandos):
            fails.append(f"Diario {m.group(1)}: el cuadre de E3-TER.4 no suma ({eq.group(0).strip()})")

# 17 UNA IGUALDAD DE CUADRE POR CADA PASE DECLARADO (anadida 2026-08-19, L198, con E3-TER.4 ampliada).
# Defecto que la origina, y es un defecto de ESTA herramienta, no solo del run: la dimension 16 usa
# re.search, que se para en la PRIMERA igualdad que encuentra. El daily del 19-08 lanzo dos pases,
# escribio la igualdad del de Espana (9 = 2+1+6, correcta) y NINGUNA para el de la UE, donde declaro
# 47 resultados y dejo la pagina 2 sin mirar. La dimension 16 dio LIMPIO sobre esa entrada porque la
# primera igualdad existia y cuadraba. Un run puede asi cumplir con un pase y callar sobre los demas,
# que es el mismo mecanismo de silencio de F10 en el indice: lo no mencionado no es lo aprobado.
# REGLA: se cuentan los pases que la entrada DECLARA (la palabra "PASE" en mayusculas, como los
# escribe el daily) y se exige al menos una igualdad de cuadre por cada uno.
for m in re.finditer(r"^## (L\d+) \| (2026-\d\d-\d\d) \|([^\n]*)\n(.*?)(?=^## L|\Z)", j, re.M | re.S):
    fecha, titulo, cuerpo = m.group(2), m.group(3), m.group(4)
    if fecha < '2026-08-19': continue
    if 'job-hunt-daily' not in titulo and 'job-hunt-daily' not in cuerpo[:2000]: continue
    pases = len(re.findall(r"^PASE [A-ZÑÁÉÍÓÚ]", cuerpo, re.M))
    if pases < 2: continue
    igualdades = len(re.findall(r"\d+\s*resultados?\s*=\s*[^\n.]*aplicada", cuerpo))
    if igualdades < pases:
        fails.append(f"Diario {m.group(1)}: {pases} pases declarados y solo {igualdades} igualdad(es) de cuadre; E3-TER.4 exige una por pase")

# 18 TODA CANDIDATURA ENVIADA POR CORREO CON EL CV ADJUNTO ESTA REGISTRADA EN LA BLACKLIST
# (anadida 2026-08-20, L201, con C0.6 y ejecutando E3-QUINQUIES(a)).
# Defecto que la origina, y es el hueco que E3-QUINQUIES(b) nombro sin poder cerrar: el CHAT envia
# candidaturas con las manos del sistema y NO escribe los ficheros de estado, asi que una candidatura
# suya es, para el dedupe de E3, una candidatura que nunca ocurrio. Medido el 20-08: siete correos con
# el CV adjunto (tres el 19-08 y cuatro entre las 21:34 y las 21:57 del 20-08) y CERO entradas en
# blacklist y pipeline; las cuatro ultimas ademas ya con E3-QUINQUIES en vigor desde esa misma manana.
# Ninguna dimension anterior podia verlo porque todas leen el Rulebook, los prompts y el diario, y esto
# no pasa por ninguno de los tres. La superficie que SI lo prueba y es legible por un script son los
# transcripts de sesion, que registran cada llamada a send_message con destinatario y adjuntos.
# LIMITE DECLARADO (A1): esto comprueba que la candidatura esta REGISTRADA, nunca como esta escrito el
# correo; el cuerpo lo audita una persona con C0.6(d).
import glob, time
SESS = os.path.expanduser('~/Library/Application Support/Claude/local-agent-mode-sessions')
def norm(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())
try:
    bl = json.load(open(f'{BASE}/JobHunt/Job_Application_Blacklist.json', encoding='utf-8'))
    CAMPANA_PUNTUAL_EXCLUIDA = ('strand.es', 'lacalasalesandrentals.com', 'ultimateestatesspain.com',
                                'serneholtestate.com', 'rhprive.com', 'costagroupestates.com',
                                'higueronhomes.com', 'miannaproperties.com', 'mxmobranueva.com')
    known = [norm(c.get('company')) for c in bl.get('companies', [])]
    seen, corte = set(), time.time() - 2 * 86400
    for path in glob.glob(f'{SESS}/**/*.jsonl', recursive=True):
        try:
            if os.path.getmtime(path) < corte: continue
        except OSError: continue
        for line in open(path, encoding='utf-8', errors='replace'):
            if 'send_message' not in line or 'attachments' not in line: continue
            try: d = json.loads(line)
            except Exception: continue
            for c in (d.get('message', {}).get('content') or []):
                if not (isinstance(c, dict) and c.get('type') == 'tool_use'): continue
                if not c.get('name', '').endswith('send_message'): continue
                i = c.get('input', {}) or {}
                dests = [t for t in (i.get('to') or []) if 'owner@example.com' not in t]
                if not dests: continue
                if not any(re.search(r'cv|curriculum|resume', a.get('filename', ''), re.I)
                           for a in (i.get('attachments') or [])): continue
                for dest in dests:
                    # EXCLUSION DE CAMPANA PUNTUAL (OWNER 2026-08-20): "no quiero que se mezcle
                    # nada de real estate con linkedin". Estas candidaturas viven en su propio
                    # registro, <WORKSPACE>/CV/templates/_puntual_realestate/, y NO se
                    # anotan en la blacklist ni en el pipeline del sistema. Si OWNER cierra la
                    # campana, esta lista se vacia y la dimension vuelve a cubrirlas.
                    if any(x in dest for x in CAMPANA_PUNTUAL_EXCLUIDA): continue
                    dom = dest.split('@')[-1]
                    tok = norm(dom.rsplit('.', 1)[0].replace('www.', ''))
                    if not tok or tok in seen: continue
                    seen.add(tok)
                    if not any(tok in k or (k and k in tok) for k in known if k):
                        fails.append(f"Candidatura enviada con CV a {dest} y SIN entrada en Job_Application_Blacklist.json (E3-QUINQUIES.a)")
except FileNotFoundError:
    pass


# ---------------------------------------------------------------- DIMENSION 19
# A0, gate de proactividad (OWNER 2026-08-21). Cobertura de FRAMEWORK COMPLETO:
# autoridad maxima, Rulebook, los 7 crons del disco, las skills persistidas que
# heredan los chats futuros, y la linea de evidencia en el diario. Sin esto, A0
# seria una intencion en vez de una norma exigible.
import glob as _glob
try:
    # (a) autoridad maxima
    try:
        drv = open(f'{BASE}/DIRECTIVES.md', encoding='utf-8').read()
        if '## 0. PROACTIVITY AND STRATEGIC JUDGMENT' not in drv:
            fails.append("DIRECTIVES.md: falta la seccion 0 (A0), la autoridad maxima no la lleva")
    except FileNotFoundError:
        fails.append("DIRECTIVES.md no encontrado")

    # (a2) gate de apertura en la autoridad maxima
    try:
        if 'OPENING GATE' not in drv:
            fails.append("DIRECTIVES.md: falta el gate de APERTURA de A0 (censo, objetivo real, contraejemplo, prueba de fallo)")
    except NameError:
        pass

    # (b) Rulebook
    if '## A0. PROACTIVIDAD Y CRITERIO ESTRATEGICO' not in rb:
        fails.append("A0 no esta en el Rulebook: la norma de rango supremo ha desaparecido")
    if 'GATE DE APERTURA A0' not in rb:
        fails.append("Rulebook: falta el gate de APERTURA de A0")

    # (c) TODOS los crons del disco, no solo los del job hunt
    for fp in sorted(_glob.glob(f'{BASE}/Scheduled/*/SKILL.md')):
        cron = fp.split('/')[-2]
        _t = open(fp, encoding='utf-8').read()
        if 'A0, NORMA DE RANGO SUPREMO' not in _t:
            fails.append("cron %s: su prompt no lleva el gate de cierre A0" % cron)
        if 'GATE DE APERTURA A0' not in _t:
            fails.append("cron %s: su prompt no lleva el gate de apertura A0" % cron)

    # (d) skills persistidas que heredan los chats futuros (la cache del plugin es
    #     de solo lectura, lo que persiste vive en skills-plugin)
    SK = '<WORKSPACE> Support/Claude/local-agent-mode-sessions/skills-plugin'
    for nombre, marca in (('norma-a0-proactividad', 'Gate de cierre, cuatro puntos'),
                          ('estilo-owner-nexo', 'NORMA DURA 0'),
                          ('linkedin-job-hunter-patches', 'A0 PROACTIVITY')):
        hits = _glob.glob(f'{SK}/*/*/skills/{nombre}/SKILL.md')
        if not hits:
            fails.append("skill persistida ausente: %s (los chats futuros no heredarian A0)" % nombre)
        elif not any(marca.lower() in open(h, encoding='utf-8').read().lower() for h in hits):
            fails.append("skill %s existe pero ya no contiene A0" % nombre)

    # (e) linea de evidencia en el diario, sin retroactividad
    diario = open(f'{BASE}/JobHunt/Job_Search_Learnings.md', encoding='utf-8').read()
    entradas = [e for e in re.split(r'\n## L\d+', diario)[1:] if e.strip()][-6:]
    def _fecha(e):
        m = re.search(r'\((20\d\d-\d\d-\d\d)', e[:80])
        return m.group(1) if m else '0000-00-00'
    A0_NACE = '2026-08-22'   # runs anteriores no se auditan contra A0
    for e in [x for x in entradas if _fecha(x) >= A0_NACE]:
        cab = e.strip().split('\n')[0][:70]
        if not re.search(r'A0:\s*VIGENCIA=.*DESBLOQUEO=.*SIGUIENTE=.*ESTRATEGICO=', e):
            fails.append("Diario, entrada '%s': cierra sin la linea de evidencia del gate A0" % cab)
except FileNotFoundError as _e:
    fails.append("Dimension 19 no pudo completarse: %s" % _e)


# ---------------------------------------------------------------- DIMENSION 20
# Las dos normas nacidas la noche del 21-08 (L206), que existen porque un barrido
# y una cola se declararon buenos sin serlo. Las dos son invisibles para el resto
# del script porque describen COMO se mira una superficie viva, asi que lo unico
# comprobable por maquina es (a) que la norma siga escrita y (b) que el diario no
# vuelva a declarar un barrido de bandeja "entero" por pantalla.
try:
    if 'LA LISTA RENDERIZADA SE SALTA HILOS QUE SI EXISTEN' not in rb:
        fails.append("F13.6 ha desaparecido del Rulebook: la bandeja volveria a enumerarse por pantalla")
    if 'messengerConversationsBySyncToken' not in rb:
        fails.append("F13.6 existe pero ha perdido la via determinista (messengerConversationsBySyncToken)")
    if 'UNA OFERTA NO ENTRA EN LA COLA DE "VIVAS"' not in rb:
        fails.append("E19.5 ha desaparecido del Rulebook: la cola volveria a heredarse con criterio de tarjeta")

    # El diario no puede volver a declarar barrido completo de bandeja sin la via
    # determinista. Sin retroactividad: la norma nace hoy y rige desde manana.
    F136_NACE = '2026-08-22'
    _diario = open(f'{BASE}/JobHunt/Job_Search_Learnings.md', encoding='utf-8').read()
    _entradas = [e for e in re.split(r'\n## L\d+', _diario)[1:] if e.strip()][-8:]
    for e in _entradas:
        m = re.search(r'\((20\d\d-\d\d-\d\d)', e[:80])
        if not m or m.group(1) < F136_NACE:
            continue
        low = e.lower()
        declara = any(s in low for s in ('lista entera', 'recorrido entero', 'lista completa'))
        if declara and 'messengerconversations' not in low:
            cab = e.strip().split('\n')[0][:70]
            fails.append("Diario, entrada '%s': declara barrido de bandeja entero sin la enumeracion determinista de F13.6" % cab)
except FileNotFoundError as _e:
    fails.append("Dimension 20 no pudo completarse: %s" % _e)

if fails:
    print(f"FALLOS ({len(fails)}):")
    for f in fails: print(" -", f)
    sys.exit(1)
print("LIMPIO: 20 dimensiones, 3 prompts, Rulebook, diario y correos de candidatura")
