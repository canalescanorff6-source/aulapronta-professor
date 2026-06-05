
# ============================================================
# AulaPronta Pro v4.1 - Checkup profissional de nomes e textos
# Remove termos de teste/demonstração da interface do professor.
# Mantém o app online compatível com o APK WebView.
# ============================================================

import os
from datetime import datetime, timedelta
from flask import request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

V410_VERSION = "v4.1-profissional"

def v410_plan_label(plan):
    p = (plan or "").strip().upper()
    labels = {
        "TESTE": "Avaliação gratuita",
        "AVALIACAO": "Avaliação gratuita",
        "AVALIAÇÃO": "Avaliação gratuita",
        "AVALIACAO_GRATUITA": "Avaliação gratuita",
        "AVALIAÇÃO GRATUITA": "Avaliação gratuita",
        "PROFESSOR": "Profissional",
        "PROFISSIONAL": "Profissional",
        "PREMIUM": "Premium",
        "ESCOLA": "Escola",
        "MENSAL": "Mensal",
        "SEMESTRAL": "Semestral",
        "ANUAL": "Anual",
    }
    return labels.get(p, plan or "Profissional")

def v410_status_label(status):
    s = (status or "").strip().lower()
    labels = {
        "pendente": "Aguardando pagamento",
        "comprovante_enviado": "Comprovante enviado para análise",
        "aprovado": "Aprovado",
        "recusado": "Recusado",
        "cancelado": "Cancelado",
        "created": "Criado",
        "pending": "Em análise",
        "verified": "Verificado",
        "blocked": "Bloqueado",
    }
    return labels.get(s, status or "Em análise")

def v410_days_left(value):
    try:
        return (datetime.fromisoformat(value).date() - datetime.now().date()).days
    except Exception:
        return None

def v410_trial_days():
    try:
        return v37_trial_days()
    except Exception:
        try:
            return int(os.getenv("TRIAL_DAYS", "7"))
        except Exception:
            return 7

def v410_bool_setting(key, default="0"):
    try:
        return v37_bool(key, default)
    except Exception:
        return str(os.getenv(key.upper(), default)).lower() in ("1","true","sim","yes","on")

def v410_int_setting(key, default=0):
    try:
        return v37_int(key, default)
    except Exception:
        try:
            return int(os.getenv(key.upper(), str(default)))
        except Exception:
            return default

def v410_flash_html():
    try:
        return v37_flash_html()
    except Exception:
        return ""

def v410_db_cleanup():
    try:
        q("UPDATE users SET plan=? WHERE plan=?", ("AVALIACAO_GRATUITA", "TESTE"))
        q("UPDATE users SET name=? WHERE name=?", ("Professor AulaPronta", "Professor Demonstração"))
        q("UPDATE users SET school=? WHERE school=?", ("Escola Modelo", "Minha Escola"))
        q("UPDATE serials SET plan=? WHERE plan=?", ("AVALIACAO_GRATUITA", "TESTE"))
        q("UPDATE invite_codes SET plan=? WHERE plan=?", ("AVALIACAO_GRATUITA", "TESTE"))
    except Exception:
        pass

v410_db_cleanup()

try:
    BASE_HTML = BASE_HTML.replace("Pro Web v2.3", "Professor")
    BASE_HTML = BASE_HTML.replace("MENU", "Menu")
    BASE_HTML = BASE_HTML.replace("Criar Atividade", "Atividades")
    BASE_HTML = BASE_HTML.replace("Criar Avaliação", "Avaliações")
    BASE_HTML = BASE_HTML.replace("Planejar Aula", "Planos de Aula")
    BASE_HTML = BASE_HTML.replace("Pareceres", "Relatórios")
    BASE_HTML = BASE_HTML.replace("Materiais", "Meus Materiais")
    BASE_HTML = BASE_HTML.replace("Minha Escola", "Perfil e Escola")
    BASE_HTML = BASE_HTML.replace("Plano {{u.plan}} • até {{u.valid_until}}", "Acesso até {{u.valid_until}}")
    BASE_HTML = BASE_HTML.replace("Plano {{u.plan}}", "Acesso")
