import re, unicodedata
from datetime import datetime, timedelta
from flask import render_template_string, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

PRO_VERSION_VISUAL = 'v2.4.5-ajuste-visual-final'

SUBJECT_VISUAL = {
    'Alfabetização': ('🔤', 'alfabetizacao'),
    'Língua Portuguesa': ('✍️', 'lingua-portuguesa'),
    'Redação': ('📝', 'redacao'),
    'Matemática': ('➗', 'matematica'),
    'Ciências': ('🔬', 'ciencias'),
    'História': ('🏛️', 'historia'),
    'Geografia': ('🌍', 'geografia'),
    'Arte': ('🎨', 'arte'),
    'Educação Física': ('⚽', 'educacao-fisica'),
    'Língua Inglesa': ('🌐', 'lingua-inglesa'),
    'Física': ('⚙️', 'fisica'),
    'Química': ('🧪', 'quimica'),
    'Biologia': ('🌿', 'biologia'),
    'Sociologia': ('👥', 'sociologia'),
    'Filosofia': ('💡', 'filosofia'),
    'Projeto de Vida': ('🚀', 'projeto-de-vida'),
    'Tecnologia e Informática': ('💻', 'tecnologia-e-informatica'),
    'Ensino Religioso': ('🤝', 'ensino-religioso'),
}

QUESTION_CUTE = ['🌟','🧠','📘','🎯','✨','💡','📝','🌈','🔎','📚']


def _subject_lookup(name):
    label = str(name or '').strip()
    if label in SUBJECT_VISUAL:
        return SUBJECT_VISUAL[label]
    for key, val in SUBJECT_VISUAL.items():
        if label.startswith(key):
            return val
    return ('⭐', 'default')


def subject_icon(name):
    return _subject_lookup(name)[0]


def subject_art(name):
    slug = _subject_lookup(name)[1]
    return f'/static/subject_art/{slug}.svg'


def material_info_from_text(text):
    raw = text or ''
    info = {'school':'', 'teacher':'', 'student':'', 'grade':'', 'subject':'', 'date':'', 'title':''}
    patterns = {
        'school': r'ESCOLA:\s*(.*)',
        'teacher': r'PROFESSOR\(A\):\s*(.*)',
        'student': r'ALUNO\(A\):\s*(.*)',
        'grade': r'TURMA:\s*(.*?)\s+DATA:',
        'date': r'DATA:\s*(.*)',
        'subject': r'DISCIPLINA:\s*(.*)'
    }
    for key, pat in patterns.items():
        m = re.search(pat, raw)
        if m:
            info[key] = m.group(1).strip()
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    for ln in lines:
        if ln.isupper() and len(ln) > 6 and 'DISCIPLINA' not in ln and 'ESCOLA' not in ln:
            info['title'] = ln.title()
            break
    return info


def days_left(value):
    if not value:
        return None
    try:
        return (datetime.fromisoformat(value).date() - datetime.now().date()).days
    except Exception:
        return None


def license_meta(u):
    if not u:
        return {'plan':'Visitante','date':'Sem login','days':'', 'status':'license-good'}
    d = days_left(u['valid_until'])
    status = 'license-good'
    if d is None:
        days_label = 'sem prazo definido'
    elif d < 0:
        status = 'license-expired'; days_label = 'expirada'
    elif d <= 7:
        status = 'license-soon'; days_label = f'{d} dia(s) restante(s)'
    else:
        days_label = f'{d} dia(s) restante(s)'
    return {'plan': u['plan'] or 'Professor', 'date': u['valid_until'] or '---', 'days': days_label, 'status': status}


def user_initials(u):
    name = (u['name'] or 'Professor').strip()
    parts = [p for p in name.split() if p]
    if not parts:
        return 'AP'
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def render_v24(content, title='AulaPronta Pro'):
    u = user()
    meta = license_meta(u)
    return render_template_string(BASE_HTML, content=content, title=title, u=u, license=meta, initials=user_initials(u), app_version=PRO_VERSION_VISUAL)

render = render_v24

