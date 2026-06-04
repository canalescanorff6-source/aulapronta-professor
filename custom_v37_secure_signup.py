
# ============================================================
# AulaPronta Pro v3.7 - Cadastro seguro
# Proteções:
# - limite de contas por IP por dia
# - bloqueio de e-mail temporário
# - cadastro público ligável/desligável
# - convite opcional
# - verificação por e-mail opcional
# - aprovação admin opcional
# - bloqueio/desbloqueio pelo Admin Center
# ============================================================

import os, secrets, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, date
from flask import request, redirect, flash, session, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash

V37_VERSION = "v3.7-cadastro-seguro"

TEMP_EMAIL_DOMAINS = {
    "10minutemail.com","10minutemail.net","tempmail.com","temp-mail.org","guerrillamail.com",
    "guerrillamail.net","mailinator.com","yopmail.com","yopmail.fr","trashmail.com",
    "fakeinbox.com","getnada.com","sharklasers.com","dispostable.com","moakt.com",
    "emailondeck.com","throwawaymail.com","maildrop.cc","mintemail.com","tempmailo.com"
}

def v37_column_exists(table, col):
    try:
        with conn() as c:
            rows = c.execute(f"PRAGMA table_info({table})").fetchall()
            return any(r[1] == col for r in rows)
    except Exception:
        return False

def v37_setup():
    try:
        with conn() as c:
            for col, ddl in [
                ("is_active", "INTEGER DEFAULT 1"),
                ("approved", "INTEGER DEFAULT 1"),
                ("email_verified", "INTEGER DEFAULT 1"),
                ("created_ip", "TEXT DEFAULT ''"),
                ("created_user_agent", "TEXT DEFAULT ''"),
            ]:
                if not v37_column_exists("users", col):
                    c.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")

            c.execute('''CREATE TABLE IF NOT EXISTS signup_attempts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                email TEXT,
                user_agent TEXT,
                status TEXT,
                reason TEXT,
                created_at TEXT,
                day TEXT
            )''')

            c.execute('''CREATE TABLE IF NOT EXISTS email_verifications(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT,
                code TEXT,
                expires_at TEXT,
                used INTEGER DEFAULT 0,
                created_at TEXT
            )''')

            c.execute('''CREATE TABLE IF NOT EXISTS invite_codes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                plan TEXT DEFAULT 'TESTE',
                days INTEGER DEFAULT 7,
                active INTEGER DEFAULT 1,
                used INTEGER DEFAULT 0,
                used_by INTEGER DEFAULT 0,
                created_at TEXT,
                used_at TEXT DEFAULT ''
            )''')

            c.execute('''CREATE TABLE IF NOT EXISTS app_settings(
                key TEXT PRIMARY KEY,
                value TEXT
            )''')

            defaults = {
                "registration_open": os.getenv("REGISTRATION_OPEN", "1"),
                "signup_limit_per_ip": os.getenv("SIGNUP_LIMIT_PER_IP", "3"),
                "block_temp_emails": os.getenv("BLOCK_TEMP_EMAILS", "1"),
                "require_invite_code": os.getenv("REQUIRE_INVITE_CODE", "0"),
                "require_email_verification": os.getenv("REQUIRE_EMAIL_VERIFICATION", "0"),
                "require_admin_approval": os.getenv("REQUIRE_ADMIN_APPROVAL", "0"),
                "trial_days": os.getenv("TRIAL_DAYS", "7"),
            }
            for k, v in defaults.items():
                c.execute("INSERT OR IGNORE INTO app_settings(key,value) VALUES(?,?)", (k, v))
            c.commit()
    except Exception:
        pass

v37_setup()

def v37_setting(key, default=""):
    env_map = {
        "registration_open": "REGISTRATION_OPEN",
        "signup_limit_per_ip": "SIGNUP_LIMIT_PER_IP",
        "block_temp_emails": "BLOCK_TEMP_EMAILS",
        "require_invite_code": "REQUIRE_INVITE_CODE",
        "require_email_verification": "REQUIRE_EMAIL_VERIFICATION",
        "require_admin_approval": "REQUIRE_ADMIN_APPROVAL",
        "trial_days": "TRIAL_DAYS",
    }
    if env_map.get(key) and os.getenv(env_map[key]) is not None:
        return os.getenv(env_map[key])
    try:
        row = q("SELECT value FROM app_settings WHERE key=?", (key,), True)
        return row["value"] if row else default
    except Exception:
        return default