except Exception:
    pass

def v410_license_card(u):
    d = v410_days_left(u["valid_until"]) if u else None
    plan = v410_plan_label(u["plan"] if u else "")
    if d is None:
        msg, cls = "validade em conferência", "license-good"
    elif d < 0:
        msg, cls = "assinatura expirada", "license-expired"
    elif d <= 7:
        msg, cls = f"vence em {d} dia(s)", "license-soon"
    else:
        msg, cls = f"{d} dia(s) restantes", "license-good"
    return f'<div class="final-license {cls}"><b>{esc(plan)}</b><span>Válido até {esc(u["valid_until"] or "---")} - {esc(msg)}</span></div>'

def professor_login_page_v410():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        if is_locked(email):
            flash("Muitas tentativas incorretas. Aguarde alguns minutos.")
            return redirect("/login")

        u = q("SELECT * FROM users WHERE email=?", (email,), True)
        if u and check_password_hash(u["password"], request.form.get("password", "")):
            try:
                if "is_active" in u.keys() and int(u["is_active"] or 0) != 1:
                    flash("Sua conta está temporariamente bloqueada. Fale com o suporte.")
                    return redirect("/login")
                if "approved" in u.keys() and int(u["approved"] or 0) != 1:
                    flash("Sua conta está em análise. Aguarde a liberação.")
                    return redirect("/login")
                if "email_verified" in u.keys() and int(u["email_verified"] or 0) != 1:
                    flash("Confirme seu e-mail para acessar.")
                    return redirect(f"/verificar-email?email={email}")
            except Exception:
                pass
            clear_failed(email)
            session["uid"] = u["id"]
            return redirect("/professor")

        record_failed(email)
        flash("E-mail ou senha inválidos.")

    content = f'''
    <div class="auth-card login-card-v34 professional-login-v410">
      <div class="login-mini-brand">
        <div class="auth-logo">AP</div>
        <div><b>AulaPronta Pro</b><span>Estúdio do Professor</span></div>
      </div>
      <h1>Entrar no AulaPronta Pro</h1>
      <p class="sub">Acesse sua área para criar atividades, avaliações, planos de aula, relatórios e materiais alinhados à BNCC.</p>
      {v410_flash_html()}
      <form method="post" class="login-form-v34">
        <p><label>E-mail</label><input name="email" placeholder="seuemail@escola.com" autocomplete="email"></p>
        <p><label>Senha</label><input name="password" type="password" placeholder="Digite sua senha" autocomplete="current-password"></p>
        <button class="btn primary big">Entrar</button>
      </form>
      <div class="login-links-v34">
        <a class="link" href="/cadastro">Criar minha conta</a>
        <a class="link" href="/termos">Termos de uso</a>
      </div>
      <div class="professional-note-v410">
        Plataforma exclusiva para professores com acesso individual e renovação segura.
      </div>
    </div>'''
    return render(content, "Entrar")

