
# ============================================================
# AulaPronta Pro v3.1 - Professor Edition sem área admin
# Remove telas/admin/pagamentos de aprovação e deixa o sistema
# focado no uso do professor.
# ============================================================

import re
from datetime import datetime, timedelta
from flask import request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

PROFESSOR_VERSION = "v3.1-professor-sem-admin"

def professor_days_left(value):
    try:
        return (datetime.fromisoformat(value).date() - datetime.now().date()).days
    except Exception:
        return None

def professor_license_card(u):
    d = professor_days_left(u["valid_until"]) if u else None
    if d is None:
        msg = "validade não definida"
        cls = "license-good"
    elif d < 0:
        msg = "licença expirada"
        cls = "license-expired"
    elif d <= 7:
        msg = f"vence em {d} dia(s)"
        cls = "license-soon"
    else:
        msg = f"{d} dia(s) restantes"
        cls = "license-good"
    return f'<div class="final-license {cls}"><b>{esc(u["plan"] or "Premium")}</b><span>Válido até {esc(u["valid_until"] or "---")} - {msg}</span></div>'

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

# Limpa links administrativos do menu lateral.
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
        valid = (datetime.now() + timedelta(days=365)).date().isoformat()
        q("INSERT INTO users(name,email,password,is_admin,plan,valid_until,school,city,state,avatar,teaching_style,local_context,default_instructions) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (request.form.get("name", "Professor(a)"), email, generate_password_hash(senha), 0, "PREMIUM", valid,
           request.form.get("school", ""), request.form.get("city", ""), request.form.get("state", "")[:2], "",
           "Acolhedor e simples", "", ""))
        flash("Conta criada com sucesso. Faça login para entrar.")
        return redirect("/login")
    content = '''
    <div class="auth-card wide">
      <div class="auth-logo">AP</div>
      <h1>Criar conta de professor</h1>
      <p class="sub">Cadastro simples, sem serial e sem painel administrativo.</p>
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

def professor_assinatura():
    u = user()
    d = professor_days_left(u["valid_until"])
    status = "Ativa"
    if d is not None and d < 0:
        status = "Expirada"
    elif d is not None and d <= 7:
        status = "Vencendo"
    content = f'''
    <div class="header">
      <div><span>Assinatura</span><h1>Minha licença</h1><p>Área simples para o professor acompanhar validade e plano. Sem aprovação de pagamento e sem painel administrativo.</p></div>
      {professor_license_card(u)}
    </div>
    <div class="cards">
      <div class="card"><small>Status</small><strong>{status}</strong><p>situação do acesso</p></div>
      <div class="card"><small>Plano</small><strong>{esc(u["plan"] or "Premium")}</strong><p>licença atual</p></div>
      <div class="card"><small>Validade</small><strong>{esc(u["valid_until"] or "---")}</strong><p>data final</p></div>
      <div class="card"><small>Dias</small><strong>{d if d is not None else "---"}</strong><p>restantes</p></div>
    </div>
    <div class="panel">
      <h2>Observação</h2>
      <p>Esta edição foi limpa para uso do professor. Recursos de aprovação de pagamento, seriais administrativos e telas de gestão foram removidos do menu e bloqueados.</p>
    </div>'''
    return render(content, "Minha licença")

def admin_removed(*args, **kwargs):
    flash("Área administrativa removida nesta edição. O sistema agora é focado no professor.")
    return redirect("/professor")

def comprar_removed(*args, **kwargs):
    flash("Pagamento/aprovação administrativa removidos nesta edição.")
    return redirect("/assinatura")

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
      <div><span>AulaPronta Pro</span><h1>Estúdio do Professor</h1><p>Crie atividades, avaliações, planos de aula e pareceres sem área administrativa aparecendo para o professor.</p></div>
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

# Sobrescreve telas principais
app.view_functions["login_page"] = professor_login_page
app.view_functions["cadastro"] = professor_cadastro
app.view_functions["dashboard"] = login_required(professor_dashboard_clean)

# Assinatura sem pagamento/admin
if "assinatura" in app.view_functions:
    app.view_functions["assinatura"] = login_required(professor_assinatura)
else:
    app.add_url_rule("/assinatura", "assinatura", login_required(professor_assinatura))

# Bloqueia compras/pagamentos/admin
for endpoint in list(app.view_functions.keys()):
    if endpoint.startswith("admin"):
        app.view_functions[endpoint] = login_required(admin_removed)

for endpoint in ["comprar_plano", "pagamento_page"]:
    if endpoint in app.view_functions:
        app.view_functions[endpoint] = login_required(comprar_removed)