def v37_bool(key, default="0"):
    return str(v37_setting(key, default)).lower() in ("1","true","sim","yes","on")

def v37_int(key, default=0):
    try:
        return int(v37_setting(key, str(default)))
    except Exception:
        return default

def v37_client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "local"

def v37_user_agent():
    return (request.headers.get("User-Agent") or "")[:500]

def v37_log_signup(email, status, reason=""):
    try:
        ip = v37_client_ip()
        q('''INSERT INTO signup_attempts(ip,email,user_agent,status,reason,created_at,day)
             VALUES(?,?,?,?,?,?,?)''',
          (ip, email, v37_user_agent(), status, reason, datetime.now().isoformat(), date.today().isoformat()))
    except Exception:
        pass

def v37_email_domain(email):
    return email.split("@")[-1].lower().strip() if "@" in email else ""

def v37_is_temp_email(email):
    domain = v37_email_domain(email)
    if not domain:
        return True
    if domain in TEMP_EMAIL_DOMAINS:
        return True
    for d in TEMP_EMAIL_DOMAINS:
        if domain.endswith("." + d):
            return True
    return False

def v37_ip_signup_count_today(ip):
    try:
        row = q('''SELECT COUNT(*) c FROM signup_attempts
                   WHERE ip=? AND day=? AND status IN ('created','pending','verified')''',
                (ip, date.today().isoformat()), True)
        return row["c"] if row else 0
    except Exception:
        return 0

def v37_trial_days():
    return max(1, min(v37_int("trial_days", 7), 30))

def v37_trial_valid_until(days=None):
    days = days or v37_trial_days()
    return (datetime.now() + timedelta(days=int(days))).date().isoformat()

def v37_flash_html():
    msgs = get_flashed_messages()
    return "".join([f'<div class="msg">{esc(m)}</div>' for m in msgs]) if msgs else ""

def v37_smtp_configured():
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"))

def v37_send_email(to, subject, body):
    if not v37_smtp_configured():
        return False
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user_smtp = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM", user_smtp)

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(user_smtp, password)
        smtp.send_message(msg)
    return True

def v37_create_verification(user_id, email):
    code = f"{secrets.randbelow(1000000):06d}"
    expires = (datetime.now() + timedelta(minutes=30)).isoformat()
    q('''INSERT INTO email_verifications(user_id,email,code,expires_at,used,created_at)
         VALUES(?,?,?,?,?,?)''', (user_id, email, code, expires, 0, datetime.now().isoformat()))
    sent = False
    try:
        sent = v37_send_email(
            email,
            "Código de verificação - AulaPronta Pro",
            f"Seu código de verificação do AulaPronta Pro é: {code}\n\nEle expira em 30 minutos."
        )
    except Exception:
        sent = False
    return code, sent

def v37_valid_invite(code):
    if not code:
        return None
    return q("SELECT * FROM invite_codes WHERE code=? AND active=1 AND used=0", (code.strip().upper(),), True)

def v37_mark_invite_used(code, user_id):
    if not code:
        return
    q("UPDATE invite_codes SET used=1, used_by=?, used_at=? WHERE code=?",
      (user_id, datetime.now().isoformat(), code.strip().upper()))