def professor_cadastro_v410():
    require_invite = v410_bool_setting("require_invite_code", "0")
    require_verify = v410_bool_setting("require_email_verification", "0")
    require_approval = v410_bool_setting("require_admin_approval", "0")
    dias = v410_trial_days()
    limit = v410_int_setting("signup_limit_per_ip", 3)

    if request.method == "POST":
        ip = v37_client_ip() if "v37_client_ip" in globals() else (request.remote_addr or "local")
        email = request.form.get("email", "").lower().strip()
        senha = request.form.get("password", "")
        senha2 = request.form.get("password2", "")
        invite_code = request.form.get("invite_code", "").strip().upper()

        if not v410_bool_setting("registration_open", "1"):
            try: v37_log_signup(email, "blocked", "registration_closed")
            except Exception: pass
            flash("O cadastro está fechado no momento.")
            return redirect("/cadastro")

        try:
            ip_count = v37_ip_signup_count_today(ip)
        except Exception:
            ip_count = 0
        if limit > 0 and ip_count >= limit:
            try: v37_log_signup(email, "blocked", "ip_limit")
            except Exception: pass
            flash("Limite de cadastro atingido neste acesso. Tente novamente amanhã.")
            return redirect("/cadastro")

        if not email or "@" not in email:
            try: v37_log_signup(email, "blocked", "invalid_email")
            except Exception: pass
            flash("Informe um e-mail válido.")
            return redirect("/cadastro")

        try:
            temp_email = v37_is_temp_email(email)
        except Exception:
            temp_email = False
        if v410_bool_setting("block_temp_emails", "1") and temp_email:
            try: v37_log_signup(email, "blocked", "temp_email")
            except Exception: pass
            flash("Use um e-mail verdadeiro da escola ou pessoal. E-mails temporários não são aceitos.")
            return redirect("/cadastro")

        if len(senha) < 6 or senha != senha2:
            try: v37_log_signup(email, "blocked", "invalid_password")
            except Exception: pass
            flash("A senha precisa ter pelo menos 6 caracteres e confirmar corretamente.")
            return redirect("/cadastro")

        if q("SELECT id FROM users WHERE email=?", (email,), True):
            try: v37_log_signup(email, "blocked", "duplicated_email")
            except Exception: pass
            flash("Já existe uma conta com este e-mail.")
            return redirect("/cadastro")

        invite = None
        plan = "AVALIACAO_GRATUITA"
        days = dias
        if require_invite:
            try:
                invite = v37_valid_invite(invite_code)
            except Exception:
                invite = None
            if not invite:
                try: v37_log_signup(email, "blocked", "invalid_invite")
                except Exception: pass
                flash("Código de convite inválido ou já utilizado.")
                return redirect("/cadastro")
            plan = invite["plan"] or "AVALIACAO_GRATUITA"
            if str(plan).upper() == "TESTE":
                plan = "AVALIACAO_GRATUITA"
            days = int(invite["days"] or dias)

        approved = 0 if require_approval else 1
        email_verified = 0 if require_verify else 1
        valid = (datetime.now() + timedelta(days=int(days))).date().isoformat()

        try:
            q('''INSERT INTO users(name,email,password,is_admin,plan,valid_until,school,city,state,avatar,teaching_style,local_context,default_instructions,is_active,approved,email_verified,created_ip,created_user_agent)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (request.form.get("name", "Professor(a)"), email, generate_password_hash(senha), 0, plan, valid,
                 request.form.get("school", ""), request.form.get("city", ""), request.form.get("state", "")[:2], "",
                 "Acolhedor e simples", "", "", 1, approved, email_verified, ip, (request.headers.get("User-Agent") or "")[:500]))
        except Exception:
            q('''INSERT INTO users(name,email,password,is_admin,plan,valid_until,school,city,state,avatar,teaching_style,local_context,default_instructions)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (request.form.get("name", "Professor(a)"), email, generate_password_hash(senha), 0, plan, valid,
                 request.form.get("school", ""), request.form.get("city", ""), request.form.get("state", "")[:2], "",
                 "Acolhedor e simples", "", ""))

        u = q("SELECT id FROM users WHERE email=?", (email,), True)
        uid = u["id"] if u else 0
        if invite:
            try: v37_mark_invite_used(invite_code, uid)
            except Exception: pass

        if require_verify:
            try:
                code, sent = v37_create_verification(uid, email)
            except Exception:
                code, sent = "", False
            try: v37_log_signup(email, "pending", "email_verification")
            except Exception: pass
            if sent:
                flash("Conta criada. Enviamos um código para seu e-mail.")
            else:
                flash(f"Conta criada. Código de verificação: {code}")
            return redirect(f"/verificar-email?email={email}")

        if require_approval:
            try: v37_log_signup(email, "pending", "admin_approval")
            except Exception: pass
            flash("Conta criada. Aguarde a liberação do acesso.")
            return redirect("/login")

        try: v37_log_signup(email, "created", "ok")
        except Exception: pass
        flash(f"Conta criada com sucesso. Você recebeu uma avaliação gratuita de {days} dias.")
        return redirect("/login")

    invite_field = '''
      <p><label>Código de convite</label><input name="invite_code" placeholder="Digite o código recebido"></p>
    ''' if require_invite else ""

    security_note = "Cadastro protegido com limite de acesso e bloqueio de e-mails temporários."
    if require_invite:
        security_note += " É necessário código de convite."
    if require_approval:
        security_note += " A conta passa por liberação."
    if require_verify:
        security_note += " O e-mail precisa ser verificado."

    content = f'''
    <div class="auth-card login-card-v34 cadastro-card-v34 professional-signup-v410">
      <div class="login-mini-brand"><div class="auth-logo">AP</div><div><b>AulaPronta Pro</b><span>Avaliação gratuita por {dias} dias</span></div></div>
      <h1>Criar conta de professor</h1>
      <p class="sub">Preencha seus dados para começar a usar o estúdio de materiais pedagógicos. {security_note}</p>
      {v410_flash_html()}
      <form method="post">
        <div class="auth-grid cadastro-grid-v34">
          <p><label>Nome do professor</label><input name="name" placeholder="Seu nome completo"></p>
          <p><label>E-mail</label><input name="email" placeholder="seuemail@escola.com"></p>
          <p><label>Senha</label><input type="password" name="password" placeholder="Mínimo de 6 caracteres"></p>
          <p><label>Confirmar senha</label><input type="password" name="password2" placeholder="Repita a senha"></p>
          <p><label>Escola</label><input name="school" placeholder="Nome da escola"></p>
          <p><label>Cidade</label><input name="city" placeholder="Cidade"></p>
          {invite_field}
        </div>
        <div class="trial-box-v35 professional-trial-v410"><b>Avaliação gratuita</b><span>Acesso liberado por {dias} dias após o cadastro.</span></div>
        <div class="action-row">
          <button class="btn primary big">Começar agora</button>
          <a class="btn" href="/login">Voltar ao login</a>
        </div>
      </form>
    </div>'''
    return render(content, "Criar conta")