BASE_HTML = '''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#D4A84F">
<title>{{title}}</title>
<link rel="manifest" href="/manifest.webmanifest">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
{% if u %}
<button class="mobile-menu" onclick="document.body.classList.toggle('menu-open')">MENU</button>
<div class="layout">
<aside class="side">
  <div class="brand">
    <div class="logo">AP</div>
    <div><h1>AulaPronta</h1><p>Professor Studio Premium</p></div>
  </div>
  <div class="version-badge">⭐ Identidade da disciplina <span>PWA / APK WebView</span></div>
  <div class="nav-section">Navegação principal</div>
  <nav>
    <a href="/professor"><span>IN</span><div><b>Início</b><small>Resumo da sua conta</small></div></a>
    <a href="/professor/atividade"><span>AT</span><div><b>Atividade Guiada</b><small>Folha do aluno + gabarito</small></div></a>
    <a href="/professor/avaliacao"><span>AV</span><div><b>Avaliação Completa</b><small>Prova com critérios</small></div></a>
    <a href="/professor/plano"><span>PL</span><div><b>Plano de Aula</b><small>Sequência e metodologia</small></div></a>
    <a href="/professor/parecer"><span>RP</span><div><b>Relatórios e Pareceres</b><small>Textos pedagógicos prontos</small></div></a>
    <a href="/professor/materiais"><span>BX</span><div><b>Biblioteca de Materiais</b><small>Histórico e exportações</small></div></a>
    <a href="/perfil"><span>PF</span><div><b>Perfil Profissional</b><small>Escola, foto e estilo</small></div></a>
    {% if u['is_admin'] %}<a href="/admin"><span>AD</span><div><b>Gestão Premium</b><small>Seriais, usuários e banco</small></div></a>{% endif %}
    <a href="/logout"><span>SA</span><div><b>Sair</b><small>Encerrar sessão</small></div></a>
  </nav>
  <div class="profile {{license.status}}">
    <div class="profile-top">
      {% if u['avatar'] %}<img class="avatar" src="{{u['avatar']}}" alt="avatar">{% else %}<div class="avatar-text">{{initials}}</div>{% endif %}
      <div><strong>{{u['name'] or 'Professor(a)'}}</strong><p>{{u['school'] or 'Sua escola'}}</p><p>{{u['city'] or 'Cidade'}}{% if u['state'] %} / {{u['state']}}{% endif %}</p></div>
    </div>
    <div class="license-pill {{license.status}}">
      <div><div class="plan">{{license.plan}}</div><div class="date">Válido até {{license.date}}</div></div>
      <div class="days">{{license.days}}</div>
    </div>
  </div>
</aside>
<main class="main">
{% with msgs = get_flashed_messages() %}{% for m in msgs %}<div class="msg">{{m}}</div>{% endfor %}{% endwith %}
{{content|safe}}
<footer class="page-footer">AulaPronta Pro • Estúdio Premium para web, desktop (.exe) e Android (PWA/WebView)</footer>
</main></div>
{% else %}
<div class="auth">
  <div class="auth-shell">
    <section class="auth-aside">
      <div>
        <div class="version-badge">AulaPronta Pro • Plataforma premium para professores</div>
        <h2>Um visual mais profissional para vender como assinatura.</h2>
        <p>Crie atividades, avaliações, planos e pareceres com identidade visual premium, banco pedagógico robusto, exportação prática e experiência pronta para desktop e Android.</p>
      </div>
      <img src="/static/login_hero.svg" alt="Painel ilustrado do AulaPronta Pro">
      <div class="auth-info">
        <div class="auth-tile"><b>Banco local</b><span>Conteúdos por turma e disciplina</span></div>
        <div class="auth-tile"><b>PWA</b><span>Pronto para experiência mobile</span></div>
        <div class="auth-tile"><b>Premium</b><span>Visual escuro elegante</span></div>
      </div>
    </section>
    <section>{{content|safe}}</section>
  </div>
</div>
{% endif %}
<script src="/static/app.js"></script>
<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/service-worker.js').catch(()=>{})}</script>
</body></html>'''


def service_worker_v24():
    js = "const CACHE_NAME='aulapronta-pro-v245-ajuste-visual-final';const OFFLINE_URL='/offline';self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll([OFFLINE_URL,'/static/style.css','/static/app.js','/static/login_hero.svg'])))});self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k))))) });self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(fetch(e.request).catch(()=>caches.match(e.request).then(r=>r||caches.match(OFFLINE_URL))))});"
    return app.response_class(js, mimetype='application/javascript')


def material_action_card(title, desc, href, img=None):
    art = f'<img src="{img}" alt="{esc(title)}">' if img else ''
    return f'<a class="action with-art" href="{href}">{art}<div><b>{esc(title)}</b><span>{esc(desc)}</span></div></a>'


def premium_header_v24(u, sub, gr, title):
    return f"ESCOLA: {u['school'] or '________________'}\nPROFESSOR(A): {u['name']}\nALUNO(A): ________________________________________________\nTURMA: {gr['name']}    DATA: ___/___/____\nDISCIPLINA: {sub['name']}   {subject_icon(sub['name'])}\n\n{title.upper()}\n\n"

premium_header = premium_header_v24


