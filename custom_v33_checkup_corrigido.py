# ============================================================
# AulaPronta Pro v3.3 - Checkup corrigido
# Corrige render sem usuário no login, restaura renovação do professor
# sem área admin, reforça rotas, banco compartilhado e mensagens.
# ============================================================

import os, secrets, re
from datetime import datetime, timedelta
from pathlib import Path
from flask import request, redirect, session, flash, send_file, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

V33_VERSION = "v3.3-checkup-corrigido"

PLANOS_PROFESSOR = {
    "mensal": {"label":"Mensal", "plan":"MENSAL", "amount":"19,90", "days":30},
    "semestral": {"label":"Semestral", "plan":"SEMESTRAL", "amount":"99,90", "days":180},
    "anual": {"label":"Anual", "plan":"ANUAL", "amount":"179,90", "days":365},
}

def v33_table_exists(name):
    try:
        return q("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,), True) is not None
    except Exception:
        return False

def v33_setup():
    with conn() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS payment_orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            amount TEXT,
            days INTEGER,
            status TEXT DEFAULT 'pendente',
            pix_key TEXT DEFAULT '',
            reference TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            paid_at TEXT DEFAULT '',
            approved_by INTEGER DEFAULT 0,
            note TEXT DEFAULT ''
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS admin_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            detail TEXT,
            created_at TEXT
        )''')
        c.commit()

v33_setup()

def v33_pix_key():
    return os.getenv("PIX_KEY") or os.getenv("CHAVE_PIX") or "configure-sua-chave-pix-no-env"

def v33_days_left(value):
    try:
        return (datetime.fromisoformat(value).date() - datetime.now().date()).days
    except Exception:
        return None

def user_initials(u):
    if not u:
        return "AP"
    name = (u["name"] or "Professor").strip()
    parts = [p for p in name.split() if p]
    if not parts:
        return "AP"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def v33_license_meta(u):
    if not u:
        return {"plan":"Visitante", "date":"---", "days":"", "status":"license-good"}
    d = v33_days_left(u["valid_until"])
    if d is None:
        return {"plan":u["plan"] or "Premium", "date":u["valid_until"] or "---", "days":"sem prazo", "status":"license-good"}
    if d < 0:
        return {"plan":u["plan"] or "Premium", "date":u["valid_until"] or "---", "days":"expirada", "status":"license-expired"}
    if d <= 7:
        return {"plan":u["plan"] or "Premium", "date":u["valid_until"] or "---", "days":f"{d} dia(s)", "status":"license-soon"}
    return {"plan":u["plan"] or "Premium", "date":u["valid_until"] or "---", "days":f"{d} dia(s)", "status":"license-good"}

def render(content, title="AulaPronta Pro"):
    # Versão segura: no login/cadastro user() retorna None, então não pode chamar user_initials(None) quebrando.
    u = user()
    meta = v33_license_meta(u)
    return render_template_string(BASE_HTML, content=content, title=title, u=u, license=meta, initials=user_initials(u), app_version=V33_VERSION)

def professor_license_card(u):
    meta = v33_license_meta(u)
    return f'<div class="final-license {meta["status"]}"><b>{esc(meta["plan"])}</b><span>Válido até {esc(meta["date"])} - {esc(meta["days"])}</span></div>'

def ensure_default_teacher():
    try:
        email = "professor@aulapronta.com"
        existing = q("SELECT id FROM users WHERE email=?", (email,), True)
        if not existing:
            valid = (datetime.now() + timedelta(days=365)).date().isoformat()
            q("INSERT INTO users(name,email,password,is_admin,plan,valid_until,school,city,state,avatar,teaching_style,local_context,default_instructions) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
              ("Professor Demonstração", email, generate_password_hash("professor123"), 0, "PREMIUM", valid,
               "Minha Escola", "", "", "", "Acolhedor e simples", "", ""))
    except Exception:
        pass

ensure_default_teacher()

# Limpa links administrativos do layout do professor, mas mantém assinatura e segurança.
try:
    BASE_HTML = re.sub(r"\{% if u\['is_admin'\] %\}.*?\{% endif %\}", "", BASE_HTML, flags=re.S)
    BASE_HTML = BASE_HTML.replace('<a href="/admin/pagamentos"><span>PG</span><div><b>Pagamentos</b><small>Aprovar renovações</small></div></a>', '')
    BASE_HTML = BASE_HTML.replace('<a href="/admin"><span>AD</span><div><b>Gestão Premium</b><small>Seriais, usuários e banco</small></div></a>', '')
except Exception:
    pass

def professor_login_page():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        if is_locked(email):
            flash("Muitas tentativas incorretas. Aguarde alguns minutos.")
            return redirect("/login")
        u = q("SELECT * FROM users WHERE email=?", (email,), True)
        if u and check_password_hash(u["password"], request.form.get("password", "")):
            clear_failed(email)
            session["uid"] = u["id"]
            return redirect("/professor")
        record_failed(email)
        flash("E-mail ou senha inválidos.")
    content = '''
    <div class="auth-card">
      <div class="auth-logo">AP</div>
      <h1>Entrar no AulaPronta</h1>
      <p class="sub">Acesso do professor para criar atividades, avaliações, planos e pareceres.</p>
      <form method="post">
        <p><label>E-mail</label><input name="email" placeholder="professor@escola.com"></p>
        <p><label>Senha</label><input name="password" type="password" placeholder="••••••••"></p>
        <button class="btn primary big">Entrar</button>
      </form>
      <a class="link" href="/cadastro">Criar conta de professor</a>
    </div>'''
    return render(content, "Login")

def professor_cadastro():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        senha = request.form.get("password", "")
        senha2 = request.form.get("password2", "")
        if not email or "@" not in email:
            flash("Informe um e-mail válido.")
            return redirect("/cadastro")
        if len(senha) < 6 or senha != senha2:
            flash("A senha precisa ter pelo menos 6 caracteres e confirmar corretamente.")
            return redirect("/cadastro")
        if q("SELECT id FROM users WHERE email=?", (email,), True):
            flash("Já existe uma conta com este e-mail.")
            return redirect("/cadastro")
        valid = (datetime.now() + timedelta(days=15)).date().isoformat()
        q("INSERT INTO users(name,email,password,is_admin,plan,valid_until,school,city,state,avatar,teaching_style,local_context,default_instructions) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (request.form.get("name", "Professor(a)"), email, generate_password_hash(senha), 0, "TESTE", valid,
           request.form.get("school", ""), request.form.get("city", ""), request.form.get("state", "")[:2], "",
           "Acolhedor e simples", "", ""))
        flash("Conta criada com sucesso. Faça login para entrar.")
        return redirect("/login")
    content = '''
    <div class="auth-card wide">
      <div class="auth-logo">AP</div>
      <h1>Criar conta de professor</h1>
      <p class="sub">Cadastro simples do professor. O controle de planos fica separado no Admin Center.</p>
      <form method="post">
        <div class="auth-grid">
          <p><label>Nome do professor</label><input name="name" placeholder="Seu nome"></p>
          <p><label>E-mail</label><input name="email" placeholder="professor@escola.com"></p>
          <p><label>Senha</label><input type="password" name="password"></p>
          <p><label>Confirmar senha</label><input type="password" name="password2"></p>
          <p><label>Escola</label><input name="school" placeholder="Nome da escola"></p>
          <p><label>Cidade</label><input name="city" placeholder="Cidade"></p>
        </div>
        <button class="btn primary big">Criar conta</button>
        <a class="btn" href="/login">Voltar</a>
      </form>
    </div>'''
    return render(content, "Cadastro")

def professor_dashboard_clean():
    u = user()
    recent = q("SELECT * FROM materials WHERE user_id=? ORDER BY id DESC LIMIT 6", (u["id"],))
    recent_html = ""
    for m in recent:
        recent_html += f'<a class="action" href="/professor/material/{m["id"]}"><b>{esc(m["type"])} - {esc(m["title"])}</b><span>{esc(m["created_at"])}</span></a>'
    if not recent_html:
        recent_html = '<p class="muted">Nenhum material gerado ainda.</p>'
    content = f'''
    <div class="hero">
      <div><span>AulaPronta Pro</span><h1>Estúdio do Professor</h1><p>Crie atividades, avaliações, planos de aula e pareceres. A administração fica em outro programa separado.</p></div>
      {professor_license_card(u)}
    </div>
    <div class="cards">
      <div class="card"><small>Questões</small><strong>{q("SELECT COUNT(*) c FROM questions", one=True)["c"]}</strong><p>banco pedagógico</p></div>
      <div class="card"><small>Conteúdos</small><strong>{q("SELECT COUNT(*) c FROM topics", one=True)["c"]}</strong><p>temas por turma</p></div>
      <div class="card"><small>Materiais</small><strong>{q("SELECT COUNT(*) c FROM materials WHERE user_id=?", (u["id"],), one=True)["c"]}</strong><p>gerados por você</p></div>
      <div class="card"><small>Licença</small><strong>{esc(u["plan"] or "Premium")}</strong><p>{esc(u["valid_until"] or "---")}</p></div>
    </div>
    <div class="layout-2">
      <div class="panel"><h2>Criar novo material</h2>
        <div class="action-grid">
          <a class="action" href="/professor/atividade"><b>Atividade Guiada</b><span>Folha do aluno e gabarito.</span></a>
          <a class="action" href="/professor/avaliacao"><b>Avaliação Completa</b><span>Prova com critérios.</span></a>
          <a class="action" href="/professor/plano"><b>Plano de Aula</b><span>Planejamento completo.</span></a>
          <a class="action" href="/professor/parecer"><b>Relatórios e Pareceres</b><span>Texto pedagógico pronto.</span></a>
        </div>
      </div>
      <div class="panel"><h2>Materiais recentes</h2>{recent_html}</div>
    </div>'''
    return render(content, "Início")

def assinatura_professor():
    u = user()
    d = v33_days_left(u["valid_until"])
    status = "Ativa"
    if d is not None and d < 0:
        status = "Expirada"
    elif d is not None and d <= 7:
        status = "Vencendo"
    cards = ""
    for key, p in PLANOS_PROFESSOR.items():
        cards += f'''<div class="card"><small>{p["label"]}</small><strong>R$ {p["amount"]}</strong><p>{p["days"]} dias de acesso</p><a class="btn primary" href="/comprar/{key}">Renovar</a></div>'''
    orders = q("SELECT * FROM payment_orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (u["id"],))
    order_html = ""
    for o in orders:
        order_html += f'''<div class="commercial-order"><div><b>Pedido #{o["id"]} - {esc(o["plan"])}</b><span>Valor: {esc(o["amount"])} - Status: {esc(o["status"])} - {esc(o["created_at"])}</span></div><a class="btn" href="/pagamento/{o["id"]}">Ver</a></div>'''
    if not order_html:
        order_html = '<p class="muted">Nenhum pedido de renovação criado ainda.</p>'
    content = f'''
    <div class="header"><div><span>Assinatura</span><h1>Minha licença</h1><p>Acompanhe sua validade e solicite renovação. A aprovação fica somente no Admin Center do dono.</p></div>{professor_license_card(u)}</div>
    <div class="cards">
      <div class="card"><small>Status</small><strong>{status}</strong><p>situação do acesso</p></div>
      <div class="card"><small>Plano</small><strong>{esc(u["plan"] or "Premium")}</strong><p>licença atual</p></div>
      <div class="card"><small>Validade</small><strong>{esc(u["valid_until"] or "---")}</strong><p>data final</p></div>
      <div class="card"><small>Dias</small><strong>{d if d is not None else "---"}</strong><p>restantes</p></div>
    </div>
    <div class="panel"><h2>Renovar plano</h2><div class="cards">{cards}</div></div>
    <div class="panel"><h2>Meus pedidos</h2>{order_html}</div>'''
    return render(content, "Minha licença")