def professor_login_page_v37():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        if is_locked(email):
            flash("Muitas tentativas incorretas. Aguarde alguns minutos.")
            return redirect("/login")

        u = q("SELECT * FROM users WHERE email=?", (email,), True)
        if u and check_password_hash(u["password"], request.form.get("password", "")):
            if v37_column_exists("users", "is_active") and int(u["is_active"] or 0) != 1:
                flash("Sua conta está bloqueada. Fale com o suporte.")
                return redirect("/login")
            if v37_column_exists("users", "approved") and int(u["approved"] or 0) != 1:
                flash("Sua conta ainda aguarda aprovação.")
                return redirect("/login")
            if v37_column_exists("users", "email_verified") and int(u["email_verified"] or 0) != 1:
                flash("Confirme seu e-mail para acessar.")
                return redirect(f"/verificar-email?email={email}")

            clear_failed(email)
            session["uid"] = u["id"]
            return redirect("/professor")

        record_failed(email)
        flash("E-mail ou senha inválidos.")

    content = f'''
    <div class="auth-card login-card-v34">
      <div class="login-mini-brand"><div class="auth-logo">AP</div><div><b>AulaPronta Pro</b><span>Professor Studio</span></div></div>
      <h1>Entrar no painel do professor</h1>
      <p class="sub">Acesse sua área para criar atividades, avaliações, planos de aula e pareceres prontos para imprimir.</p>
      {v37_flash_html()}
      <form method="post" class="login-form-v34">
        <p><label>E-mail</label><input name="email" placeholder="professor@escola.com" autocomplete="email"></p>
        <p><label>Senha</label><input name="password" type="password" placeholder="Digite sua senha" autocomplete="current-password"></p>
        <button class="btn primary big">Entrar no sistema</button>
      </form>
      <div class="login-links-v34">
        <a class="link" href="/cadastro">Criar conta de professor</a>
        <a class="link" href="/termos">Termos de uso</a>
      </div>
      <div class="login-demo-v34"><b>Login de demonstração</b><span>professor@aulapronta.com • professor123</span></div>
    </div>'''
    return render(content, "Login")