def premium_q_student_v24(qq, n):
    cute = QUESTION_CUTE[(n - 1) % len(QUESTION_CUTE)]
    s = f"{cute} {n}. {qq['statement']}\n   {qq['command']}\n"
    if qq['type'] == 'MULTIPLA':
        for a in q('SELECT * FROM alternatives WHERE question_id=? ORDER BY letter', (qq['id'],)):
            s += f"   {a['letter']}) {a['text']}\n"
    elif qq['type'] == 'VF':
        s += '   (   ) Verdadeiro     (   ) Falso\n'
    elif qq['type'] == 'LACUNAS':
        s += '   Resposta: ________________________________\n'
    elif qq['type'] == 'TEXTO':
        s += '   Produção textual:\n   __________________________________________________________\n   __________________________________________________________\n   __________________________________________________________\n'
    else:
        s += '   Resposta: ________________________________________________\n   __________________________________________________________\n'
    return s

premium_q_student = premium_q_student_v24


def premium_q_teacher_v24(qq, n):
    cute = QUESTION_CUTE[(n - 1) % len(QUESTION_CUTE)]
    skill = f"\n   Habilidade/objetivo: {qq['skill']}" if qq['skill'] else ''
    return f"{cute} {n}. {qq['statement']}\n   Tipo: {qq['type']} | Nível: {qq['difficulty']}{skill}\n   Resposta esperada: {qq['answer']}\n   Orientação: {qq['explanation']}\n"

premium_q_teacher = premium_q_teacher_v24


def form_selector_v24(extra=''):
    return f'''<div class="wizard">
      <div class="step active"><b>1</b><span>Selecione a turma</span></div>
      <div class="step active"><b>2</b><span>Escolha a disciplina</span></div>
      <div class="step active"><b>3</b><span>Defina o conteúdo</span></div>
      <div class="step"><b>4</b><span>Gere o material</span></div>
    </div>
    <div class="grid premium-selects">
      <p><label>Disciplina</label><select name="subject" id="subject">{options(q('SELECT * FROM subjects ORDER BY name'))}</select></p>
      <p><label>Turma / Ano</label><select name="grade" id="grade">{options(q('SELECT * FROM grades ORDER BY ord'))}</select></p>
      <p><label>Tema / Conteúdo</label><select name="topic" id="topic"></select><small id="topicHelp" class="field-help">Escolha disciplina e turma para carregar os temas disponíveis.</small></p>
      <p><label>Nível de dificuldade</label><select name="difficulty"><option>Todas</option><option>Fácil</option><option>Média</option><option>Difícil</option></select></p>
      {extra}
    </div>
    <div class="subject-showcase"><img id="subjectPreviewImg" src="/static/subject_art/default.svg" alt="Disciplina"><div><h3 id="subjectPreviewTitle">Disciplina em destaque</h3><p id="subjectPreviewDesc">Este é apenas o ícone visual da disciplina. Ele ajuda o material a ficar mais bonito e organizado.</p><div id="subjectPreviewMeta" class="subject-meta"></div></div></div>'''

form_selector = form_selector_v24


def login_page_v24():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        if is_locked(email):
            flash('Muitas tentativas incorretas. Aguarde alguns minutos e tente novamente.')
            return redirect('/login')
        u = q('SELECT * FROM users WHERE email=?', (email,), True)
        if u and check_password_hash(u['password'], request.form.get('password', '')):
            clear_failed(email)
            session['uid'] = u['id']
            return redirect('/professor')
        record_failed(email)
        flash('E-mail ou senha inválidos.')
    content = '''<div class="auth-card"><div class="auth-logo">AP</div><h1>Entrar no estúdio</h1><p class="sub">Acesse seu painel premium para gerar materiais com aparência profissional.</p><form method="post"><p><label>E-mail</label><input name="email" placeholder="professor@escola.com"></p><p><label>Senha</label><input name="password" type="password" placeholder="••••••••"></p><button class="btn primary big">Entrar</button></form><a class="link" href="/cadastro">Ainda não tenho conta • ativar com serial</a></div>'''
    return render(content, 'Login')