def professor_dashboard_v410():
    u = user()
    recent = q("SELECT * FROM materials WHERE user_id=? ORDER BY id DESC LIMIT 6", (u["id"],))
    recent_html = ""
    for m in recent:
        recent_html += f'<a class="action" href="/professor/material/{m["id"]}"><b>{esc(m["type"])} - {esc(m["title"])}</b><span>{esc(m["created_at"])}</span></a>'
    if not recent_html:
        recent_html = '<p class="muted">Nenhum material gerado ainda.</p>'
    plan = v410_plan_label(u["plan"])
    content = f'''
    <div class="hero">
      <div><span>AulaPronta Pro</span><h1>Estúdio do Professor</h1><p>Crie atividades, avaliações, planos de aula e relatórios com visual profissional e alinhamento pedagógico.</p></div>
      {v410_license_card(u)}
    </div>
    <div class="cards">
      <div class="card"><small>Questões</small><strong>{q("SELECT COUNT(*) c FROM questions", one=True)["c"]}</strong><p>banco pedagógico</p></div>
      <div class="card"><small>Conteúdos</small><strong>{q("SELECT COUNT(*) c FROM topics", one=True)["c"]}</strong><p>temas por turma</p></div>
      <div class="card"><small>Meus materiais</small><strong>{q("SELECT COUNT(*) c FROM materials WHERE user_id=?", (u["id"],), one=True)["c"]}</strong><p>produções salvas</p></div>
      <div class="card"><small>Acesso</small><strong>{esc(plan)}</strong><p>válido até {esc(u["valid_until"] or "---")}</p></div>
    </div>
    <div class="layout-2">
      <div class="panel"><h2>Criar novo material</h2>
        <div class="action-grid">
          <a class="action" href="/professor/atividade"><b>Atividade guiada</b><span>Folha do aluno com gabarito.</span></a>
          <a class="action" href="/professor/avaliacao"><b>Avaliação completa</b><span>Prova organizada com critérios.</span></a>
          <a class="action" href="/professor/plano"><b>Plano de aula</b><span>Planejamento com habilidade BNCC.</span></a>
          <a class="action" href="/professor/parecer"><b>Relatórios e pareceres</b><span>Texto pedagógico pronto para adaptar.</span></a>
        </div>
      </div>
      <div class="panel"><h2>Materiais recentes</h2>{recent_html}</div>
    </div>'''
    return render(content, "Início")