def professor_cadastro_v37():
    require_invite = v37_bool("require_invite_code", "0")
    require_verify = v37_bool("require_email_verification", "0")
    require_approval = v37_bool("require_admin_approval", "0")
    dias = v37_trial_days()
    limit = v37_int("signup_limit_per_ip", 3)

    if request.method == "POST":
        ip = v37_client_ip()
        email = request.form.get("email", "").lower().strip()
        senha = request.form.get("password", "")
        senha2 = request.form.get("password2", "")
        invite_code = request.form.get("invite_code", "").strip().upper()

        if not v37_bool("registration_open", "1"):
            v37_log_signup(email, "blocked", "registration_closed")
            flash("O cadastro público está fechado no momento.")
            return redirect("/cadastro")

        if limit > 0 and v37_ip_signup_count_today(ip) >= limit:
            v37_log_signup(email, "blocked", "ip_limit")
            flash("Limite de cadastro atingido neste IP. Tente novamente amanhã.")
            return redirect("/cadastro")

        if not email or "@" not in email:
            v37_log_signup(email, "blocked", "invalid_email")
            flash("Informe um e-mail válido.")
            return redirect("/cadastro")

        if v37_bool("block_temp_emails", "1") and v37_is_temp_email(email):
            v37_log_signup(email, "blocked", "temp_email")
            flash("Use um e-mail verdadeiro da escola ou pessoal. E-mails temporários não são aceitos.")
            return redirect("/cadastro")

        if len(senha) < 6 or senha != senha2:
            v37_log_signup(email, "blocked", "invalid_password")
            flash("A senha precisa ter pelo menos 6 caracteres e confirmar corretamente.")
            return redirect("/cadastro")

        if q("SELECT id FROM users WHERE email=?", (email,), True):
            v37_log_signup(email, "blocked", "duplicated_email")
            flash("Já existe uma conta com este e-mail.")
            return redirect("/cadastro")

        invite = None
        plan = "TESTE"
        days = dias
        if require_invite:
            invite = v37_valid_invite(invite_code)
            if not invite:
                v37_log_signup(email, "blocked", "invalid_invite")
                flash("Código de convite inválido ou já utilizado.")
                return redirect("/cadastro")
            plan = invite["plan"] or "TESTE"
            days = int(invite["days"] or dias)

        approved = 0 if require_approval else 1
        email_verified = 0 if require_verify else 1
        valid = v37_trial_valid_until(days)

        q('''INSERT INTO users(name,email,password,is_admin,plan,valid_until,school,city,state,avatar,teaching_style,local_context,default_instructions,is_active,approved,email_verified,created_ip,created_user_agent)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (request.form.get("name", "Professor(a)"), email, generate_password_hash(senha), 0, plan, valid,
             request.form.get("school", ""), request.form.get("city", ""), request.form.get("state", "")[:2], "",
             "Acolhedor e simples", "", "", 1, approved, email_verified, ip, v37_user_agent()))

        u = q("SELECT id FROM users WHERE email=?", (email,), True)
        uid = u["id"] if u else 0

        if invite:
            v37_mark_invite_used(invite_code, uid)

        if require_verify:
            code, sent = v37_create_verification(uid, email)
            v37_log_signup(email, "pending", "email_verification")
            if sent:
                flash("Conta criada. Enviamos um código para seu e-mail.")
            else:
                flash(f"Conta criada. Código de verificação: {code}")
            return redirect(f"/verificar-email?email={email}")

        if require_approval:
            v37_log_signup(email, "pending", "admin_approval")
            flash("Conta criada. Aguarde aprovação do administrador.")
            return redirect("/login")

        v37_log_signup(email, "created", "ok")
        flash(f"Conta criada com sucesso. Você recebeu {days} dias de teste.")
        return redirect("/login")

    invite_field = '''
      <p><label>Código de convite</label><input name="invite_code" placeholder="Ex: AP-AB12-CD34"></p>
    ''' if require_invite else ""

    security_note = "Cadastro protegido por limite de IP e bloqueio de e-mails temporários."
    if require_invite:
        security_note += " É necessário código de convite."
    if require_approval:
        security_note += " A conta precisa de aprovação."
    if require_verify:
        security_note += " O e-mail precisa ser verificado."

    content = f'''
    <div class="auth-card login-card-v34 cadastro-card-v34">
      <div class="login-mini-brand"><div class="auth-logo">AP</div><div><b>Cadastro do professor</b><span>Teste grátis de {dias} dias</span></div></div>
      <h1>Criar conta de professor</h1>
      <p class="sub">A conta começa no plano TESTE por {dias} dias. {security_note}</p>
      {v37_flash_html()}
      <form method="post">
        <div class="auth-grid cadastro-grid-v34">
          <p><label>Nome do professor</label><input name="name" placeholder="Seu nome"></p>
          <p><label>E-mail</label><input name="email" placeholder="professor@escola.com"></p>
          <p><label>Senha</label><input type="password" name="password"></p>
          <p><label>Confirmar senha</label><input type="password" name="password2"></p>
          <p><label>Escola</label><input name="school" placeholder="Nome da escola"></p>
          <p><label>Cidade</label><input name="city" placeholder="Cidade"></p>
          {invite_field}
        </div>
        <div class="trial-box-v35"><b>Plano inicial: TESTE</b><span>Validade automática: {dias} dias após o cadastro.</span></div>
        <div class="action-row">
          <button class="btn primary big">Criar conta de teste</button>
          <a class="btn" href="/login">Voltar ao login</a>
        </div>
      </form>
    </div>'''
    return render(content, "Cadastro")

def verificar_email():
    email = request.args.get("email", request.form.get("email", "")).lower().strip()
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        row = q('''SELECT * FROM email_verifications
                   WHERE email=? AND code=? AND used=0
                   ORDER BY id DESC LIMIT 1''', (email, code), True)
        if not row:
            flash("Código inválido.")
            return redirect(f"/verificar-email?email={email}")
        try:
            if datetime.fromisoformat(row["expires_at"]) < datetime.now():
                flash("Código expirado. Peça um novo cadastro ou fale com o suporte.")
                return redirect(f"/verificar-email?email={email}")
        except Exception:
            pass
        q("UPDATE email_verifications SET used=1 WHERE id=?", (row["id"],))
        q("UPDATE users SET email_verified=1 WHERE id=?", (row["user_id"],))
        v37_log_signup(email, "verified", "email_ok")
        flash("E-mail verificado. Agora você pode entrar.")
        return redirect("/login")

    content = f'''
    <div class="auth-card login-card-v34">
      <div class="login-mini-brand"><div class="auth-logo">AP</div><div><b>Verificar e-mail</b><span>Segurança da conta</span></div></div>
      <h1>Confirme seu e-mail</h1>
      <p class="sub">Digite o código enviado para <b>{esc(email)}</b>.</p>
      {v37_flash_html()}
      <form method="post">
        <input type="hidden" name="email" value="{esc(email)}">
        <p><label>Código de verificação</label><input name="code" placeholder="000000"></p>
        <button class="btn primary big">Verificar e-mail</button>
      </form>
      <div class="login-links-v34"><a class="link" href="/login">Voltar ao login</a></div>
    </div>'''
    return render(content, "Verificar e-mail")

app.view_functions["login_page"] = professor_login_page_v37
app.view_functions["cadastro"] = professor_cadastro_v37
try:
    app.add_url_rule("/verificar-email", "verificar_email", verificar_email, methods=["GET","POST"])
except Exception:
    pass