def cadastro_v24():
    if request.method == 'POST':
        code = request.form.get('serial', '').upper().strip()
        s = q('SELECT * FROM serials WHERE code=? AND active=1 AND used=0', (code,), True)
        if not s:
            flash('Serial inválido, inativo ou já utilizado.')
            return redirect('/cadastro')
        if request.form.get('password', '') != request.form.get('password2', ''):
            flash('As senhas não conferem.')
            return redirect('/cadastro')
        email = request.form.get('email', '').lower().strip()
        if not email or '@' not in email or len(request.form.get('password', '')) < 4:
            flash('Informe um e-mail válido e uma senha com pelo menos 4 caracteres.')
            return redirect('/cadastro')
        if q('SELECT id FROM users WHERE email=?', (email,), True):
            flash('Já existe uma conta com este e-mail.')
            return redirect('/cadastro')
        valid = (datetime.now() + timedelta(days=s['days'])).date().isoformat()
        uid = insert('INSERT INTO users(name,email,password,is_admin,plan,valid_until,teaching_style) VALUES(?,?,?,?,?,?,?)', (request.form.get('name', 'Professor(a)'), email, generate_password_hash(request.form.get('password', '')), 0, s['plan'], valid, 'Detalhado e organizado'))
        q('UPDATE serials SET used=1,used_by=?,used_at=? WHERE id=?', (uid, datetime.now().isoformat(), s['id']))
        flash('Conta criada com sucesso. Faça login para entrar no sistema.')
        return redirect('/login')
    content = '''<div class="auth-card wide"><div class="auth-logo">AP</div><h1>Ativar conta com serial</h1><p class="sub">Use o serial da licença para criar sua conta e já deixar o sistema pronto para o seu perfil de professor.</p><form method="post"><div class="auth-grid"><p><label>Nome do professor</label><input name="name" placeholder="Seu nome"></p><p><label>E-mail</label><input name="email" placeholder="professor@escola.com"></p><p><label>Senha</label><input type="password" name="password"></p><p><label>Confirmar senha</label><input type="password" name="password2"></p></div><p><label>Serial de ativação</label><input name="serial" placeholder="AP-XXXX-XXXX-XXXX"></p><div class="action-row"><button class="btn primary big">Criar conta</button><a class="btn" href="/login">Voltar ao login</a></div></form></div>'''
    return render(content, 'Cadastro')


def expirada_v24():
    u = user(); when = u['valid_until'] if u else '---'
    return render(f'<div class="panel"><h1>Licença expirada</h1><p>Seu acesso venceu em <b>{esc(when)}</b>. Gere um novo serial ou peça renovação para continuar usando a plataforma.</p><div class="action-row"><a class="btn primary" href="/logout">Sair</a><a class="btn" href="/login">Voltar ao login</a></div></div>', 'Licença expirada')


def premium_dashboard_v24():
    u = user()
    cards = f'''<div class="cards">
      <div class="card"><small>Questões</small><strong>{q('SELECT COUNT(*) c FROM questions',one=True)['c']}</strong><p>banco premium por disciplina</p></div>
      <div class="card"><small>Conteúdos</small><strong>{q('SELECT COUNT(*) c FROM topics',one=True)['c']}</strong><p>temas por turma e etapa</p></div>
      <div class="card"><small>Materiais</small><strong>{q('SELECT COUNT(*) c FROM materials WHERE user_id=?',(u['id'],),one=True)['c']}</strong><p>criados por você</p></div>
      <div class="card"><small>Licença</small><strong>{esc(u['plan'] or 'Premium')}</strong><p>expira em {esc(u['valid_until'] or '---')}</p></div>
    </div>'''
    recent = q('SELECT * FROM materials WHERE user_id=? ORDER BY id DESC LIMIT 6', (u['id'],))
    recent_html = ''.join([f'<a class="action" href="/professor/material/{m["id"]}"><b>{esc(m["type"])} — {esc(m["title"])}</b><span>{esc(m["created_at"])}</span></a>' for m in recent]) or '<p class="muted">Nenhum material gerado até agora.</p>'
    actions = '<div class="layout-2"><div class="panel"><h2>O que você quer preparar hoje?</h2><div class="action-grid">'
    actions += material_action_card('Atividade Guiada','Folha do aluno com texto de apoio, questões e gabarito.','/professor/atividade','/static/subject_art/default.svg')
    actions += material_action_card('Avaliação Completa','Provas e simulados com questões objetivas e discursivas.','/professor/avaliacao','/static/subject_art/matematica.svg')
    actions += material_action_card('Plano de Aula','Planejamento pedagógico com objetivo, metodologia e avaliação.','/professor/plano','/static/subject_art/lingua-portuguesa.svg')
    actions += material_action_card('Relatórios e Pareceres','Texto pedagógico pronto, claro e profissional.','/professor/parecer','/static/subject_art/historia.svg')
    actions += '</div></div><div class="panel"><h2>Biblioteca recente</h2>' + recent_html + '</div></div>'
    hero = f'''<div class="hero"><div><span>AulaPronta Pro</span><h1>Estúdio do Professor</h1><p>Seu painel premium para criar materiais com a cara da sua escola, da sua disciplina e da sua turma.</p><div class="header-meta"><div class="header-chip">Plano <strong>{esc(u['plan'] or 'Premium')}</strong></div><div class="header-chip">Vence em <strong>{esc(u['valid_until'] or '---')}</strong></div><div class="header-chip">Perfil <strong>{esc(u['teaching_style'] or 'Acolhedor e simples')}</strong></div></div></div><div class="hero-art"><img src="/static/login_hero.svg" alt="Painel AulaPronta Pro"></div></div>'''
    return render(hero + cards + actions)


