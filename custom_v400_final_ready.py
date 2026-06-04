
import os
from flask import jsonify, request, redirect, flash

V400_VERSION = "v4.0-final-pronto"

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE=os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0").lower() in ("1","true","sim","yes","on"),
    MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH", str(8 * 1024 * 1024)))
)

@app.after_request
def v400_security_headers(resp):
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    if request.headers.get("X-Forwarded-Proto", request.scheme) == "https":
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp

@app.route("/healthz")
def healthz_v400():
    try:
        q("SELECT 1", one=True)
        return jsonify({"ok": True, "app": "professor", "version": V400_VERSION})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

def bncc_info_for_question_v400(qq):
    try:
        hid = int(qq["bncc_habilidade_id"] or 0)
    except Exception:
        hid = 0
    row = q("SELECT * FROM bncc_habilidades WHERE id=?", (hid,), True) if hid else None
    if not row and qq["bncc_code"]:
        row = q("SELECT * FROM bncc_habilidades WHERE codigo=?", (qq["bncc_code"],), True)
    return row

def bncc_info_for_topic_v400(top):
    try:
        hid = int(top["bncc_habilidade_id"] or 0)
    except Exception:
        hid = 0
    row = q("SELECT * FROM bncc_habilidades WHERE id=?", (hid,), True) if hid else None
    if not row and top["bncc_code"]:
        row = q("SELECT * FROM bncc_habilidades WHERE codigo=?", (top["bncc_code"],), True)
    return row

def bncc_line_question_v400(qq):
    row = bncc_info_for_question_v400(qq)
    if row:
        return f"   BNCC: {row['codigo']} - {row['descricao']}\n"
    if qq["bncc_code"]:
        return f"   BNCC: {qq['bncc_code']}\n"
    return ""

def q_student(qq, n):
    s = f"{n}. {qq['statement']}\n   {qq['command']}\n"
    s += bncc_line_question_v400(qq)
    if qq['type'] == 'MULTIPLA':
        for a in q('SELECT * FROM alternatives WHERE question_id=? ORDER BY letter', (qq['id'],)):
            s += f"   {a['letter']}) {a['text']}\n"
    elif qq['type'] == 'VF':
        s += '   (   ) Verdadeiro    (   ) Falso\n'
    elif qq['type'] == 'LACUNAS':
        s += '   Resposta: ________________________________________________\n'
    else:
        s += '   Resposta: ________________________________________________\n'
    return s

def q_teacher(qq, n):
    s = f"{n}. {qq['statement']}\n"
    s += bncc_line_question_v400(qq)
    s += f"   Resposta: {qq['answer']}\n   Explicação: {qq['explanation']}\n"
    return s

def bncc_block_v400(top):
    row = bncc_info_for_topic_v400(top)
    if not row:
        code = top["bncc_code"] if "bncc_code" in top.keys() else ""
        return f"Habilidade BNCC: {code or 'não vinculada'}\n\n"
    return f'''BNCC
Código: {row['codigo']}
Etapa/Ano: {row['etapa']} - {row['ano_serie']}
Área/Componente: {row['area']} - {row['componente']}
Unidade temática/Campo: {row['unidade_tematica'] or row['campo_experiencia']}
Objeto de conhecimento: {row['objeto_conhecimento']}
Habilidade: {row['descricao']}

'''

def plano_v400():
    if request.method == 'POST':
        u = user(); sub, gr, top = get_sel()
        if not (sub and gr and top):
            flash('Escolha matéria, turma e conteúdo válidos.')
            return redirect('/professor/plano')
        pl = q('SELECT * FROM lessons WHERE topic_id=? ORDER BY RANDOM() LIMIT 1', (top['id'],), one=True)
        bncc = bncc_block_v400(top)
        if not pl:
            txt = f'''PLANO DE AULA

Disciplina: {sub['name']}
Turma: {gr['name']}
Tema: {top['name']}
Duração: 50 minutos

{bncc}Objetivo:
Compreender e aplicar conhecimentos relacionados ao tema.
'''
        else:
            txt = f'''PLANO DE AULA

Título: {pl['title']}
Disciplina: {sub['name']}
Turma: {gr['name']}
Tema: {top['name']}
Duração: {pl['duration']}

{bncc}Objetivo:
{pl['objective']}

Metodologia:
{pl['methodology']}

Recursos:
{pl['resources']}

Desenvolvimento:
{pl['development']}

Avaliação:
{pl['evaluation']}

Tarefa:
{pl['homework']}
'''
        mid = material_insert(u['id'], 'Plano de aula', f'Plano de aula - {top["name"]}', txt, '')
        return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Planejar Aula</h1><p>Plano de aula completo com habilidade BNCC vinculada.</p></div></div><div class="panel"><form method="post">'+form_selector()+'<div class="preview-note"><b>O plano inclui:</b> objetivo, BNCC, metodologia, recursos, desenvolvimento, avaliação e tarefa.</div><button class="btn primary big">Gerar plano de aula</button></form></div>')

app.view_functions["plano"] = login_required(plano_v400)
