
# ============================================================
# AulaPronta Pro v3.4 - Login premium + preparo RunSite/EXE/APK
# Corrige render sem usuário e melhora a tela inicial do professor.
# ============================================================

from flask import render_template_string, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

V34_VERSION = "v3.4-login-runsite-exe-apk"

def v34_initials(u):
    if not u:
        return "AP"
    name = str(u["name"] or "Professor").strip()
    parts = [p for p in name.split() if p]
    if not parts:
        return "AP"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def render(content, title="AulaPronta Pro"):
    u = user()
    meta = v33_license_meta(u) if "v33_license_meta" in globals() else {"plan":"Visitante","date":"---","days":"","status":"license-good"}
    return render_template_string(BASE_HTML, content=content, title=title, u=u, license=meta, initials=v34_initials(u), app_version=V34_VERSION)

try:
    BASE_HTML = BASE_HTML.replace("AulaPronta Pro • Plataforma premium para professores", "AulaPronta Pro • Estúdio do Professor")
    BASE_HTML = BASE_HTML.replace("Um visual mais profissional para vender como assinatura.", "Sua aula pronta em poucos minutos.")
    BASE_HTML = BASE_HTML.replace("Crie atividades, avaliações, planos e pareceres com identidade visual premium, banco pedagógico robusto, exportação prática e experiência pronta para desktop e Android.", "Crie atividades, avaliações, planos de aula e pareceres com banco pedagógico, exportação em PDF/Word e acesso preparado para computador e celular.")
    BASE_HTML = BASE_HTML.replace("<div class=\"auth-tile\"><b>Banco local</b><span>Conteúdos por turma e disciplina</span></div>", "<div class=\"auth-tile\"><b>Banco pedagógico</b><span>Conteúdos por turma e disciplina</span></div>")
    BASE_HTML = BASE_HTML.replace("<div class=\"auth-tile\"><b>PWA</b><span>Pronto para experiência mobile</span></div>", "<div class=\"auth-tile\"><b>Mobile</b><span>Pronto para Android/WebView</span></div>")
    BASE_HTML = BASE_HTML.replace("<div class=\"auth-tile\"><b>Premium</b><span>Visual escuro elegante</span></div>", "<div class=\"auth-tile\"><b>Exportação</b><span>PDF e Word para imprimir</span></div>")
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
    <div class="auth-card login-card-v34">
      <div class="login-mini-brand">
        <div class="auth-logo">AP</div>
        <div><b>AulaPronta Pro</b><span>Professor Studio</span></div>
      </div>
      <h1>Entrar no painel do professor</h1>
      <p class="sub">Crie atividades, avaliações, planos de aula e pareceres prontos para imprimir.</p>
      {% with msgs = get_flashed_messages() %}{% for m in msgs %}<div class="msg">{{m}}</div>{% endfor %}{% endwith %}
      <form method="post" class="login-form-v34">
        <p><label>E-mail</label><input name="email" placeholder="professor@escola.com" autocomplete="email"></p>
        <p><label>Senha</label><input name="password" type="password" placeholder="Digite sua senha" autocomplete="current-password"></p>
        <button class="btn primary big">Entrar no sistema</button>
      </form>
      <div class="login-links-v34">
        <a class="link" href="/cadastro">Criar conta de professor</a>
        <a class="link" href="/termos">Termos de uso</a>
      </div>
      <div class="login-demo-v34">
        <b>Login de demonstração</b>
        <span>professor@aulapronta.com • professor123</span>
      </div>
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
    <div class="auth-card login-card-v34 cadastro-card-v34">
      <div class="login-mini-brand">
        <div class="auth-logo">AP</div>
        <div><b>Criar conta</b><span>Acesso do professor</span></div>
      </div>
      <h1>Criar conta de professor</h1>
      <p class="sub">Preencha seus dados para personalizar os materiais com sua escola e seu nome.</p>
      {% with msgs = get_flashed_messages() %}{% for m in msgs %}<div class="msg">{{m}}</div>{% endfor %}{% endwith %}
      <form method="post">
        <div class="auth-grid cadastro-grid-v34">
          <p><label>Nome do professor</label><input name="name" placeholder="Seu nome"></p>
          <p><label>E-mail</label><input name="email" placeholder="professor@escola.com"></p>
          <p><label>Senha</label><input type="password" name="password"></p>
          <p><label>Confirmar senha</label><input type="password" name="password2"></p>
          <p><label>Escola</label><input name="school" placeholder="Nome da escola"></p>
          <p><label>Cidade</label><input name="city" placeholder="Cidade"></p>
        </div>
        <div class="action-row">
          <button class="btn primary big">Criar conta</button>
          <a class="btn" href="/login">Voltar ao login</a>
        </div>
      </form>
    </div>'''
    return render(content, "Cadastro")

app.view_functions["login_page"] = professor_login_page
app.view_functions["cadastro"] = professor_cadastro