def premium_atividade_v24():
    if request.method == 'POST':
        u = user(); sub, gr, top = get_sel()
        if not (sub and gr and top):
            flash('Escolha disciplina, turma e conteúdo válidos.')
            return redirect('/professor/atividade')
        total = safe_int(request.form.get('quantity', 10), 10, 1, 60)
        qs = premium_build_questions(sub, gr, top, total, request.form.get('difficulty','Todas'))
        student = premium_header(u, sub, gr, f'Atividade de {top["name"]}') + premium_instruction(u, gr)
        student += f"TEMA CENTRAL: {top['name']} {subject_icon(sub['name'])}\n\n"
        if request.form.get('text'):
            tx = q('SELECT * FROM texts WHERE topic_id=? ORDER BY RANDOM() LIMIT 1', (top['id'],), one=True)
            if tx:
                student += f"📖 TEXTO DE APOIO\n{tx['title']}\n{tx['body']}\n\n"
        student += 'QUESTÕES\n\n'
        teacher = premium_teacher_cover(u, sub, gr, top, 'atividade', len(qs))
        for i, qq in enumerate(qs, 1):
            student += premium_q_student(qq, i) + '\n'
            teacher += premium_q_teacher(qq, i) + '\n'
        mid = material_insert(u['id'], 'Atividade Guiada', f'Atividade - {sub["name"]} - {top["name"]}', student, teacher)
        return redirect(f'/professor/material/{mid}')
    extra = '<p class="quantity"><label>Quantidade de questões</label><input name="quantity" type="number" value="10" min="1" max="60"></p><label class="toggle"><input type="checkbox" name="text" checked><span>Incluir texto de apoio</span></label>'
    content = '<div class="header"><div><span>AulaPronta Pro</span><h1>Atividade Guiada</h1><p>Monte atividades bonitas, claras e com um visual mais encantador para o aluno.</p></div><div class="header-meta"><div class="header-chip">Com gabarito</div><div class="header-chip">Com estilo da turma</div></div></div><div class="panel"><form method="post">' + form_selector(extra) + '<div class="preview-note"><b>Dica premium:</b> o sistema aplica o perfil do professor, o nível da turma e o ícone visual da disciplina para deixar o material mais profissional.</div><button class="btn primary big">Gerar atividade agora</button></form></div>'
    return render(content)


def premium_avaliacao_v24():
    if request.method == 'POST':
        u = user(); sub, gr, top = get_sel()
        if not (sub and gr and top):
            flash('Escolha disciplina, turma e conteúdo válidos.')
            return redirect('/professor/avaliacao')
        total = safe_int(request.form.get('quantity',10),10,1,60)
        obj = safe_int(request.form.get('obj',5),5,0,60)
        qobj = premium_build_questions(sub,gr,top,obj,request.form.get('difficulty','Todas'),['MULTIPLA'])
        qdisc = premium_build_questions(sub,gr,top,max(0,total-len(qobj)),request.form.get('difficulty','Todas'),['DISCURSIVA','VF','LACUNAS','TEXTO'])
        qs = (qobj + qdisc)[:total]
        student = premium_header(u,sub,gr,f'Avaliação de {top["name"]}') + premium_instruction(u,gr)
        student += f"CONTEÚDO AVALIADO: {top['name']} {subject_icon(sub['name'])}\nValor: ________    Nota: ________\n\nQUESTÕES\n\n"
        teacher = premium_teacher_cover(u,sub,gr,top,'avaliação',len(qs)) + 'Critérios: considerar acerto conceitual, clareza e organização.\n\n'
        for i, qq in enumerate(qs, 1):
            student += premium_q_student(qq, i) + '\n'
            teacher += premium_q_teacher(qq, i) + '\n'
        mid = material_insert(u['id'],'Avaliação Completa',f'Avaliação - {sub["name"]} - {top["name"]}',student,teacher)
        return redirect(f'/professor/material/{mid}')
    extra = '<p class="quantity"><label>Total de questões</label><input name="quantity" type="number" value="10" min="1" max="60"></p><p class="quantity"><label>Questões objetivas</label><input name="obj" type="number" value="5" min="0" max="60"></p>'
    content = '<div class="header"><div><span>AulaPronta Pro</span><h1>Avaliação Completa</h1><p>Crie provas e simulados com visual premium, critérios claros e gabarito para o professor.</p></div></div><div class="panel"><form method="post">' + form_selector(extra) + '<div class="preview-note"><b>Sugestão:</b> combine questões objetivas e discursivas para uma avaliação mais completa e profissional.</div><button class="btn primary big">Gerar avaliação agora</button></form></div>'
    return render(content)


