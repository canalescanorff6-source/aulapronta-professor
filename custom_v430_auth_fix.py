
# ============================================================
# AulaPronta Pro v4.3 - Correção tela login/cadastro duplicada
# ============================================================

from flask import request, redirect, flash, session, render_template_string, get_flashed_messages
from werkzeug.security import check_password_hash

V430_VERSION = "v4.3-auth-layout-fix"

def v430_asset(path):
    return "/static/brand/" + path

def v430_trial_days():
    try:
        return v420_trial_days()
    except Exception:
        try:
            return v410_trial_days()
        except Exception:
            try:
                return int(os.getenv("TRIAL_DAYS", "7"))
            except Exception:
                return 7

def v430_messages_html():
    msgs = get_flashed_messages()
    if not msgs:
        return ""
    return "".join([f'<div class="alert-v430">{esc(m)}</div>' for m in msgs])

def v430_auth_shell(title, body):
    return render_template_string(f'''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
  <title>{esc(title)} - AulaPronta Pro</title>
  <link rel="icon" href="/static/brand/favicon.svg">
  <link rel="stylesheet" href="/static/style.css">
  <style>
    html,body{{margin:0!important;min-height:100%;overflow-x:hidden!important;background:#050b14!important;}}
    body{{font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;color:#fff;}}
    .auth-v430{{
      min-height:100vh;width:100%;box-sizing:border-box;display:grid;
      grid-template-columns:minmax(360px,1.05fr) minmax(360px,.95fr);
      gap:26px;padding:32px;
      background:radial-gradient(circle at 8% 18%,rgba(47,89,143,.32),transparent 34%),
      radial-gradient(circle at 92% 10%,rgba(218,165,55,.16),transparent 32%),#050b14;
    }}
    .auth-showcase-v430,.auth-card-v430{{
      border:1px solid rgba(94,132,180,.35);border-radius:30px;
      background:linear-gradient(145deg,rgba(19,35,58,.96),rgba(9,18,32,.97));
      box-shadow:0 24px 80px rgba(0,0,0,.42);box-sizing:border-box;min-width:0;
    }}
    .auth-showcase-v430{{padding:36px;display:flex;flex-direction:column;justify-content:center;overflow:hidden}}
    .brandline-v430{{display:flex;align-items:center;gap:14px;margin-bottom:18px}}
    .brandline-v430 img{{width:58px;height:58px;border-radius:18px;box-shadow:0 12px 30px rgba(0,0,0,.25)}}
    .brandline-v430 b{{display:block;color:#fff;font-size:22px;font-weight:900}}
    .brandline-v430 span{{display:block;color:#9fb3d1;font-weight:700;margin-top:3px}}
    .badge-v430{{display:inline-flex;width:max-content;max-width:100%;box-sizing:border-box;padding:10px 16px;border-radius:999px;color:#ffd96d;background:rgba(212,157,49,.12);border:1px solid rgba(212,157,49,.35);font-weight:900;font-size:13px;margin-bottom:22px}}
    .auth-showcase-v430 h1{{font-size:44px;line-height:1.05;margin:0 0 16px;color:#fff;letter-spacing:-.04em}}
    .auth-showcase-v430 p{{font-size:18px;line-height:1.55;color:#c0cde3;max-width:760px}}
    .hero-img-v430{{width:100%;max-height:330px;object-fit:contain;margin:28px 0 22px;border-radius:28px;border:1px solid rgba(94,132,180,.22);background:rgba(255,255,255,.02)}}
    .feature-row-v430{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
    .feature-row-v430 div{{padding:16px;border-radius:18px;background:rgba(255,255,255,.045);border:1px solid rgba(94,132,180,.2)}}
    .feature-row-v430 b{{display:block;color:#ffd96d;font-size:17px}}
    .feature-row-v430 span{{display:block;color:#c4d1e5;font-size:13px;margin-top:5px}}
    .auth-card-v430{{padding:38px;align-self:center;max-width:620px;width:100%;justify-self:center}}
    .form-logo-v430 img{{width:76px;height:76px;border-radius:22px;margin-bottom:20px}}
    .auth-card-v430 h2{{font-size:38px;line-height:1.08;margin:0 0 12px;color:#fff;letter-spacing:-.035em}}
    .auth-card-v430 p.desc{{color:#b9c8df;font-size:17px;line-height:1.5;margin:0 0 22px}}
    .auth-card-v430 label{{display:block;margin:13px 0 7px;color:#d9e6fb;font-weight:900}}
    .auth-card-v430 input{{width:100%;box-sizing:border-box;border:1px solid rgba(142,171,213,.32);background:#f5f8fc;color:#0d1728;border-radius:14px;padding:15px 16px;font-weight:800;outline:none}}
    .btn-v430{{width:100%;margin-top:18px;border:0;border-radius:15px;padding:16px;font-size:16px;font-weight:900;background:linear-gradient(135deg,#f3cf6a,#d6a63d);color:#111827;cursor:pointer;text-decoration:none;display:block;text-align:center;box-sizing:border-box}}
    .links-v430{{display:flex;justify-content:space-between;gap:16px;margin-top:18px}}
    .links-v430 a{{color:#eaf2ff;text-decoration:none;font-weight:900}}
    .note-v430,.alert-v430{{margin-top:16px;padding:12px 14px;border:1px solid rgba(212,168,79,.22);border-radius:14px;background:rgba(212,168,79,.08);color:#dce7f7;font-size:13px;font-weight:800}}
    .alert-v430{{margin:0 0 12px;color:#ffe29a}}
    .grid-v430{{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px}}
    .grid-v430 p{{margin:0}}
    .trial-v430{{margin:18px 0 0;padding:15px 16px;border-radius:18px;border:1px solid rgba(212,157,49,.35);background:rgba(212,157,49,.10)}}
    .trial-v430 b{{display:block;color:#ffd96d;font-size:17px}}
    .trial-v430 span{{display:block;color:#d3def1;margin-top:4px}}
    @media(max-width:980px){{
      .auth-v430{{grid-template-columns:1fr;padding:18px;min-height:100svh}}
      .auth-showcase-v430{{display:none}}
      .auth-card-v430{{padding:26px;border-radius:24px;max-width:none}}
      .grid-v430{{grid-template-columns:1fr}}
      .auth-card-v430 h2{{font-size:31px}}
    }}
  </style>
</head>
<body>{body}</body>
</html>''')

