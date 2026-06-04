
# ============================================================
# AulaPronta Pro v3.6 - Login/Cadastro corrigidos
# Remove código Jinja aparecendo na tela e separa melhor
# os textos do login e do cadastro.
# ============================================================

from flask import request, redirect, flash, session, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

V36_VERSION = "v3.6-login-cadastro-corrigido"

def v36_flash_html():
    msgs = get_flashed_messages()
    if not msgs:
        return ""
    return "".join([f'<div class="msg">{esc(m)}</div>' for m in msgs])

def v36_trial_days():
    try:
        return max(1, min(int(os.getenv("TRIAL_DAYS", "7")), 30))
    except Exception:
        return 7

def v36_trial_valid_until():
    return (datetime.now() + timedelta(days=v36_trial_days())).date().isoformat()

def professor_login_page_v36():
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

    msgs = v36_flash_html()
    content = f'''
    <div class="auth-card login-card-v34">
      <div class="login-mini-brand">
        <div class="auth-logo">AP</div>
        <div><b>AulaPronta Pro</b><span>Professor Studio</span></div>
      </div>

      <h1>Entrar no painel do professor</h1>
      <p class="sub">Acesse sua área para criar atividades, avaliações, planos de aula e pareceres prontos para imprimir.</p>

      {msgs}

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

def professor_cadastro_v36():
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

        valid = v36_trial_valid_until()
        q("INSERT INTO users(name,email,password,is_admin,plan,valid_until,school,city,state,avatar,teaching_style,local_context,default_instructions) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (request.form.get("name", "Professor(a)"), email, generate_password_hash(senha), 0, "TESTE", valid,
           request.form.get("school", ""), request.form.get("city", ""), request.form.get("state", "")[:2], "",
           "Acolhedor e simples", "", ""))

        flash(f"Conta criada com sucesso. Você recebeu {v36_trial_days()} dias de teste.")
        return redirect("/login")

    msgs = v36_flash_html()
    dias = v36_trial_days()
    content = f'''
    <div class="auth-card login-card-v34 cadastro-card-v34">
      <div class="login-mini-brand">
        <div class="auth-logo">AP</div>
        <div><b>Cadastro do professor</b><span>Teste grátis de {dias} dias</span></div>
      </div>

      <h1>Criar conta de professor</h1>
      <p class="sub">Preencha os dados abaixo. A conta começa no plano TESTE por {dias} dias e depois pode ser renovada.</p>

      {msgs}

      <form method="post">
        <div class="auth-grid cadastro-grid-v34">
          <p><label>Nome do professor</label><input name="name" placeholder="Seu nome"></p>
          <p><label>E-mail</label><input name="email" placeholder="professor@escola.com"></p>
          <p><label>Senha</label><input type="password" name="password"></p>
          <p><label>Confirmar senha</label><input type="password" name="password2"></p>
          <p><label>Escola</label><input name="school" placeholder="Nome da escola"></p>
          <p><label>Cidade</label><input name="city" placeholder="Cidade"></p>
        </div>

        <div class="trial-box-v35">
          <b>Plano inicial: TESTE</b>
          <span>Validade automática: {dias} dias após o cadastro.</span>
        </div>

        <div class="action-row">
          <button class="btn primary big">Criar conta de teste</button>
          <a class="btn" href="/login">Voltar ao login</a>
        </div>
      </form>
    </div>'''
    return render(content, "Cadastro")

app.view_functions["login_page"] = professor_login_page_v36
app.view_functions["cadastro"] = professor_cadastro_v36