def premium_plano_v24():
    if request.method == 'POST':
        u = user(); sub, gr, top = get_sel()
        if not (sub and gr and top):
            flash('Escolha disciplina, turma e conteúdo válidos.')
            return redirect('/professor/plano')
        pl = q('SELECT * FROM lessons WHERE topic_id=? ORDER BY RANDOM() LIMIT 1', (top['id'],), one=True)
        txt = f'''PLANO DE AULA PREMIUM\n\nProfessor(a): {u['name']}\nEscola: {u['school'] or '________________'}\nDisciplina: {sub['name']} {subject_icon(sub['name'])}\nTurma: {gr['name']}\nEtapa: {premium_stage_label(gr)}\nTema: {top['name']}\nDuração: {(pl['duration'] if pl else '50 minutos')}\n\nPerfil pedagógico do professor:\n{premium_professor_note(u, gr)}\n\nObjetivo de aprendizagem:\n{(pl['objective'] if pl else premium_skill(premium_stage_label(gr), sub['name'], top['name']))}\n\nMetodologia:\n{(pl['methodology'] if pl else premium_methodology(premium_stage_label(gr)))}\n\nRecursos:\n{(pl['resources'] if pl else 'Quadro, caderno, material impresso, imagens temáticas e exemplos do cotidiano.')}\n\nDesenvolvimento da aula:\n{(pl['development'] if pl else premium_development(premium_stage_label(gr), sub['name'], top['name']))}\n\nAvaliação:\n{(pl['evaluation'] if pl else premium_evaluation(premium_stage_label(gr)))}\n\nTarefa / continuidade:\n{(pl['homework'] if pl else premium_homework(premium_stage_label(gr), top['name']))}\n'''
        mid = material_insert(u['id'], 'Plano de Aula', f'Plano - {sub["name"]} - {top["name"]}', txt, '')
        return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Plano de Aula</h1><p>Planejamento mais bonito e compreensível, pronto para impressão ou adaptação.</p></div></div><div class="panel"><form method="post">' + form_selector() + '<div class="preview-note"><b>Inclui:</b> objetivo, metodologia, recursos, desenvolvimento, avaliação e continuidade.</div><button class="btn primary big">Gerar plano de aula</button></form></div>')


def premium_parecer_v24():
    if request.method == 'POST':
        u = user(); aluno = request.form.get('student','Aluno(a)'); sit = request.form.get('situation','bom'); turma = request.form.get('turma','')
        frases = {'excelente':'apresenta excelente participação, autonomia e domínio das propostas.', 'bom':'participa das atividades propostas, demonstra interesse e vem desenvolvendo as aprendizagens esperadas.', 'regular':'participa quando solicitado, mas precisa ampliar autonomia, constância e organização.', 'dificuldade':'apresenta dificuldades em alguns conteúdos e necessita de retomadas graduadas e acompanhamento mais próximo.'}
        txt = f'''RELATÓRIO E PARECER PEDAGÓGICO\n\nAluno(a): {aluno}\nTurma/Série: {turma or '________________'}\nProfessor(a): {u['name']}\nEscola: {u['school'] or '________________'}\nData: {datetime.now().strftime('%d/%m/%Y')}\n\nParecer:\nO(a) estudante {frases.get(sit, frases['bom'])}\n\nObservação do professor:\n{u['default_instructions'] or 'Manter acompanhamento contínuo, valorizando avanços e retomando os pontos de maior dificuldade.'}\n\nIntervenções sugeridas:\n- Retomar conteúdos com exemplos práticos e linguagem clara.\n- Propor atividades graduadas, respeitando o ritmo do estudante.\n- Incentivar leitura dos enunciados, organização das respostas e participação oral.\n- Registrar avanços para acompanhar o desenvolvimento ao longo do período.\n'''
        mid = material_insert(u['id'], 'Relatório e Parecer', f'Parecer - {aluno}', txt, '')
        return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Relatórios e Pareceres</h1><p>Textos pedagógicos claros, bonitos e mais profissionais.</p></div></div><div class="panel"><form method="post"><div class="grid"><p><label>Nome do estudante</label><input name="student" value="Aluno(a)"></p><p><label>Turma / Série</label><input name="turma" placeholder="Ex.: 7º ano A"></p><p><label>Situação</label><select name="situation"><option value="excelente">Excelente</option><option value="bom" selected>Bom</option><option value="regular">Regular</option><option value="dificuldade">Precisa de acompanhamento</option></select></p></div><button class="btn primary big">Gerar parecer</button></form></div>')