def comprar_plano_professor(plan_key):
    u = user()
    if plan_key not in PLANOS_PROFESSOR:
        flash("Plano inválido.")
        return redirect("/assinatura")
    p = PLANOS_PROFESSOR[plan_key]
    ref = "AP-" + secrets.token_hex(4).upper()
    q("INSERT INTO payment_orders(user_id,plan,amount,days,status,pix_key,reference,created_at) VALUES(?,?,?,?,?,?,?,?)",
      (u["id"], p["label"], p["amount"], p["days"], "pendente", v33_pix_key(), ref, datetime.now().isoformat()))
    row = q("SELECT id FROM payment_orders WHERE reference=?", (ref,), True)
    flash("Pedido de renovação criado. Faça o Pix e envie o comprovante para o responsável.")
    return redirect(f"/pagamento/{row['id']}")

def pagamento_professor(order_id):
    u = user()
    o = q("SELECT * FROM payment_orders WHERE id=? AND user_id=?", (order_id, u["id"]), True)
    if not o:
        flash("Pedido não encontrado.")
        return redirect("/assinatura")
    msg = f"AulaPronta Pro | Pedido {o['reference']} | Plano {o['plan']} | Valor {o['amount']} | Email {u['email']}"
    content = f'''
    <div class="header"><div><span>Renovação</span><h1>Pedido #{o["id"]}</h1><p>Faça o pagamento e aguarde a liberação pelo responsável.</p></div></div>
    <div class="panel payment-box">
      <h2>Plano {esc(o["plan"])}</h2>
      <p><b>Valor:</b> R$ {esc(o["amount"])}</p>
      <p><b>Status:</b> {esc(o["status"])}</p>
      <p><b>Referência:</b> {esc(o["reference"])}</p>
      <p><label>Chave Pix</label><input readonly value="{esc(o["pix_key"])}"></p>
      <p><label>Mensagem para enviar junto com o comprovante</label><textarea readonly rows="3">{esc(msg)}</textarea></p>
      <p class="muted">O professor não aprova pagamento. A aprovação é feita no Admin Center separado.</p>
      <a class="btn" href="/assinatura">Voltar</a>
    </div>'''
    return render(content, "Pedido de renovação")

