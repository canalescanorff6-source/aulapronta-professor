
# ============================================================
# AulaPronta Pro v4.2 - Visual com logo e cadastro profissional
# ============================================================

import os
from flask import request

V420_VERSION = "v4.2-visual-logo"

_OLD_LOGIN_PAGE_V420 = app.view_functions.get("login_page")
_OLD_CADASTRO_PAGE_V420 = app.view_functions.get("cadastro")

def v420_asset(path):
    return "/static/brand/" + path

def v420_trial_days():
    try:
        return v410_trial_days()
    except Exception:
        try:
            return v37_trial_days()
        except Exception:
            try:
                return int(os.getenv("TRIAL_DAYS", "7"))
            except Exception:
                return 7

def v420_flash_html():
    try:
        return v410_flash_html()
    except Exception:
        try:
            return v37_flash_html()
        except Exception:
            return ""

def v420_login_page():
    if request.method == "POST" and _OLD_LOGIN_PAGE_V420:
        return _OLD_LOGIN_PAGE_V420()

    content = f'''
    <div class="auth-v420">
      <section class="auth-showcase-v420">
        <div class="brandline-v420">
          <img src="{v420_asset('logo-aulapronta.svg')}" alt="AulaPronta Pro">
          <div><b>AulaPronta Pro</b><span>Professor Studio</span></div>
        </div>
        <div class="auth-badge-v420">Plataforma premium para professores</div>
        <h1>Sua aula pronta em poucos minutos.</h1>
        <p>Crie atividades, avaliações, planos de aula, relatórios e materiais alinhados à BNCC com visual profissional.</p>
        <img class="auth-hero-img-v420" src="{v420_asset('login-hero.svg')}" alt="Painel AulaPronta Pro">
        <div class="feature-row-v420">
          <div><b>BNCC</b><span>Habilidades vinculadas</span></div>
          <div><b>PDF/Word</b><span>Pronto para imprimir</span></div>
          <div><b>Mobile</b><span>Funciona no APK</span></div>
        </div>
      </section>

      <section class="auth-form-v420">
        <div class="form-logo-v420"><img src="{v420_asset('logo-aulapronta.svg')}" alt="Logo AulaPronta Pro"></div>
        <h2>Entrar no painel do professor</h2>
        <p>Acesse sua conta para preparar materiais pedagógicos com rapidez e organização.</p>
        {v420_flash_html()}
        <form method="post">
          <label>E-mail</label>
          <input name="email" placeholder="seuemail@escola.com" autocomplete="email">
          <label>Senha</label>
          <input name="password" type="password" placeholder="Digite sua senha" autocomplete="current-password">
          <button class="btn primary big">Entrar no sistema</button>
        </form>
        <div class="login-links-v34 clean-links-v420">
          <a class="link" href="/cadastro">Criar minha conta</a>
          <a class="link" href="/termos">Termos de uso</a>
        </div>
        <div class="professional-note-v410">Acesso individual para professores, escolas e equipes pedagógicas.</div>
      </section>
    </div>
    '''
    return render(content, "Entrar")

def v420_cadastro_page():
    if request.method == "POST" and _OLD_CADASTRO_PAGE_V420:
        return _OLD_CADASTRO_PAGE_V420()

    dias = v420_trial_days()
    content = f'''
    <div class="auth-v420 signup-v420">
      <section class="auth-showcase-v420">
        <div class="brandline-v420">
          <img src="{v420_asset('logo-aulapronta.svg')}" alt="AulaPronta Pro">
          <div><b>AulaPronta Pro</b><span>Cadastro do professor</span></div>
        </div>
        <div class="auth-badge-v420">Avaliação gratuita por {dias} dias</div>
        <h1>Comece a preparar materiais com aparência profissional.</h1>
        <p>Cadastre-se para acessar o estúdio do professor e gerar materiais prontos para imprimir, editar e organizar.</p>
        <img class="auth-hero-img-v420" src="{v420_asset('signup-hero.svg')}" alt="Cadastro AulaPronta Pro">
        <div class="feature-row-v420">
          <div><b>Seguro</b><span>Cadastro protegido</span></div>
          <div><b>Professor</b><span>Perfil individual</span></div>
          <div><b>Escola</b><span>Identidade no material</span></div>
        </div>
      </section>

      <section class="auth-form-v420 signup-form-v420">
        <div class="form-logo-v420"><img src="{v420_asset('logo-aulapronta.svg')}" alt="Logo AulaPronta Pro"></div>
        <h2>Criar conta de professor</h2>
        <p>Preencha seus dados para liberar sua avaliação gratuita e personalizar os materiais com sua escola.</p>
        {v420_flash_html()}
        <form method="post">
          <div class="form-grid-v420">
            <p><label>Nome completo</label><input name="name" placeholder="Nome do professor"></p>
            <p><label>E-mail</label><input name="email" placeholder="seuemail@escola.com"></p>
            <p><label>Senha</label><input type="password" name="password" placeholder="Mínimo de 6 caracteres"></p>
            <p><label>Confirmar senha</label><input type="password" name="password2" placeholder="Repita sua senha"></p>
            <p><label>Nome da escola</label><input name="school" placeholder="Ex.: Escola Municipal..."></p>
            <p><label>Cidade</label><input name="city" placeholder="Cidade"></p>
            <p><label>UF</label><input name="state" maxlength="2" placeholder="PA"></p>
            <p><label>Código de convite</label><input name="invite_code" placeholder="Opcional, se recebido"></p>
          </div>
          <div class="trial-card-v420">
            <b>Avaliação gratuita</b>
            <span>Acesso por {dias} dias para conhecer a plataforma.</span>
          </div>
          <button class="btn primary big">Começar agora</button>
          <a class="btn ghost-v420" href="/login">Já tenho conta</a>
        </form>
      </section>
    </div>
    '''
    return render(content, "Criar conta")

try:
    BASE_HTML = BASE_HTML.replace('<div class="mark">AP</div>', '<div class="mark logo-mark-v420"><img src="/static/brand/logo-aulapronta.svg" alt="AP"></div>')
    BASE_HTML = BASE_HTML.replace('AulaPronta</h1>', 'AulaPronta Pro</h1>')
    BASE_HTML = BASE_HTML.replace('Professor Studio<br>Premium', 'Professor Studio')
    BASE_HTML = BASE_HTML.replace('☆ Identidade da disciplina', '★ Visual profissional')
    BASE_HTML = BASE_HTML.replace('PWA / APK WebView', 'App Android')
except Exception:
    pass

app.view_functions["login_page"] = v420_login_page
app.view_functions["cadastro"] = v420_cadastro_page