def premium_materiais_v24():
    rows = q('SELECT * FROM materials WHERE user_id=? ORDER BY id DESC', (user()['id'],))
    html = '<div class="header"><div><span>AulaPronta Pro</span><h1>Biblioteca de Materiais</h1><p>Veja, exporte e organize tudo o que já foi gerado na sua conta.</p></div></div><div class="panel">'
    if not rows:
        html += '<p class="muted">Nenhum material gerado até agora.</p>'
    for m in rows:
        info = material_info_from_text(m['student'])
        img = subject_art(info.get('subject'))
        desc = f"{info.get('subject') or m['type']} • {info.get('grade') or 'Turma não identificada'} • {m['created_at']}"
        html += material_action_card(m['title'], desc, f"/professor/material/{m['id']}", img)
    html += '</div>'
    return render(html)


def premium_material_v24(mid):
    m = q('SELECT * FROM materials WHERE id=? AND user_id=?', (mid, user()['id']), True)
    if not m:
        flash('Material não encontrado ou não pertence a esta conta.')
        return redirect('/professor/materiais')
    info = material_info_from_text(m['student'])
    title = info.get('title') or m['title']
    subject = info.get('subject') or m['type']
    img = subject_art(subject)
    teacher_html = f'<h2>Folha do professor</h2><pre>{safe_pre(m["teacher"])}</pre>' if m['teacher'] else ''
    hero = f'''<div class="header"><div class="material-hero"><img src="{img}" alt="{esc(subject)}"><div><span>{esc(m['type'])}</span><h1>{esc(title)}</h1><p>Material gerado em {esc(m['created_at'])}</p><div class="material-meta"><span class="subject-badge">{esc(subject)}</span><span class="subject-badge">{esc(info.get('grade') or 'Turma')}</span><span class="subject-badge">Exportação pronta</span></div></div></div><div class="header-meta"><a class="btn primary" target="_blank" href="/professor/material/{mid}/print">Exportar HTML / PDF</a></div></div>'''
    content = hero + f'<div class="panel"><h2>Folha do aluno</h2><pre>{safe_pre(m["student"])}</pre>{teacher_html}</div>'
    return render(content, title)


def premium_material_print_v24(mid):
    m = q('SELECT * FROM materials WHERE id=? AND user_id=?', (mid, user()['id']), True)
    if not m:
        return '<h1>Material não encontrado</h1><p>Volte ao painel e escolha um material válido.</p>', 404
    info = material_info_from_text(m['student'])
    subject = info.get('subject') or m['type']
    title = info.get('title') or m['title']
    img = subject_art(subject)
    teacher_page = f'<div class="page"><h2>Folha do professor</h2><pre>{safe_pre(m["teacher"])}</pre></div>' if m['teacher'] else ''
    css = 'body{font-family:Arial,sans-serif;background:#eef2f7;padding:26px} .page{background:white;max-width:980px;margin:0 auto 24px;padding:34px;border-radius:18px;box-shadow:0 10px 30px rgba(0,0,0,.1)} .hero{display:grid;grid-template-columns:180px 1fr;gap:20px;align-items:center;padding-bottom:18px;border-bottom:2px solid #eceff4;margin-bottom:18px} .hero img{width:180px;border-radius:16px;border:1px solid #d8dee8} .badge{display:inline-block;background:#101827;color:#d4a84f;padding:8px 12px;border-radius:999px;font-size:12px;font-weight:700;margin-right:8px} h1{margin:8px 0 10px;color:#101827} p{color:#475569} pre{white-space:pre-wrap;font-family:Consolas,monospace;line-height:1.6;background:#f8fafc;border:1px solid #e5e7eb;padding:18px;border-radius:14px;color:#111827} @media print{body{padding:0;background:white}.page{box-shadow:none;border-radius:0;max-width:none;margin:0;padding:20px}}'
    return f'''<html><head><meta charset="utf-8"><title>{esc(title)}</title><style>{css}</style></head><body><div class="page"><div class="hero"><img src="{img}" alt="{esc(subject)}"><div><div><span class="badge">{esc(m['type'])}</span><span class="badge">{esc(subject)}</span></div><h1>{esc(title)}</h1><p>Gerado em {esc(m['created_at'])}</p></div></div><h2>Folha do aluno</h2><pre>{safe_pre(m['student'])}</pre></div>{teacher_page}</body></html>'''