def trocar_senha_professor():
    u = user()
    if request.method == "POST":
        atual = request.form.get("atual", "")
        nova = request.form.get("nova", "")
        repetir = request.form.get("repetir", "")
        if not check_password_hash(u["password"], atual):
            flash("Senha atual incorreta.")
            return redirect("/trocar-senha")
        if len(nova) < 6 or nova != repetir:
            flash("Nova senha inválida ou não confere. Use pelo menos 6 caracteres.")
            return redirect("/trocar-senha")
        q("UPDATE users SET password=? WHERE id=?", (generate_password_hash(nova), u["id"]))
        flash("Senha alterada com sucesso.")
        return redirect("/professor")
    return render('''<div class="header"><div><span>Segurança</span><h1>Trocar senha</h1><p>Use uma senha forte para proteger sua conta.</p></div></div><div class="panel"><form method="post"><p><label>Senha atual</label><input type="password" name="atual"></p><p><label>Nova senha</label><input type="password" name="nova"></p><p><label>Repetir nova senha</label><input type="password" name="repetir"></p><button class="btn primary big">Alterar senha</button></form></div>''', "Trocar senha")

def admin_removed(*args, **kwargs):
    flash("Área administrativa removida do programa do professor. Use o Admin Center separado.")
    return redirect("/professor")

# Sobrescreve endpoints principais com versões corrigidas.
app.view_functions["login_page"] = professor_login_page
app.view_functions["cadastro"] = professor_cadastro
app.view_functions["dashboard"] = login_required(professor_dashboard_clean)
app.view_functions["assinatura"] = login_required(assinatura_professor)
if "comprar_plano" in app.view_functions:
    app.view_functions["comprar_plano"] = login_required(comprar_plano_professor)
if "pagamento_page" in app.view_functions:
    app.view_functions["pagamento_page"] = login_required(pagamento_professor)
if "trocar_senha" in app.view_functions:
    app.view_functions["trocar_senha"] = login_required(trocar_senha_professor)

for endpoint in list(app.view_functions.keys()):
    if endpoint.startswith("admin"):
        app.view_functions[endpoint] = login_required(admin_removed)