def login_page_v430():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        try:
            if is_locked(email):
                flash("Muitas tentativas incorretas. Aguarde alguns minutos.")
                return redirect("/login")
        except Exception:
            pass
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
            try: clear_failed(email)
            except Exception: pass
            session["uid"] = u["id"]
            return redirect("/professor")
        try: record_failed(email)
        except Exception: pass
        flash("E-mail ou senha inválidos.")
        return redirect("/login")

    body = f'''
    <div class="auth-v430">
      <section class="auth-showcase-v430">
        <div class="brandline-v430"><img src="{v430_asset('logo-aulapronta.svg')}" alt="AulaPronta Pro"><div><b>AulaPronta Pro</b><span>Professor Studio</span></div></div>
        <div class="badge-v430">Plataforma premium para professores</div>
        <h1>Sua aula pronta em poucos minutos.</h1>
        <p>Crie atividades, avaliações, planos de aula, relatórios e materiais alinhados à BNCC com visual profissional.</p>
        <img class="hero-img-v430" src="{v430_asset('login-hero.svg')}" alt="Painel AulaPronta Pro">
        <div class="feature-row-v430"><div><b>BNCC</b><span>Habilidades vinculadas</span></div><div><b>PDF/Word</b><span>Pronto para imprimir</span></div><div><b>Mobile</b><span>Funciona no APK</span></div></div>
      </section>
      <section class="auth-card-v430">
        <div class="form-logo-v430"><img src="{v430_asset('logo-aulapronta.svg')}" alt="Logo AulaPronta Pro"></div>
        <h2>Entrar no painel do professor</h2>
        <p class="desc">Acesse sua conta para preparar materiais pedagógicos com rapidez e organização.</p>
        {v430_messages_html()}
        <form method="post">
          <label>E-mail</label><input name="email" placeholder="seuemail@escola.com" autocomplete="email">
          <label>Senha</label><input name="password" type="password" placeholder="Digite sua senha" autocomplete="current-password">
          <button class="btn-v430">Entrar no sistema</button>
        </form>
        <div class="links-v430"><a href="/cadastro">Criar minha conta</a><a href="/termos">Termos de uso</a></div>
        <div class="note-v430">Acesso individual para professores, escolas e equipes pedagógicas.</div>
      </section>
    </div>'''
    return v430_auth_shell("Entrar", body)