def assinatura_professor_v410():
    u = user()
    d = v410_days_left(u["valid_until"])
    if d is not None and d < 0:
        status = "Expirada"
    elif d is not None and d <= 7:
        status = "Vencendo"
    else:
        status = "Ativa"

    cards = ""
    for key, p in PLANOS_PROFESSOR.items():
        cards += f'''<div class="card"><small>{p["label"]}</small><strong>R$ {p["amount"]}</strong><p>{p["days"]} dias de acesso</p><a class="btn primary" href="/comprar/{key}">Solicitar renovação</a></div>'''

    orders = q("SELECT * FROM payment_orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (u["id"],))
    order_html = ""
    for o in orders:
        order_html += f'''<div class="commercial-order"><div><b>Pedido #{o["id"]} - {esc(o["plan"])}</b><span>Valor: R$ {esc(o["amount"])} - Situação: {esc(v410_status_label(o["status"]))} - {esc(o["created_at"])}</span></div><a class="btn" href="/pagamento/{o["id"]}">Ver pedido</a></div>'''
    if not order_html:
        order_html = '<p class="muted">Nenhum pedido de renovação criado ainda.</p>'

    content = f'''
    <div class="header"><div><span>Assinatura</span><h1>Minha assinatura</h1><p>Acompanhe sua validade e solicite renovação de forma simples e segura.</p></div>{v410_license_card(u)}</div>
    <div class="cards">
      <div class="card"><small>Status</small><strong>{esc(status)}</strong><p>situação do acesso</p></div>
      <div class="card"><small>Plano</small><strong>{esc(v410_plan_label(u["plan"]))}</strong><p>acesso atual</p></div>
      <div class="card"><small>Validade</small><strong>{esc(u["valid_until"] or "---")}</strong><p>data final</p></div>
      <div class="card"><small>Dias restantes</small><strong>{d if d is not None else "---"}</strong><p>tempo disponível</p></div>
    </div>
    <div class="panel"><h2>Renovar assinatura</h2><p class="muted">Escolha um plano, faça o Pix e envie o comprovante pelo WhatsApp.</p><div class="cards">{cards}</div></div>
    <div class="panel"><h2>Meus pedidos</h2>{order_html}</div>'''
    return render(content, "Minha assinatura")

def pagamento_professor_v410(order_id):
    u = user()
    o = q("SELECT * FROM payment_orders WHERE id=? AND user_id=?", (order_id, u["id"]), True)
    if not o:
        flash("Pedido não encontrado.")
        return redirect("/assinatura")

    try:
        pix_raw = v39_pix_key()
        pix_display = v310_format_br_phone(pix_raw)
        whatsapp_display = v310_format_br_phone(v39_whatsapp_number())
        pix_holder = v39_pix_holder()
        pix_bank = v39_pix_bank()
        whats_url = v39_whatsapp_url(u, o)
        msg = v39_payment_message(u, o)
    except Exception:
        pix_raw = os.getenv("PIX_KEY", "98996127032")
        pix_display = pix_raw
        whatsapp_display = os.getenv("WHATSAPP_PAYMENT", "5598996127032")
        pix_holder = os.getenv("PIX_HOLDER", "LUIS TIAGO SANTOS MARQUES")
        pix_bank = os.getenv("PIX_BANK", "BANCO MERCADO PAGO")
        whats_url = "#"
        msg = f"Olá! Fiz o pagamento do pedido #{o['id']} - {o['plan']} - R$ {o['amount']}."

    content = f'''
    <div class="header">
      <div>
        <span>Renovação</span>
        <h1>Pedido #{o["id"]}</h1>
        <p>Faça o Pix, envie o comprovante pelo WhatsApp e aguarde a liberação do acesso.</p>
      </div>
    </div>

    <div class="payment-premium-grid">
      <div class="panel payment-box">
        <h2>Plano {esc(o["plan"])}</h2>

        <div class="payment-summary-v39">
          <div><small>Valor</small><b>R$ {esc(o["amount"])}</b></div>
          <div><small>Situação</small><b>{esc(v410_status_label(o["status"]))}</b></div>
          <div><small>Referência</small><b>{esc(o["reference"])}</b></div>
        </div>

        <div class="pix-card-v39">
          <h3>Dados para pagamento Pix</h3>
          <p><label>Chave Pix — telefone</label><input id="pixDisplayV310" readonly value="{esc(pix_display)}"><input id="pixKeyV39" type="hidden" value="{esc(pix_raw)}"></p>
          <p><label>Nome completo</label><input readonly value="{esc(pix_holder)}"></p>
          <p><label>Banco</label><input readonly value="{esc(pix_bank)}"></p>
          <div class="phone-note-v310"><b>Chave para copiar:</b> {esc(pix_raw)}</div>
          <button class="btn" type="button" onclick="navigator.clipboard && navigator.clipboard.writeText(document.getElementById('pixKeyV39').value); alert('Chave Pix copiada!')">Copiar chave Pix</button>
        </div>

        <div class="whatsapp-card-v39">
          <h3>Enviar comprovante</h3>
          <p class="muted">Depois de pagar, clique no botão abaixo. O WhatsApp abrirá com a mensagem do pedido pronta. Anexe o comprovante antes de enviar.</p>
          <p><label>Mensagem pronta</label><textarea id="msgWhatsV39" readonly rows="7">{esc(msg)}</textarea></p>
          <div class="action-row-v39">
            <a class="btn primary big" href="/pagamento/{o["id"]}/confirmar-whatsapp" target="_blank">Enviar comprovante pelo WhatsApp</a>
            <button class="btn" type="button" onclick="navigator.clipboard && navigator.clipboard.writeText(document.getElementById('msgWhatsV39').value); alert('Mensagem copiada!')">Copiar mensagem</button>
            <a class="btn" href="/assinatura">Voltar</a>
          </div>
        </div>
      </div>

      <div class="panel support-box-v39">
        <h2>Resumo</h2>
        <p><b>Recebedor:</b><br>{esc(pix_holder)}</p>
        <p><b>Pix:</b><br>{esc(pix_display)}</p>
        <p><b>Banco:</b><br>{esc(pix_bank)}</p>
        <p><b>WhatsApp:</b><br>{esc(whatsapp_display)}</p>
        <a class="btn primary" href="{whats_url}" target="_blank">Abrir WhatsApp</a>
      </div>
    </div>
    '''
    return render(content, "Pedido de renovação")

app.view_functions["login_page"] = professor_login_page_v410
app.view_functions["cadastro"] = professor_cadastro_v410
app.view_functions["dashboard"] = login_required(professor_dashboard_v410)
if "assinatura" in app.view_functions:
    app.view_functions["assinatura"] = login_required(assinatura_professor_v410)
if "pagamento_page" in app.view_functions:
    app.view_functions["pagamento_page"] = login_required(pagamento_professor_v410)
