
# ============================================================
# AulaPronta Pro v3.5 - Cadastro com plano TESTE
# Novos cadastros entram com prazo curto de teste.
# Padrão: 7 dias. Configure com TRIAL_DAYS no .env.
# ============================================================

import os
from datetime import datetime, timedelta
from flask import request, redirect, flash
from werkzeug.security import generate_password_hash

V35_VERSION = "v3.5-teste-7-dias"

def trial_days():
    try:
        return max(1, min(int(os.getenv("TRIAL_DAYS", "7")), 30))
    except Exception:
        return 7

def trial_valid_until():
    return (datetime.now() + timedelta(days=trial_days())).date().isoformat()

def ensure_demo_teacher_trial():
    try:
        demo = q("SELECT * FROM users WHERE email=?", ("professor@aulapronta.com",), True)
        if demo:
            q("UPDATE users SET plan=?, valid_until=? WHERE email=?", ("TESTE", trial_valid_until(), "professor@aulapronta.com"))
    except Exception:
        pass

ensure_demo_teacher_trial()

def professor_cadastro_v35():
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

        valid = trial_valid_until()
        q("INSERT INTO users(name,email,password,is_admin,plan,valid_until,school,city,state,avatar,teaching_style,local_context,default_instructions) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (request.form.get("name", "Professor(a)"), email, generate_password_hash(senha), 0, "TESTE", valid,
           request.form.get("school", ""), request.form.get("city", ""), request.form.get("state", "")[:2], "",
           "Acolhedor e simples", "", ""))

        flash(f"Conta criada com sucesso. Você recebeu {trial_days()} dias de teste.")
        return redirect("/login")

    content = f'''
    <div class="auth-card login-card-v34 cadastro-card-v34">
      <div class="login-mini-brand">
        <div class="auth-logo">AP</div>
        <div><b>Criar conta</b><span>Teste grátis de {trial_days()} dias</span></div>
      </div>
      <h1>Criar conta de professor</h1>
      <p class="sub">O cadastro libera um plano TESTE por {trial_days()} dias. Depois, a renovação pode ser feita pela área Minha assinatura.</p>
      {{% with msgs = get_flashed_messages() %}}{{% for m in msgs %}}<div class="msg">{{{{m}}}}</div>{{% endfor %}}{{% endwith %}}
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
          <span>Validade automática: {trial_days()} dias após o cadastro.</span>
        </div>
        <div class="action-row">
          <button class="btn primary big">Criar conta de teste</button>
          <a class="btn" href="/login">Voltar ao login</a>
        </div>
      </form>
    </div>'''
    return render(content, "Cadastro")

app.view_functions["cadastro"] = professor_cadastro_v35