def premium_perfil_v24():
    u = user()
    if request.method == 'POST':
        q('UPDATE users SET name=?, school=?, city=?, state=?, avatar=?, teaching_style=?, local_context=?, default_instructions=? WHERE id=?', (request.form.get('name',''), request.form.get('school',''), request.form.get('city',''), request.form.get('state','')[:2], request.form.get('avatar',''), request.form.get('teaching_style','Acolhedor e simples'), request.form.get('local_context',''), request.form.get('default_instructions',''), u['id']))
        flash('Perfil profissional salvo com sucesso.')
        return redirect('/perfil')
    styles = ['Acolhedor e simples','Direto e objetivo','Detalhado e organizado','Lúdico e participativo','EJA contextualizado','Ensino Médio analítico','Interdisciplinar e visual']
    style_opts = ''.join([f'<option {"selected" if (u["teaching_style"] or "") == s else ""}>{s}</option>' for s in styles])
    lic = license_meta(u)
    content = f'''<div class="header"><div><span>AulaPronta Pro</span><h1>Perfil Profissional</h1><p>Defina seu nome, escola, imagem e estilo pedagógico para deixar cada material com mais personalidade.</p></div><div class="header-meta"><div class="header-chip">Plano <strong>{esc(lic['plan'])}</strong></div><div class="header-chip">Expira em <strong>{esc(lic['date'])}</strong></div></div></div>
    <div class="panel"><form method="post"><div class="grid"><p><label>Nome do professor</label><input name="name" value="{esc(u['name'])}"></p><p><label>Nome da escola</label><input name="school" value="{esc(u['school'])}"></p><p><label>Cidade</label><input name="city" value="{esc(u['city'])}"></p><p><label>UF</label><input name="state" value="{esc(u['state'])}"></p></div><div class="grid"><p><label>Estilo dos materiais</label><select name="teaching_style">{style_opts}</select></p><p><label>Imagem do perfil (URL)</label><input name="avatar" value="{esc(u['avatar'])}" placeholder="https://..."></p></div><p><label>Contexto da turma / escola</label><textarea name="local_context" rows="4" placeholder="Ex.: turma com dificuldade de leitura, escola rural, EJA noturno, foco em atividades mais visuais...">{esc(u['local_context'])}</textarea></p><p><label>Orientações padrão do professor</label><textarea name="default_instructions" rows="4" placeholder="Ex.: usar linguagem simples, questões curtas, exemplos do cotidiano, incluir atividades mais fofas e acolhedoras...">{esc(u['default_instructions'])}</textarea></p><button class="btn primary big">Salvar perfil</button></form></div>'''
    return render(content)


def premium_admin_v24():
    return render(f'''<div class="header"><div><span>Gestão Premium</span><h1>Painel Administrativo</h1><p>Gerencie usuários, seriais, banco pedagógico e manutenção geral da plataforma.</p></div></div>
    <div class="cards"><div class="card"><small>Usuários</small><strong>{q("SELECT COUNT(*) c FROM users",one=True)["c"]}</strong><p>contas cadastradas</p></div><div class="card"><small>Seriais</small><strong>{q("SELECT COUNT(*) c FROM serials",one=True)["c"]}</strong><p>licenças emitidas</p></div><div class="card"><small>Questões</small><strong>{q("SELECT COUNT(*) c FROM questions",one=True)["c"]}</strong><p>banco pedagógico</p></div><div class="card"><small>Conteúdos</small><strong>{q("SELECT COUNT(*) c FROM topics",one=True)["c"]}</strong><p>temas disponíveis</p></div></div>
    <div class="panel"><div class="action-row"><a class="btn primary" href="/admin/seriais">Gerar seriais</a><a class="btn" href="/admin/usuarios">Ver usuários</a><a class="btn" href="/admin/checkup">Reconstruir banco</a><a class="btn" href="/admin/banco">Resumo do banco</a><a class="btn" href="/admin/diagnostico">Diagnóstico</a></div></div>''')

# override endpoints
app.view_functions['service_worker'] = service_worker_v24
app.view_functions['login_page'] = login_page_v24
app.view_functions['cadastro'] = cadastro_v24
app.view_functions['expirada'] = expirada_v24
app.view_functions['dashboard'] = login_required(premium_dashboard_v24)
app.view_functions['atividade'] = login_required(premium_atividade_v24)
app.view_functions['avaliacao'] = login_required(premium_avaliacao_v24)
app.view_functions['plano'] = login_required(premium_plano_v24)
app.view_functions['parecer'] = login_required(premium_parecer_v24)
app.view_functions['materiais'] = login_required(premium_materiais_v24)
app.view_functions['material'] = login_required(premium_material_v24)
app.view_functions['material_print'] = login_required(premium_material_print_v24)
app.view_functions['perfil'] = login_required(premium_perfil_v24)
app.view_functions['admin'] = admin_required(premium_admin_v24)