try:
    _OLD_CADASTRO_PAGE_V430 = app.view_functions.get("cadastro")
except Exception:
    _OLD_CADASTRO_PAGE_V430 = None

def cadastro_page_v430():
    if request.method == "POST":
        if _OLD_CADASTRO_PAGE_V430:
            return _OLD_CADASTRO_PAGE_V430()
        return redirect("/cadastro")
    dias = v430_trial_days()
    body = f'''
    <div class="auth-v430">
      <section class="auth-showcase-v430">
        <div class="brandline-v430"><img src="{v430_asset('logo-aulapronta.svg')}" alt="AulaPronta Pro"><div><b>AulaPronta Pro</b><span>Cadastro do professor</span></div></div>
        <div class="badge-v430">Avaliação gratuita por {dias} dias</div>
        <h1>Comece a preparar materiais com aparência profissional.</h1>
        <p>Cadastre-se para acessar o estúdio do professor e gerar materiais prontos para imprimir, editar e organizar.</p>
        <img class="hero-img-v430" src="{v430_asset('signup-hero.svg')}" alt="Cadastro AulaPronta Pro">
        <div class="feature-row-v430"><div><b>Seguro</b><span>Cadastro protegido</span></div><div><b>Professor</b><span>Perfil individual</span></div><div><b>Escola</b><span>Identidade no material</span></div></div>
      </section>
      <section class="auth-card-v430">
        <div class="form-logo-v430"><img src="{v430_asset('logo-aulapronta.svg')}" alt="Logo AulaPronta Pro"></div>
        <h2>Criar conta de professor</h2>
        <p class="desc">Preencha seus dados para liberar sua avaliação gratuita e personalizar os materiais com sua escola.</p>
        {v430_messages_html()}
        <form method="post">
          <div class="grid-v430">
            <p><label>Nome completo</label><input name="name" placeholder="Nome do professor"></p>
            <p><label>E-mail</label><input name="email" placeholder="seuemail@escola.com"></p>
            <p><label>Senha</label><input type="password" name="password" placeholder="Mínimo de 6 caracteres"></p>
            <p><label>Confirmar senha</label><input type="password" name="password2" placeholder="Repita sua senha"></p>
            <p><label>Nome da escola</label><input name="school" placeholder="Ex.: Escola Municipal..."></p>
            <p><label>Cidade</label><input name="city" placeholder="Cidade"></p>
            <p><label>UF</label><input name="state" maxlength="2" placeholder="PA"></p>
            <p><label>Código de convite</label><input name="invite_code" placeholder="Opcional, se recebido"></p>
          </div>
          <div class="trial-v430"><b>Avaliação gratuita</b><span>Acesso por {dias} dias para conhecer a plataforma.</span></div>
          <button class="btn-v430">Começar agora</button>
          <a class="btn-v430" style="background:rgba(255,255,255,.06);color:#fff;border:1px solid rgba(142,171,213,.24)" href="/login">Já tenho conta</a>
        </form>
      </section>
    </div>'''
    return v430_auth_shell("Criar conta", body)

app.view_functions["login_page"] = login_page_v430
app.view_functions["cadastro"] = cadastro_page_v430
