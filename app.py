import os, sqlite3, secrets, string, random, html
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from flask import Flask, request, redirect, url_for, session, render_template_string, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
BASE = Path(__file__).resolve().parent
DB = Path(os.getenv('AULAPRONTA_DB', BASE.parent / 'dados' / 'aulapronta.db'))
DB.parent.mkdir(parents=True, exist_ok=True)
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-change-me')

@app.after_request
def security_headers(resp):
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Referrer-Policy'] = 'same-origin'
    return resp


# ---------------- DB ----------------
def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def q(sql, args=(), one=False):
    with conn() as c:
        cur = c.execute(sql, args)
        rows = cur.fetchall()
        c.commit()
        return (rows[0] if rows else None) if one else rows

def insert(sql, args=()):
    # Executa INSERT e retorna o ID correto na mesma conexão.
    with conn() as c:
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid


def init_db():
    c = conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT UNIQUE,password TEXT,is_admin INTEGER DEFAULT 0,plan TEXT,valid_until TEXT,school TEXT DEFAULT '',city TEXT DEFAULT '',state TEXT DEFAULT '',avatar TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS login_attempts(email TEXT PRIMARY KEY, attempts INTEGER DEFAULT 0, locked_until TEXT);
    CREATE TABLE IF NOT EXISTS serials(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE,plan TEXT,days INTEGER,used INTEGER DEFAULT 0,used_by INTEGER,created_at TEXT,used_at TEXT,active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS grades(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,ord INTEGER);
    CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,area TEXT);
    CREATE TABLE IF NOT EXISTS topics(id INTEGER PRIMARY KEY AUTOINCREMENT,subject_id INTEGER,grade_id INTEGER,name TEXT,description TEXT);
    CREATE TABLE IF NOT EXISTS texts(id INTEGER PRIMARY KEY AUTOINCREMENT,subject_id INTEGER,grade_id INTEGER,topic_id INTEGER,title TEXT,body TEXT,eja INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT,subject_id INTEGER,grade_id INTEGER,topic_id INTEGER,type TEXT,difficulty TEXT,statement TEXT,command TEXT,answer TEXT,explanation TEXT,eja INTEGER DEFAULT 0,active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS alternatives(id INTEGER PRIMARY KEY AUTOINCREMENT,question_id INTEGER,letter TEXT,text TEXT,correct INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY AUTOINCREMENT,subject_id INTEGER,grade_id INTEGER,topic_id INTEGER,title TEXT,duration TEXT,objective TEXT,methodology TEXT,resources TEXT,development TEXT,evaluation TEXT,homework TEXT);
    CREATE TABLE IF NOT EXISTS materials(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,type TEXT,title TEXT,student TEXT,teacher TEXT,created_at TEXT);
    ''')
    c.commit(); c.close()

def serial_code():
    a = string.ascii_uppercase + string.digits
    part = lambda: ''.join(secrets.choice(a) for _ in range(4))
    return f'APW-{part()}-{part()}-{part()}-{part()}'

def seed():
    if q('SELECT id FROM subjects LIMIT 1', one=True):
        return
    grades = ['Pré I','Pré II','1º ano','2º ano','3º ano','4º ano','5º ano','6º ano','7º ano','8º ano','9º ano','1ª série EM','2ª série EM','3ª série EM','EJA Alfabetização','EJA Fundamental I','EJA Fundamental II','EJA Médio']
    for i,g in enumerate(grades): q('INSERT INTO grades(name,ord) VALUES(?,?)',(g,i))
    themes = {
        'Alfabetização':['Vogais','Consoantes','Sílabas simples','Nome próprio','Rimas','Numerais'],
        'Língua Portuguesa':['Leitura e interpretação','Produção textual','Pontuação','Ortografia','Gêneros textuais'],
        'Matemática':['Números naturais','Operações fundamentais','Frações','Porcentagem','Geometria plana','Equações'],
        'Ciências':['Seres vivos','Corpo humano','Água','Meio ambiente','Saúde e higiene'],
        'História':['Tempo histórico','Povos indígenas','Brasil Colônia','República','Cidadania'],
        'Geografia':['Lugar e paisagem','Mapas e orientação','Campo e cidade','Clima','Meio ambiente'],
        'Arte':['Cores e formas','Artes visuais','Música','Dança','Arte no cotidiano'],
        'Educação Física':['Jogos e brincadeiras','Esportes coletivos','Ginástica','Saúde e movimento'],
        'Língua Inglesa':['Vocabulário básico','Cumprimentos','Números e cores','Family'],
        'Física':['Movimento','Força','Energia','Eletricidade'],
        'Química':['Matéria','Misturas','Átomos','Reações químicas'],
        'Biologia':['Citologia','Genética','Ecologia','Evolução'],
        'Sociologia':['Cultura','Sociedade','Trabalho','Cidadania'],
        'Filosofia':['Ética','Conhecimento','Política','Liberdade'],
        'Projeto de Vida':['Autoconhecimento','Organização pessoal','Profissões','Metas'],
        'Tecnologia e Informática':['Partes do computador','Digitação','Internet segura','Pensamento computacional'],
        'Ensino Religioso':['Valores','Convivência','Respeito','Solidariedade']}
    for s in themes: q('INSERT INTO subjects(name,area) VALUES(?,?)',(s,'Geral'))
    def applicable(g):
        if g in ['Pré I','Pré II']: return ['Alfabetização','Matemática','Arte','Educação Física','Projeto de Vida']
        if g in ['1º ano','2º ano']: return ['Alfabetização','Língua Portuguesa','Matemática','Ciências','História','Geografia','Arte','Educação Física']
        if g in ['3º ano','4º ano','5º ano']: return ['Língua Portuguesa','Matemática','Ciências','História','Geografia','Arte','Educação Física','Tecnologia e Informática']
        if g in ['6º ano','7º ano','8º ano','9º ano']: return ['Língua Portuguesa','Matemática','Ciências','História','Geografia','Língua Inglesa','Arte','Educação Física','Tecnologia e Informática']
        if 'EM' in g: return ['Língua Portuguesa','Matemática','Física','Química','Biologia','História','Geografia','Sociologia','Filosofia','Língua Inglesa','Arte','Educação Física','Projeto de Vida']
        return ['Alfabetização','Língua Portuguesa','Matemática','Ciências','História','Geografia','Arte','Projeto de Vida','Tecnologia e Informática']
    for gr in q('SELECT * FROM grades'):
        for sn in applicable(gr['name']):
            subj = q('SELECT * FROM subjects WHERE name=?',(sn,),True)
            for th in themes[sn]:
                top = insert('INSERT INTO topics(subject_id,grade_id,name,description) VALUES(?,?,?,?)',(subj['id'],gr['id'],th,f'Conteúdo sobre {th}'))
                q('INSERT INTO texts(subject_id,grade_id,topic_id,title,body,eja) VALUES(?,?,?,?,?,?)',(subj['id'],gr['id'],top,f'Texto de apoio - {th}',f'{th} é um conteúdo importante para compreender situações da vida escolar e social.',1 if 'EJA' in gr['name'] else 0))
                q('INSERT INTO lessons(subject_id,grade_id,topic_id,title,duration,objective,methodology,resources,development,evaluation,homework) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(subj['id'],gr['id'],top,f'Plano de aula - {th}','50 minutos',f'Compreender {th}.','Aula dialogada e atividade prática.','Quadro, caderno e material impresso.',f'Apresentar {th}, praticar e socializar respostas.','Observar participação e registros.',f'Atividade complementar sobre {th}.'))
                for diff in ['Fácil','Média','Difícil']:
                    for typ in ['DISCURSIVA','MULTIPLA','VF','LACUNAS']:
                        qid=insert('INSERT INTO questions(subject_id,grade_id,topic_id,type,difficulty,statement,command,answer,explanation,eja) VALUES(?,?,?,?,?,?,?,?,?,?)',(subj['id'],gr['id'],top,typ,diff,f'Sobre {th}, responda conforme o conteúdo estudado.','Responda com atenção.','Resposta coerente com o tema.',f'Avaliar compreensão sobre {th}.',1 if 'EJA' in gr['name'] else 0))
                        if typ=='MULTIPLA':
                            for L,txt,corr in [('A','Alternativa correta sobre o tema.',1),('B','Alternativa fora do contexto.',0),('C','Resposta incompleta.',0),('D','Conclusão incorreta.',0)]: q('INSERT INTO alternatives(question_id,letter,text,correct) VALUES(?,?,?,?)',(qid,L,txt,corr))
    admin_email=os.getenv('ADMIN_EMAIL','admin@aulapronta.com').lower(); admin_pass=os.getenv('ADMIN_PASSWORD','admin123'); admin_name=os.getenv('ADMIN_NAME','Administrador')
    if not q('SELECT id FROM users WHERE email=?',(admin_email,),True): q('INSERT INTO users(name,email,password,is_admin,plan,valid_until) VALUES(?,?,?,?,?,?)',(admin_name,admin_email,generate_password_hash(admin_pass),1,'ESCOLA','2099-12-31'))
    for plan,days in [('TESTE',7),('PROFESSOR',30),('PREMIUM',30),('ESCOLA',30)]: q('INSERT INTO serials(code,plan,days,created_at) VALUES(?,?,?,?)',(serial_code(),plan,days,datetime.now().isoformat()))

def reset_pedagogico():
    for table in ['alternatives','questions','texts','lessons','topics','subjects','grades']:
        q(f'DELETE FROM {table}')
        try:
            q('DELETE FROM sqlite_sequence WHERE name=?',(table,))
        except Exception:
            pass


def repair_bad_seed():
    # Corrige banco antigo criado com IDs 0 por causa de last_insert_rowid em conexão errada.
    try:
        invalid_questions = q('SELECT COUNT(*) c FROM questions WHERE topic_id=0 OR topic_id IS NULL', one=True)['c']
        invalid_texts = q('SELECT COUNT(*) c FROM texts WHERE topic_id=0 OR topic_id IS NULL', one=True)['c']
        invalid_lessons = q('SELECT COUNT(*) c FROM lessons WHERE topic_id=0 OR topic_id IS NULL', one=True)['c']
        has_topics = q('SELECT COUNT(*) c FROM topics', one=True)['c']
        has_subjects = q('SELECT COUNT(*) c FROM subjects', one=True)['c']
        if invalid_questions or invalid_texts or invalid_lessons or (has_subjects and not has_topics):
            reset_pedagogico()
    except Exception:
        pass

init_db(); repair_bad_seed(); seed()

# ---------------- Helpers ----------------
def user():
    return q('SELECT * FROM users WHERE id=?',(session.get('uid'),),True) if session.get('uid') else None

def is_locked(email):
    row = q('SELECT * FROM login_attempts WHERE email=?',(email,),True)
    if not row or not row['locked_until']:
        return False
    return row['locked_until'] > datetime.now().isoformat()

def record_failed(email):
    row = q('SELECT * FROM login_attempts WHERE email=?',(email,),True)
    attempts = (row['attempts'] if row else 0) + 1
    locked = ''
    if attempts >= 5:
        locked = (datetime.now() + timedelta(minutes=10)).isoformat()
        attempts = 0
    if row:
        q('UPDATE login_attempts SET attempts=?, locked_until=? WHERE email=?',(attempts, locked, email))
    else:
        q('INSERT INTO login_attempts(email,attempts,locked_until) VALUES(?,?,?)',(email,attempts,locked))

def clear_failed(email):
    if q('SELECT * FROM login_attempts WHERE email=?',(email,),True):
        q('UPDATE login_attempts SET attempts=0, locked_until="" WHERE email=?',(email,))

def login_required(fn):
    @wraps(fn)
    def wrap(*a,**kw):
        if not user(): return redirect('/login')
        u=user();
        if request.path.startswith('/professor') and u['valid_until'] and u['valid_until'] < datetime.now().date().isoformat(): return redirect('/expirada')
        return fn(*a,**kw)
    return wrap

def admin_required(fn):
    @wraps(fn)
    def wrap(*a,**kw):
        u=user()
        if not u: return redirect('/login')
        if not u['is_admin']: return 'Acesso negado',403
        return fn(*a,**kw)
    return wrap

def render(content, title='AulaPronta Pro'):
    u=user()
    return render_template_string(BASE_HTML, content=content, title=title, u=u)


def safe_int(value, default=0, minimum=None, maximum=None):
    try:
        n = int(value)
    except Exception:
        n = default
    if minimum is not None:
        n = max(minimum, n)
    if maximum is not None:
        n = min(maximum, n)
    return n

def esc(x):
    return html.escape(str(x or ''), quote=True)

def safe_pre(x):
    return esc(x)

BASE_HTML='''<!doctype html>
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
    <div><h1>AulaPronta</h1><p>Pro Web v2.3</p></div>
  </div>
  <nav>
    <a href="/professor"><span>IN</span>Início</a>
    <a href="/professor/atividade"><span>AT</span>Criar Atividade</a>
    <a href="/professor/avaliacao"><span>AV</span>Criar Avaliação</a>
    <a href="/professor/plano"><span>PL</span>Planejar Aula</a>
    <a href="/professor/parecer"><span>PR</span>Pareceres</a>
    <a href="/professor/materiais"><span>MT</span>Materiais</a>
    <a href="/perfil"><span>ES</span>Minha Escola</a>
    {% if u.is_admin %}<a href="/admin"><span>AD</span>Painel Admin</a>{% endif %}
    <a href="/logout"><span>SA</span>Sair</a>
  </nav>
  <div class="profile">
    {% if u.avatar %}<img class="avatar" src="{{u.avatar}}">{% else %}<div class="avatar-text">AP</div>{% endif %}
    <strong>{{u.name}}</strong>
    <p class="muted">Plano {{u.plan}} • até {{u.valid_until}}</p>
  </div>
</aside>
<main class="main">
{% with messages = get_flashed_messages() %}
  {% if messages %}{% for m in messages %}<div class="msg">{{m}}</div>{% endfor %}{% endif %}
{% endwith %}
{{content|safe}}
</main>
</div>
{% else %}
<main class="auth">{{content|safe}}</main>
{% endif %}
<script src="/static/app.js"></script>
<script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/service-worker.js").catch(()=>{});}</script>
</body>
</html>'''

def options(rows, val='id', label='name'):
    return ''.join([f'<option value="{esc(r[val])}">{esc(r[label])}</option>' for r in rows])

def selector(extra=''):
    return f'''<div class="wizard">
      <div class="step active"><b>1</b><span>Turma</span></div>
      <div class="step active"><b>2</b><span>Matéria</span></div>
      <div class="step active"><b>3</b><span>Conteúdo</span></div>
      <div class="step"><b>4</b><span>Gerar</span></div>
    </div>
    <div class="grid premium-selects">
      <p><label>Matéria</label><select name="subject" id="subject">{options(q('SELECT * FROM subjects ORDER BY name'))}</select></p>
      <p><label>Turma / Ano</label><select name="grade" id="grade">{options(q('SELECT * FROM grades ORDER BY ord'))}</select></p>
      <p><label>Conteúdo</label><select name="topic" id="topic"></select><small id="topicHelp" class="field-help">Escolha matéria e turma para carregar os conteúdos.</small></p>
      <p><label>Nível</label><select name="difficulty"><option>Todas</option><option>Fácil</option><option>Média</option><option>Difícil</option></select></p>
      {extra}
    </div><script>window.addEventListener('load',()=>setupTopics())</script>'''

def get_sel():
    try:
        subject_id = int(request.form.get('subject','0'))
        grade_id = int(request.form.get('grade','0'))
        topic_id = int(request.form.get('topic','0'))
    except Exception:
        return None, None, None
    sub=q('SELECT * FROM subjects WHERE id=?',(subject_id,),True)
    gr=q('SELECT * FROM grades WHERE id=?',(grade_id,),True)
    top=q('SELECT * FROM topics WHERE id=? AND subject_id=? AND grade_id=?',(topic_id,subject_id,grade_id),True)
    return sub,gr,top

def material_insert(uid,typ,title,student,teacher=''):
    return insert('INSERT INTO materials(user_id,type,title,student,teacher,created_at) VALUES(?,?,?,?,?,?)',(uid,typ,title,student,teacher,datetime.now().isoformat()))

def build_questions(sub,gr,top,count,diff='Todas',types=None):
    if not (sub and gr and top):
        return []
    sql='SELECT * FROM questions WHERE subject_id=? AND grade_id=? AND topic_id=? AND active=1'; args=[sub['id'],gr['id'],top['id']]
    if diff!='Todas': sql+=' AND difficulty=?'; args.append(diff)
    if types: sql += ' AND type IN (%s)'%(','.join(['?']*len(types))); args += types
    rows=list(q(sql,args)); random.shuffle(rows); return rows[:safe_int(count, 10, 1, 60)]

def q_student(qq,n):
    s=f"{n}. {qq['statement']}\n   {qq['command']}\n"
    if qq['type']=='MULTIPLA':
        for a in q('SELECT * FROM alternatives WHERE question_id=? ORDER BY letter',(qq['id'],)): s+=f"   {a['letter']}) {a['text']}\n"
    elif qq['type']=='VF': s+='   (   ) Verdadeiro     (   ) Falso\n'
    else: s+='   Resposta: ________________________________________________\n   __________________________________________________________\n'
    return s

def q_teacher(qq,n): return f"{n}. {qq['statement']}\n   Resposta: {qq['answer']}\n   Explicação: {qq['explanation']}\n"

def header(u,sub,gr,title): return f"ESCOLA: {u['school'] or '________________'}\nPROFESSOR(A): {u['name']}\nALUNO(A): ________________________________________________\nTURMA: {gr['name']}    DATA: ___/___/____\nDISCIPLINA: {sub['name']}\n\n{title.upper()}\n\n"

# ---------------- Routes ----------------
@app.route('/')
def home(): return redirect('/professor' if user() else '/login')
@app.route('/login',methods=['GET','POST'])
def login_page():
    if request.method=='POST':
        email=request.form.get('email','').lower().strip()
        if is_locked(email):
            flash('Muitas tentativas erradas. Tente novamente em alguns minutos.')
            return redirect('/login')
        u=q('SELECT * FROM users WHERE email=?',(email,),True)
        if u and check_password_hash(u['password'],request.form.get('password','')):
            clear_failed(email)
            session['uid']=u['id']; return redirect('/professor')
        record_failed(email)
        flash('E-mail ou senha inválidos.')
    return render('<section class="auth-card"><div class="logo">AP</div><h1>Entrar</h1><form method="post"><p><label>E-mail</label><input name="email"></p><p><label>Senha</label><input name="password" type="password"></p><button class="btn primary">Entrar</button></form><a class="btn" href="/cadastro">Cadastrar com serial</a></section>','Login')
@app.route('/cadastro',methods=['GET','POST'])
def cadastro():
    if request.method=='POST':
        code=request.form.get('serial','').upper().strip(); s=q('SELECT * FROM serials WHERE code=? AND active=1 AND used=0',(code,),True)
        if not s: flash('Serial inválido ou já usado.'); return redirect('/cadastro')
        if request.form.get('password','')!=request.form.get('password2',''): flash('As senhas não conferem.'); return redirect('/cadastro')
        email=request.form.get('email','').lower().strip()
        if not email or '@' not in email or len(request.form.get('password','')) < 4:
            flash('Informe e-mail válido e senha com pelo menos 4 caracteres.'); return redirect('/cadastro')
        if q('SELECT id FROM users WHERE email=?',(email,),True): flash('Já existe conta com este e-mail.'); return redirect('/cadastro')
        valid=(datetime.now()+timedelta(days=s['days'])).date().isoformat()
        uid=insert('INSERT INTO users(name,email,password,is_admin,plan,valid_until) VALUES(?,?,?,?,?,?)',(request.form.get('name','Professor(a)'),email,generate_password_hash(request.form.get('password','')),0,s['plan'],valid))
        q('UPDATE serials SET used=1,used_by=?,used_at=? WHERE id=?',(uid,datetime.now().isoformat(),s['id']))
        flash('Cadastro ativado. Faça login.'); return redirect('/login')
    return render('<section class="auth-card"><div class="logo">AP</div><h1>Cadastro</h1><form method="post"><p><label>Nome do professor</label><input name="name" required></p><p><label>E-mail</label><input name="email" required></p><p><label>Senha</label><input type="password" name="password" required></p><p><label>Confirmar senha</label><input type="password" name="password2" required></p><p><label>Serial</label><input name="serial" required></p><button class="btn primary">Cadastrar</button></form><a class="btn" href="/login">Voltar</a></section>','Cadastro')
@app.route('/logout')
def logout_page(): session.clear(); return redirect('/login')
@app.route('/expirada')
def expirada(): return render('<div class="panel"><h1>Assinatura expirada</h1><p>Fale com o administrador para renovar.</p><a class="btn" href="/logout">Sair</a></div>')
@app.route('/perfil',methods=['GET','POST'])
@login_required
def perfil():
    u=user()
    if request.method=='POST':
        q('UPDATE users SET name=?, school=?, city=?, state=?, avatar=? WHERE id=?',(request.form.get('name',''),request.form.get('school',''),request.form.get('city',''),request.form.get('state','')[:2],request.form.get('avatar',''),u['id']))
        flash('Perfil salvo.'); return redirect('/perfil')
    u=user(); return render(f'''<div class="header"><div><span>AulaPronta Pro</span><h1>Minha Escola</h1><p>Dados usados no cabeçalho.</p></div></div><div class="panel"><form method="post"><div class="grid"><p><label>Nome do professor</label><input name="name" value="{u['name'] or ''}"></p><p><label>Nome da escola</label><input name="school" value="{u['school'] or ''}"></p><p><label>Cidade</label><input name="city" value="{u['city'] or ''}"></p><p><label>UF</label><input name="state" value="{u['state'] or ''}"></p></div><p><label>URL da imagem do perfil</label><input name="avatar" value="{u['avatar'] or ''}" placeholder="https://..."></p><button class="btn primary">Salvar</button></form></div>''')

@app.route('/professor')
@login_required
def dashboard():
    u=user(); cards=f'''<div class="cards"><div class="card"><small>Questões</small><strong>{q('SELECT COUNT(*) c FROM questions',one=True)['c']}</strong><p>atividades e provas</p></div><div class="card"><small>Conteúdos</small><strong>{q('SELECT COUNT(*) c FROM topics',one=True)['c']}</strong><p>por turma</p></div><div class="card"><small>Materiais</small><strong>{q('SELECT COUNT(*) c FROM materials WHERE user_id=?',(u['id'],),one=True)['c']}</strong><p>gerados por você</p></div><div class="card"><small>Plano</small><strong>{u['plan']}</strong><p>até {u['valid_until']}</p></div></div>'''
    actions='''<div class="panel"><h2>O que você quer preparar hoje?</h2><a class="action" href="/professor/atividade"><b>Criar uma atividade</b><span>Folha do aluno com questões e gabarito.</span></a><a class="action" href="/professor/avaliacao"><b>Criar uma avaliação</b><span>Prova com questões objetivas e discursivas.</span></a><a class="action" href="/professor/plano"><b>Planejar uma aula</b><span>Plano de aula completo.</span></a><a class="action" href="/professor/parecer"><b>Escrever parecer</b><span>Relatório pedagógico com intervenções.</span></a></div>'''
    return render(f'<div class="header"><div><span>AulaPronta Pro Web</span><h1>Início</h1><p>Sistema online para preparar materiais escolares.</p></div></div>{cards}{actions}')

@app.route('/api/topics')
@app.route('/api/topicos')
@login_required
def api_topicos():
    rows=q('SELECT id,name FROM topics WHERE subject_id=? AND grade_id=? ORDER BY name',(request.args.get('subject'),request.args.get('grade')))
    return jsonify([dict(r) for r in rows])

def form_selector(extra=''):
    return f"""<div class="wizard">
      <div class="step active"><b>1</b><span>Turma</span></div>
      <div class="step active"><b>2</b><span>Matéria</span></div>
      <div class="step active"><b>3</b><span>Conteúdo</span></div>
      <div class="step"><b>4</b><span>Gerar</span></div>
    </div>
    <div class="grid premium-selects">
      <p><label>Matéria</label><select name="subject" id="subject">{options(q('SELECT * FROM subjects ORDER BY name'))}</select></p>
      <p><label>Turma / Ano</label><select name="grade" id="grade">{options(q('SELECT * FROM grades ORDER BY ord'))}</select></p>
      <p><label>Conteúdo</label><select name="topic" id="topic"></select><small id="topicHelp" class="field-help">Escolha matéria e turma para carregar os conteúdos.</small></p>
      <p><label>Nível</label><select name="difficulty"><option>Todas</option><option>Fácil</option><option>Média</option><option>Difícil</option></select></p>
    </div>
    <div class="options-row">{extra}</div>
    <script>window.addEventListener('load',()=>setupTopics())</script>"""

@app.route('/professor/atividade',methods=['GET','POST'])
@login_required
def atividade():
    if request.method=='POST':
        u=user(); sub,gr,top=get_sel()
        if not (sub and gr and top):
            flash('Escolha matéria, turma e conteúdo válidos.')
            return redirect('/professor/atividade')
        qs=build_questions(sub,gr,top,request.form.get('quantity',10),request.form.get('difficulty','Todas'))
        student=header(u,sub,gr,f'Atividade de {top["name"]}')
        if request.form.get('text'):
            tx=q('SELECT * FROM texts WHERE topic_id=? ORDER BY RANDOM() LIMIT 1',(top['id'],),one=True)
            if tx: student+=f"{tx['title']}\n{tx['body']}\n\n"
        student+='Instruções: leia com atenção e responda às questões.\n\n'; teacher=f'GABARITO - {sub["name"]} - {gr["name"]}\n\n'
        for i,qq in enumerate(qs,1): student+=q_student(qq,i)+'\n'; teacher+=q_teacher(qq,i)+'\n'
        mid=material_insert(u['id'],'Atividade',f'Atividade de {top["name"]}',student,teacher); return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Criar Atividade</h1><p>Atividade completa com texto de apoio e gabarito.</p></div></div><div class="panel"><form method="post">'+form_selector('<p class="quantity"><label>Quantidade</label><input name="quantity" type="number" value="10" min="1" max="40"></p><label class="toggle"><input type="checkbox" name="text" checked><span>Adicionar texto de apoio</span></label>')+'<div class="preview-note"><b>O que será gerado:</b> cabeçalho, questões numeradas, folha do aluno e gabarito do professor.</div><button class="btn primary big">Gerar atividade agora</button></form></div>')

@app.route('/professor/avaliacao',methods=['GET','POST'])
@login_required
def avaliacao():
    if request.method=='POST':
        u=user(); sub,gr,top=get_sel()
        if not (sub and gr and top):
            flash('Escolha matéria, turma e conteúdo válidos.')
            return redirect('/professor/avaliacao')
        total=safe_int(request.form.get('quantity',10),10,1,60); obj=safe_int(request.form.get('obj',5),5,0,60); diff=request.form.get('difficulty','Todas')
        qs=build_questions(sub,gr,top,obj,diff,['MULTIPLA'])+build_questions(sub,gr,top,max(0,total-obj),diff,['DISCURSIVA','VF','LACUNAS'])
        student=header(u,sub,gr,f'Avaliação de {top["name"]}')+'Orientações: leia com atenção e responda com letra legível.\n\n'; teacher=f'GABARITO - {sub["name"]} - {gr["name"]}\n\n'
        for i,qq in enumerate(qs[:total],1): student+=q_student(qq,i)+'\n'; teacher+=q_teacher(qq,i)+'\n'
        mid=material_insert(u['id'],'Avaliação',f'Avaliação de {top["name"]}',student,teacher); return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Criar Avaliação</h1><p>Prova com gabarito separado.</p></div></div><div class="panel"><form method="post">'+form_selector('<p class="quantity"><label>Total de questões</label><input name="quantity" type="number" value="10" min="1" max="40"></p><p class="quantity"><label>Questões de marcar</label><input name="obj" type="number" value="5" min="0" max="40"></p>')+'<div class="preview-note"><b>Dica:</b> use questões objetivas e discursivas para uma avaliação equilibrada.</div><button class="btn primary big">Gerar avaliação agora</button></form></div>')

@app.route('/professor/plano',methods=['GET','POST'])
@login_required
def plano():
    if request.method=='POST':
        u=user(); sub,gr,top=get_sel()
        if not (sub and gr and top):
            flash('Escolha matéria, turma e conteúdo válidos.')
            return redirect('/professor/plano')
        pl=q('SELECT * FROM lessons WHERE topic_id=? ORDER BY RANDOM() LIMIT 1',(top['id'],),one=True)
        if not pl:
            txt=f'''PLANO DE AULA

Disciplina: {sub['name']}
Turma: {gr['name']}
Tema: {top['name']}
Duração: 50 minutos

Objetivo:
Compreender e aplicar conhecimentos relacionados ao tema.
'''
        else:
            txt=f'''PLANO DE AULA\n\nTítulo: {pl['title']}\nDisciplina: {sub['name']}\nTurma: {gr['name']}\nTema: {top['name']}\nDuração: {pl['duration']}\n\nObjetivo:\n{pl['objective']}\n\nMetodologia:\n{pl['methodology']}\n\nRecursos:\n{pl['resources']}\n\nDesenvolvimento:\n{pl['development']}\n\nAvaliação:\n{pl['evaluation']}\n\nTarefa:\n{pl['homework']}\n'''
        mid=material_insert(u['id'],'Plano de aula',f'Plano de aula - {top["name"]}',txt,''); return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Planejar Aula</h1><p>Plano de aula completo.</p></div></div><div class="panel"><form method="post">'+form_selector()+'<div class="preview-note"><b>O plano inclui:</b> objetivo, metodologia, recursos, desenvolvimento, avaliação e tarefa.</div><button class="btn primary big">Gerar plano de aula</button></form></div>')

@app.route('/professor/parecer',methods=['GET','POST'])
@login_required
def parecer():
    if request.method=='POST':
        u=user(); aluno=request.form.get('student','Aluno(a)'); sit=request.form.get('situation','bom')
        frases={'excelente':'apresenta excelente participação e autonomia.','bom':'participa das atividades propostas e demonstra interesse.','regular':'participa quando solicitado, mas precisa ampliar autonomia e constância.','dificuldade':'apresenta dificuldades e necessita de acompanhamento mais próximo.'}
        txt=f'''RELATÓRIO PEDAGÓGICO\n\nAluno(a): {aluno}\nProfessor(a): {u['name']}\n\nParecer:\nO(a) estudante {frases.get(sit,frases['bom'])}\n\nSugestões de intervenção:\n- Retomar conteúdos com exemplos práticos.\n- Propor atividades graduadas.\n- Acompanhar leitura de enunciados e organização das respostas.\n'''
        mid=material_insert(u['id'],'Parecer',f'Parecer - {aluno}',txt,''); return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Pareceres</h1><p>Relatórios pedagógicos.</p></div></div><div class="panel"><form method="post"><div class="grid"><p><label>Nome do aluno</label><input name="student" value="Aluno(a)"></p><p><label>Situação</label><select name="situation"><option value="excelente">Excelente</option><option value="bom" selected>Bom</option><option value="regular">Regular</option><option value="dificuldade">Dificuldade</option></select></p></div><button class="btn primary">Gerar parecer</button></form></div>')

@app.route('/professor/materiais')
@login_required
def materiais():
    rows=q('SELECT * FROM materials WHERE user_id=? ORDER BY id DESC',(user()['id'],)); html='<div class="header"><div><span>AulaPronta Pro</span><h1>Materiais</h1><p>Histórico de materiais gerados.</p></div></div><div class="panel">'
    for m in rows: html+=f'<a class="action" href="/professor/material/{m["id"]}"><b>{esc(m["type"])} — {esc(m["title"])}</b><span>{esc(m["created_at"])}</span></a>'
    html+='</div>'; return render(html)

@app.route('/professor/material/<int:mid>')
@login_required
def material(mid):
    m=q('SELECT * FROM materials WHERE id=? AND user_id=?',(mid,user()['id']),True)
    if not m:
        flash('Material não encontrado ou não pertence a esta conta.')
        return redirect('/professor/materiais')
    teacher_html = f'<h2>Folha do professor</h2><pre>{safe_pre(m["teacher"])}</pre>' if m['teacher'] else ''
    return render(f'<div class="header"><div><span>{esc(m["type"])}</span><h1>{esc(m["title"])}</h1><p>{esc(m["created_at"])}</p></div><a class="btn primary" target="_blank" href="/professor/material/{mid}/print">Exportar HTML / PDF</a></div><div class="panel"><h2>Folha do aluno</h2><pre>{safe_pre(m["student"])}</pre>{teacher_html}</div>')

@app.route('/professor/material/<int:mid>/print')
@login_required
def material_print(mid):
    m=q('SELECT * FROM materials WHERE id=? AND user_id=?',(mid,user()['id']),True)
    if not m:
        return '<h1>Material não encontrado</h1><p>Volte ao painel e escolha um material válido.</p>', 404
    teacher_page = f'<div class="page"><h1>Folha do professor</h1><pre>{safe_pre(m["teacher"])}</pre></div>' if m['teacher'] else ''
    css = 'body{font-family:Arial;background:#f3f4f6;padding:24px}.page{background:white;max-width:900px;margin:0 auto 24px;padding:36px;box-shadow:0 4px 18px #0002}pre{white-space:pre-wrap;font-family:Arial;line-height:1.55}button{position:fixed;right:20px;top:20px;background:#d4a84f;border:0;padding:12px;font-weight:bold}@media print{button{display:none}body{background:white;padding:0}.page{box-shadow:none;page-break-after:always}}'
    return '<!doctype html><html><head><meta charset="utf-8"><title>'+esc(m['title'])+'</title><style>'+css+'</style></head><body><button onclick="window.print()">Imprimir / Salvar PDF</button><div class="page"><h1>'+esc(m['title'])+'</h1><pre>'+safe_pre(m['student'])+'</pre></div>'+teacher_page+'</body></html>'

@app.route('/admin')
@admin_required
def admin(): return render(f'<div class="header"><div><span>Admin</span><h1>Painel Administrativo</h1><p>Controle do SaaS.</p></div></div><div class="cards"><div class="card"><small>Usuários</small><strong>{q("SELECT COUNT(*) c FROM users",one=True)["c"]}</strong></div><div class="card"><small>Seriais</small><strong>{q("SELECT COUNT(*) c FROM serials",one=True)["c"]}</strong></div><div class="card"><small>Questões</small><strong>{q("SELECT COUNT(*) c FROM questions",one=True)["c"]}</strong></div></div><div class="panel"><a class="btn primary" href="/admin/seriais">Gerar seriais</a><a class="btn" href="/admin/usuarios">Ver usuários</a><a class="btn" href="/admin/checkup">Rodar checkup</a></div>')

@app.route('/admin/checkup')
@admin_required
def admin_checkup():
    reset_pedagogico(); seed()
    flash('Checkup concluído. Banco pedagógico reconstruído com IDs corretos.')
    return redirect('/admin')

@app.route('/admin/seriais',methods=['GET','POST'])
@admin_required
def admin_seriais():
    novos=[]
    if request.method=='POST':
        for _ in range(safe_int(request.form.get('quantity',1),1,1,100)):
            code=serial_code(); q('INSERT INTO serials(code,plan,days,created_at) VALUES(?,?,?,?)',(code,request.form.get('plan','PROFESSOR'),safe_int(request.form.get('days',30),30,1,3650),datetime.now().isoformat())); novos.append(code)
    rows=q('SELECT * FROM serials ORDER BY id DESC LIMIT 200'); html='<div class="header"><div><span>Admin</span><h1>Gerar Seriais</h1><p>Cadastro dos professores só funciona com serial.</p></div></div><div class="panel"><form method="post"><div class="grid"><p><label>Plano</label><select name="plan"><option>TESTE</option><option selected>PROFESSOR</option><option>PREMIUM</option><option>ESCOLA</option></select></p><p><label>Dias</label><input name="days" value="30"></p><p><label>Quantidade</label><input name="quantity" value="1"></p></div><button class="btn primary">Gerar</button></form></div>'
    if novos: html+='<div class="panel"><h2>Novos seriais</h2>'+''.join([f'<pre>{esc(x)}</pre>' for x in novos])+'</div>'
    html+='<div class="panel table"><table><tr><th>Serial</th><th>Plano</th><th>Dias</th><th>Usado</th></tr>'+''.join([f'<tr><td><code>{esc(r["code"])}</code></td><td>{esc(r["plan"])}</td><td>{r["days"]}</td><td>{"Sim" if r["used"] else "Não"}</td></tr>' for r in rows])+'</table></div>'
    return render(html)

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    rows=q('SELECT * FROM users ORDER BY id DESC'); html='<div class="header"><div><span>Admin</span><h1>Usuários</h1><p>Professores cadastrados.</p></div></div><div class="panel table"><table><tr><th>Nome</th><th>E-mail</th><th>Plano</th><th>Validade</th><th>Admin</th></tr>'
    html+=''.join([f'<tr><td>{esc(r["name"])}</td><td>{esc(r["email"])}</td><td>{esc(r["plan"])}</td><td>{esc(r["valid_until"])}</td><td>{"Sim" if r["is_admin"] else "Não"}</td></tr>' for r in rows])+'</table></div>'
    return render(html)


@app.route('/manifest.webmanifest')
def manifest():
    return jsonify({
        "name":"AulaPronta Pro",
        "short_name":"AulaPronta",
        "start_url":"/",
        "display":"standalone",
        "background_color":"#0B0F17",
        "theme_color":"#D4A84F",
        "description":"Sistema online para professores criarem atividades, avaliações, planos e pareceres.",
        "icons":[
            {"src":"/static/icons/icon-192.png","sizes":"192x192","type":"image/png"},
            {"src":"/static/icons/icon-512.png","sizes":"512x512","type":"image/png"}
        ]
    })

@app.route('/service-worker.js')
def service_worker():
    js = """const CACHE_NAME='aulapronta-pro-v231-checkup';const OFFLINE_URL='/offline';self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll([OFFLINE_URL,'/static/style.css','/static/app.js'])))});self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(fetch(e.request).catch(()=>caches.match(e.request).then(r=>r||caches.match(OFFLINE_URL))))});"""
    return app.response_class(js, mimetype='application/javascript')

@app.route('/offline')
def offline():
    return render('<div class="auth-card"><div class="auth-logo">AP</div><h1>Sem conexão</h1><p>O AulaPronta Pro precisa de internet para login, banco e assinatura.</p><a class="btn primary" href="/">Tentar novamente</a></div>','Offline')


# ---------------- V2.3 BANCO PREMIUM E PERSONALIZAÇÃO ----------------
PED_VERSION_PREMIUM = 'v2.3-banco-premium-personalizado'

def premium_cols(table):
    try:
        return {r['name'] for r in q(f'PRAGMA table_info({table})')}
    except Exception:
        return set()

def premium_add_col(table, col, ddl):
    if col not in premium_cols(table):
        q(f'ALTER TABLE {table} ADD COLUMN {ddl}')

def premium_upgrade_schema():
    q("CREATE TABLE IF NOT EXISTS app_meta(key TEXT PRIMARY KEY, value TEXT)")
    premium_add_col('users','teaching_style',"teaching_style TEXT DEFAULT 'Acolhedor e simples'")
    premium_add_col('users','local_context',"local_context TEXT DEFAULT ''")
    premium_add_col('users','default_instructions',"default_instructions TEXT DEFAULT ''")
    premium_add_col('grades','stage',"stage TEXT DEFAULT ''")
    premium_add_col('topics','bncc',"bncc TEXT DEFAULT ''")
    premium_add_col('questions','skill',"skill TEXT DEFAULT ''")
    premium_add_col('questions','context',"context TEXT DEFAULT ''")

def premium_stage(g):
    if g in ['Pré I','Pré II']: return 'Educação Infantil'
    if g in ['1º ano','2º ano','3º ano','4º ano','5º ano']: return 'Ensino Fundamental I'
    if g in ['6º ano','7º ano','8º ano','9º ano']: return 'Ensino Fundamental II'
    if 'EM' in g: return 'Ensino Médio'
    if 'EJA' in g: return 'EJA'
    return 'Geral'

def premium_applicable(grade):
    if grade in ['Pré I','Pré II']:
        return ['Alfabetização','Matemática','Arte','Educação Física','Projeto de Vida']
    if grade in ['1º ano','2º ano']:
        return ['Alfabetização','Língua Portuguesa','Matemática','Ciências','História','Geografia','Arte','Educação Física','Ensino Religioso','Tecnologia e Informática']
    if grade in ['3º ano','4º ano','5º ano']:
        return ['Língua Portuguesa','Redação','Matemática','Ciências','História','Geografia','Arte','Educação Física','Ensino Religioso','Tecnologia e Informática','Projeto de Vida']
    if grade in ['6º ano','7º ano','8º ano','9º ano']:
        return ['Língua Portuguesa','Redação','Matemática','Ciências','História','Geografia','Arte','Educação Física','Língua Inglesa','Ensino Religioso','Tecnologia e Informática','Projeto de Vida']
    if 'EM' in grade:
        return ['Língua Portuguesa','Redação','Matemática','Física','Química','Biologia','História','Geografia','Sociologia','Filosofia','Língua Inglesa','Arte','Educação Física','Projeto de Vida','Tecnologia e Informática']
    if grade == 'EJA Médio':
        return ['Língua Portuguesa','Redação','Matemática','Física','Química','Biologia','História','Geografia','Sociologia','Filosofia','Projeto de Vida','Tecnologia e Informática','Arte']
    return ['Alfabetização','Língua Portuguesa','Matemática','Ciências','História','Geografia','Arte','Projeto de Vida','Tecnologia e Informática','Ensino Religioso']

def premium_topics():
    return {
        'Alfabetização':['Vogais','Consoantes','Sílabas simples','Sílabas complexas','Nome próprio','Rimas','Leitura de frases','Formação de palavras','Escrita espontânea','Alfabeto','Numerais','Lista de palavras'],
        'Língua Portuguesa':['Leitura e interpretação','Produção textual','Pontuação','Ortografia','Gêneros textuais','Classes de palavras','Sinônimos e antônimos','Coesão textual','Concordância','Literatura','Oralidade','Resumo'],
        'Redação':['Parágrafo','Introdução','Desenvolvimento','Conclusão','Tese e argumento','Coesão e coerência','Carta argumentativa','Crônica','Artigo de opinião','Revisão textual','Texto dissertativo','Narrativa'],
        'Matemática':['Números naturais','Operações fundamentais','Problemas matemáticos','Frações','Números decimais','Porcentagem','Grandezas e medidas','Geometria plana','Perímetro e área','Probabilidade','Estatística','Equações'],
        'Ciências':['Seres vivos','Corpo humano','Água','Solo','Ar','Meio ambiente','Saúde e higiene','Energia','Reciclagem','Astronomia','Cadeia alimentar','Tecnologia e ciência'],
        'História':['Tempo histórico','Fontes históricas','Povos indígenas','África e Brasil','Brasil Colônia','Independência do Brasil','República','Cidadania','Patrimônio cultural','Direitos humanos','Trabalho e sociedade'],
        'Geografia':['Lugar e paisagem','Mapas e orientação','Campo e cidade','Clima','Relevo','População','Regiões do Brasil','Meio ambiente','Globalização','Território','Migração','Cartografia'],
        'Arte':['Cores e formas','Artes visuais','Música','Teatro','Dança','Cultura brasileira','Leitura de imagem','Arte no cotidiano','Patrimônio artístico','Arte indígena','Arte africana','Fotografia'],
        'Educação Física':['Jogos e brincadeiras','Esportes coletivos','Ginástica','Danças','Saúde e movimento','Cooperação','Lutas','Atletismo','Alongamento','Respeito às regras'],
        'Língua Inglesa':['Vocabulário básico','Cumprimentos','Números e cores','Family','School objects','Food','Simple present','Verbo to be','Days of the week','Reading comprehension'],
        'Física':['Movimento','Velocidade','Força','Energia','Calor','Ondas','Eletricidade','Óptica','Leis de Newton','Trabalho e potência'],
        'Química':['Matéria','Misturas','Átomos','Tabela periódica','Ligações químicas','Reações químicas','Funções químicas','Soluções','pH','Química no cotidiano'],
        'Biologia':['Citologia','Genética','Ecologia','Evolução','Fisiologia humana','Botânica','Zoologia','Microbiologia','Sustentabilidade','Biotecnologia'],
        'Sociologia':['Cultura','Sociedade','Trabalho','Desigualdade social','Cidadania','Movimentos sociais','Instituições sociais','Mídia e sociedade','Juventude','Diversidade'],
        'Filosofia':['Ética','Conhecimento','Política','Lógica','Liberdade','Filosofia antiga','Cidadania','Estética','Argumentação','Existência'],
        'Projeto de Vida':['Autoconhecimento','Organização pessoal','Profissões','Metas','Cidadania','Educação financeira','Projeto de futuro','Comunicação','Trabalho em equipe','Tomada de decisão'],
        'Tecnologia e Informática':['Partes do computador','Digitação','Internet segura','Editor de texto','Planilhas','Pensamento computacional','Algoritmos','Cidadania digital','Pesquisa online','Apresentações'],
        'Ensino Religioso':['Valores','Convivência','Respeito','Solidariedade','Diversidade cultural','Tradições religiosas','Ética e diálogo','Cultura de paz']}

def premium_area(name):
    if name in ['Língua Portuguesa','Redação','Língua Inglesa','Arte','Educação Física','Alfabetização']: return 'Linguagens'
    if name == 'Matemática': return 'Matemática'
    if name in ['Ciências','Física','Química','Biologia']: return 'Ciências da Natureza'
    if name in ['História','Geografia','Sociologia','Filosofia','Ensino Religioso']: return 'Ciências Humanas'
    if name == 'Tecnologia e Informática': return 'Tecnologia'
    return 'Formação Geral'

def premium_skill(stage, subject, theme):
    if stage == 'Educação Infantil': return f'Explorar {theme.lower()} por meio de oralidade, brincadeiras, percepção visual e registros simples.'
    if stage == 'Ensino Fundamental I': return f'Reconhecer, registrar e aplicar conhecimentos de {theme.lower()} em situações do cotidiano escolar.'
    if stage == 'Ensino Fundamental II': return f'Analisar e resolver situações relacionadas a {theme.lower()}, justificando respostas com clareza.'
    if stage == 'Ensino Médio': return f'Interpretar, argumentar e aplicar conceitos de {theme.lower()} em situações-problema contextualizadas.'
    if stage == 'EJA': return f'Relacionar {theme.lower()} com experiências de vida, trabalho, família e comunidade, sem infantilizar a linguagem.'
    return f'Compreender {theme.lower()} e aplicar o conhecimento em atividades orientadas.'

def premium_context(stage, subject, theme):
    if stage == 'Educação Infantil': return f'Observe uma situação da sala, das brincadeiras ou das imagens apresentadas sobre {theme}.'
    if stage == 'Ensino Fundamental I': return f'Pense em uma situação da escola, da família ou do bairro envolvendo {theme}.'
    if stage == 'Ensino Fundamental II': return f'Considere uma situação do cotidiano, da tecnologia ou da comunidade relacionada a {theme}.'
    if stage == 'Ensino Médio': return f'Analise uma situação social, científica ou cultural relacionada a {theme}.'
    if stage == 'EJA': return f'Relacione {theme} com experiências de trabalho, compras, transporte, família, saúde ou comunidade.'
    return f'Analise uma situação relacionada a {theme}.'

def premium_statement(stage, subject, theme, typ):
    base = premium_context(stage, subject, theme)
    if typ == 'MULTIPLA': return f'{base} Assinale a alternativa que melhor representa uma ideia correta sobre {theme}.'
    if typ == 'VF': return f'{base} Julgue a afirmação sobre {theme} como verdadeira ou falsa.'
    if typ == 'LACUNAS': return f'Complete: O estudo de {theme} ajuda a compreender ______________________________.'
    if typ == 'TEXTO': return f'Produza um texto curto relacionando {theme} com uma situação real. Organize começo, desenvolvimento e conclusão.'
    return f'{base} Explique, com suas palavras, um conceito importante relacionado a {theme}.'

def premium_command(stage, typ):
    if typ == 'MULTIPLA': return 'Leia todas as alternativas antes de marcar a resposta.'
    if typ == 'VF': return 'Marque V para verdadeiro ou F para falso e, quando possível, justifique oralmente.'
    if typ == 'LACUNAS': return 'Complete a lacuna com uma palavra ou expressão adequada.'
    if typ == 'TEXTO': return 'Escreva com clareza, usando exemplos e respeitando o tema proposto.'
    return 'Responda com suas palavras, usando uma ideia completa.'

def premium_answer(typ, theme):
    if typ == 'MULTIPLA': return 'Alternativa A.'
    if typ == 'VF': return 'Depende da afirmação apresentada; considerar verdadeiro quando estiver de acordo com o conteúdo.'
    if typ == 'LACUNAS': return f'Resposta coerente com {theme}, respeitando o sentido da frase.'
    if typ == 'TEXTO': return 'Produção pessoal coerente, com começo, desenvolvimento e conclusão.'
    return f'Resposta pessoal conceitualmente correta sobre {theme}.'

def premium_support(stage, subject, theme):
    if stage == 'EJA': return f'{theme} aparece em situações da vida adulta, como trabalho, compras, transporte, saúde, documentos, família e comunidade. Estudar esse conteúdo ajuda a interpretar informações e tomar decisões com mais segurança.'
    if stage == 'Educação Infantil': return f'Vamos observar, conversar e brincar com o tema {theme}. A criança aprende quando fala, escuta, compara, registra, movimenta-se e participa com curiosidade.'
    if stage == 'Ensino Médio': return f'O tema {theme} permite analisar situações sociais, científicas e culturais com maior profundidade, interpretando informações, comparando ideias e justificando respostas.'
    return f'O tema {theme} ajuda a compreender melhor situações da escola, da família e da comunidade. Ao estudar esse conteúdo, o aluno observa exemplos, responde perguntas e explica o que aprendeu com suas palavras.'

def premium_methodology(stage):
    if stage == 'EJA': return 'Conversa inicial com experiências dos estudantes, explicação objetiva, exemplos práticos, atividade orientada e socialização.'
    if stage == 'Educação Infantil': return 'Roda de conversa, exploração visual, brincadeira dirigida, registro simples e interação coletiva.'
    if stage == 'Ensino Médio': return 'Problematização inicial, análise de exemplo, explicação conceitual, atividade individual ou em grupo e debate final.'
    return 'Aula dialogada, levantamento de conhecimentos prévios, explicação com exemplos, atividade prática e correção coletiva.'

def premium_development(stage, subject, theme):
    return f'1. Acolhida e apresentação do tema {theme}.\n2. Levantamento do que a turma já sabe.\n3. Explicação com exemplos adequados à realidade da turma.\n4. Atividade orientada, com apoio aos estudantes com dificuldade.\n5. Socialização das respostas e retomada dos pontos principais.'

def premium_evaluation(stage):
    if stage == 'Educação Infantil': return 'Observar participação, oralidade, coordenação, interação e registros produzidos durante a atividade.'
    return 'Avaliar participação, compreensão dos enunciados, organização das respostas, resolução das questões e capacidade de explicar o raciocínio.'

def premium_homework(stage, theme):
    if stage == 'EJA': return f'Observar uma situação real em casa, no trabalho ou na comunidade relacionada a {theme} e registrar uma frase sobre ela.'
    return f'Resolver uma atividade complementar sobre {theme} ou registrar um exemplo do cotidiano relacionado ao tema.'

def premium_reset_pedagogico():
    for table in ['alternatives','questions','texts','lessons','topics','subjects','grades']:
        q(f'DELETE FROM {table}')
        try: q('DELETE FROM sqlite_sequence WHERE name=?',(table,))
        except Exception: pass


def ensure_admin_and_serials():
    admin_email=os.getenv('ADMIN_EMAIL','admin@aulapronta.com').lower()
    admin_pass=os.getenv('ADMIN_PASSWORD','admin123')
    admin_name=os.getenv('ADMIN_NAME','Administrador')
    if not q('SELECT id FROM users WHERE email=?',(admin_email,),True):
        insert('INSERT INTO users(name,email,password,is_admin,plan,valid_until,teaching_style) VALUES(?,?,?,?,?,?,?)',(admin_name,admin_email,generate_password_hash(admin_pass),1,'ESCOLA','2099-12-31','Detalhado e organizado'))
    if q('SELECT COUNT(*) c FROM serials', one=True)['c'] < 4:
        for plan,days in [('TESTE',7),('PROFESSOR',30),('PREMIUM',30),('ESCOLA',30)]:
            insert('INSERT INTO serials(code,plan,days,created_at) VALUES(?,?,?,?)',(serial_code(),plan,days,datetime.now().isoformat()))

def premium_seed(force=False):
    current = q("SELECT value FROM app_meta WHERE key='pedagogico_version'", one=True)
    total_q = q('SELECT COUNT(*) c FROM questions', one=True)['c']
    if not force and current and current['value'] == PED_VERSION_PREMIUM and total_q > 15000:
        ensure_admin_and_serials()
        return

    premium_reset_pedagogico()
    grades = ['Pré I','Pré II','1º ano','2º ano','3º ano','4º ano','5º ano','6º ano','7º ano','8º ano','9º ano','1ª série EM','2ª série EM','3ª série EM','EJA Alfabetização','EJA Fundamental I','EJA Fundamental II','EJA Médio']
    themes = premium_topics()

    with conn() as c:
        grade_ids = {}
        for i,g in enumerate(grades):
            cur = c.execute('INSERT OR IGNORE INTO grades(name,ord,stage) VALUES(?,?,?)',(g,i,premium_stage(g)))
            row = c.execute('SELECT id FROM grades WHERE name=?',(g,)).fetchone()
            grade_ids[g] = row['id']

        subject_ids = {}
        for sn in themes:
            c.execute('INSERT OR IGNORE INTO subjects(name,area) VALUES(?,?)',(sn,premium_area(sn)))
            row = c.execute('SELECT id FROM subjects WHERE name=?',(sn,)).fetchone()
            subject_ids[sn] = row['id']

        for g in grades:
            stage = premium_stage(g)
            gid = grade_ids[g]
            for sn in premium_applicable(g):
                sid = subject_ids.get(sn)
                if not sid:
                    continue
                for th in themes[sn]:
                    skill = premium_skill(stage, sn, th)
                    cur = c.execute('INSERT INTO topics(subject_id,grade_id,name,description,bncc) VALUES(?,?,?,?,?)',(sid,gid,th,f'Conteúdo de {sn} para {g}: {th}.',skill))
                    top = cur.lastrowid
                    c.execute('INSERT INTO texts(subject_id,grade_id,topic_id,title,body,eja) VALUES(?,?,?,?,?,?)',(sid,gid,top,f'Texto de apoio - {th}',premium_support(stage,sn,th),1 if 'EJA' in g else 0))
                    c.execute('INSERT INTO lessons(subject_id,grade_id,topic_id,title,duration,objective,methodology,resources,development,evaluation,homework) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(sid,gid,top,f'Plano de aula - {th}','50 minutos',skill,premium_methodology(stage),'Quadro, caderno, material impresso, exemplos do cotidiano, imagens e recursos digitais quando disponíveis.',premium_development(stage,sn,th),premium_evaluation(stage),premium_homework(stage,th)))
                    for diff in ['Fácil','Média','Difícil']:
                        types = ['DISCURSIVA','MULTIPLA','VF','LACUNAS']
                        if sn in ['Língua Portuguesa','Redação','Projeto de Vida','Filosofia','Sociologia']:
                            types.append('TEXTO')
                        for typ in types:
                            cur = c.execute('INSERT INTO questions(subject_id,grade_id,topic_id,type,difficulty,statement,command,answer,explanation,eja,skill,context) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(sid,gid,top,typ,diff,premium_statement(stage,sn,th,typ),premium_command(stage,typ),premium_answer(typ,th),f'Espera-se que o estudante relacione {th} ao conteúdo de {sn}, usando linguagem adequada para {g}.',1 if 'EJA' in g else 0,skill,premium_context(stage,sn,th)))
                            qid = cur.lastrowid
                            if typ == 'MULTIPLA':
                                alts=[('A',f'Uma ideia correta e relacionada ao estudo de {th}.',1),('B','Uma afirmação incompleta ou sem relação direta com o conteúdo.',0),('C','Uma conclusão contrária ao que foi estudado.',0),('D','Uma resposta que mistura informações sem explicar o tema.',0)]
                                for L,txt,corr in alts:
                                    c.execute('INSERT INTO alternatives(question_id,letter,text,correct) VALUES(?,?,?,?)',(qid,L,txt,corr))
        c.execute("INSERT OR REPLACE INTO app_meta(key,value) VALUES('pedagogico_version',?)",(PED_VERSION_PREMIUM,))
        c.commit()
    ensure_admin_and_serials()

premium_upgrade_schema()
premium_seed(False)

# Escape seguro para materiais renderizados
try:
    _old_esc = esc
except Exception:
    def esc(x): return html.escape(str(x or ''))

def premium_stage_label(gr): return gr['stage'] or premium_stage(gr['name'])

def premium_professor_note(u, gr):
    style = u['teaching_style'] or 'Acolhedor e simples'
    ctx = u['local_context'] or ''
    note = f'Estilo do professor: {style}. '
    if ctx.strip(): note += f'Contexto da turma/escola: {ctx.strip()} '
    if 'EJA' in gr['name']: note += 'Linguagem adequada para jovens e adultos, sem infantilização.'
    elif premium_stage_label(gr) == 'Educação Infantil': note += 'Proposta lúdica, oral e visual.'
    elif premium_stage_label(gr) == 'Ensino Médio': note += 'Proposta com análise, argumentação e contextualização.'
    return note

def premium_header(u,sub,gr,title):
    return f"ESCOLA: {u['school'] or '________________'}\nPROFESSOR(A): {u['name']}\nALUNO(A): ________________________________________________\nTURMA: {gr['name']}    DATA: ___/___/____\nDISCIPLINA: {sub['name']}\n\n{title.upper()}\n\n"

def premium_instruction(u, gr):
    st = premium_stage_label(gr)
    if st == 'Educação Infantil': return 'ORIENTAÇÕES: escute o professor, observe as imagens/situações e participe com atenção.\n\n'
    if st == 'EJA': return 'ORIENTAÇÕES: leia com calma, relacione as questões com sua experiência de vida e responda com suas palavras.\n\n'
    if st == 'Ensino Médio': return 'ORIENTAÇÕES: leia os enunciados, justifique quando necessário e relacione o conteúdo com situações reais.\n\n'
    return 'ORIENTAÇÕES: leia com atenção, responda com capricho e revise antes de entregar.\n\n'

def premium_q_student(qq,n):
    s=f"{n}. {qq['statement']}\n   {qq['command']}\n"
    if qq['type']=='MULTIPLA':
        for a in q('SELECT * FROM alternatives WHERE question_id=? ORDER BY letter',(qq['id'],)):
            s+=f"   {a['letter']}) {a['text']}\n"
    elif qq['type']=='VF': s+='   (   ) Verdadeiro     (   ) Falso\n'
    elif qq['type']=='LACUNAS': s+='   Resposta: ________________________________\n'
    elif qq['type']=='TEXTO': s+='   Produção textual:\n   __________________________________________________________\n   __________________________________________________________\n   __________________________________________________________\n'
    else: s+='   Resposta: ________________________________________________\n   __________________________________________________________\n'
    return s

def premium_q_teacher(qq,n):
    skill = f"\n   Habilidade/objetivo: {qq['skill']}" if qq['skill'] else ''
    return f"{n}. {qq['statement']}\n   Tipo: {qq['type']} | Nível: {qq['difficulty']}{skill}\n   Resposta esperada: {qq['answer']}\n   Orientação: {qq['explanation']}\n"

def premium_teacher_cover(u, sub, gr, top, kind, count):
    return f'''FOLHA DO PROFESSOR — {kind.upper()}\nDisciplina: {sub['name']}\nTurma: {gr['name']}\nConteúdo: {top['name']}\nQuestões solicitadas: {count}\n\n{premium_professor_note(u, gr)}\n\nObjetivo principal:\n{top['bncc'] or premium_skill(premium_stage_label(gr), sub['name'], top['name'])}\n\nSugestão de uso:\n1. Faça uma breve conversa inicial.\n2. Leia os enunciados com a turma quando necessário.\n3. Oriente os estudantes com dificuldade sem entregar a resposta.\n4. Use o gabarito como apoio para correção e retomada.\n\nGABARITO / ORIENTAÇÕES\n\n'''

def premium_build_questions(sub,gr,top,count,diff='Todas',types=None):
    try: count=max(1,min(60,int(count)))
    except Exception: count=10
    sql='SELECT * FROM questions WHERE subject_id=? AND grade_id=? AND topic_id=? AND active=1'; args=[sub['id'],gr['id'],top['id']]
    if diff and diff!='Todas': sql+=' AND difficulty=?'; args.append(diff)
    if types: sql += ' AND type IN (%s)'%(','.join(['?']*len(types))); args += list(types)
    rows=list(q(sql,args)); random.shuffle(rows); return rows[:count]

def premium_perfil():
    u=user()
    if request.method=='POST':
        q('UPDATE users SET name=?, school=?, city=?, state=?, avatar=?, teaching_style=?, local_context=?, default_instructions=? WHERE id=?',(request.form.get('name',''),request.form.get('school',''),request.form.get('city',''),request.form.get('state','')[:2],request.form.get('avatar',''),request.form.get('teaching_style','Acolhedor e simples'),request.form.get('local_context',''),request.form.get('default_instructions',''),u['id']))
        flash('Perfil pedagógico salvo. Os próximos materiais seguirão esse estilo.'); return redirect('/perfil')
    styles=['Acolhedor e simples','Direto e objetivo','Detalhado e organizado','Lúdico e participativo','EJA contextualizado','Ensino Médio analítico']
    style_opts=''.join([f'<option {"selected" if (u["teaching_style"] or "") == s else ""}>{s}</option>' for s in styles])
    return render(f'''<div class="header"><div><span>AulaPronta Pro</span><h1>Minha Escola e meu estilo</h1><p>Esses dados deixam as atividades com a cara do professor, da escola e da turma.</p></div></div><div class="panel"><form method="post"><div class="grid"><p><label>Nome do professor</label><input name="name" value="{esc(u['name'])}"></p><p><label>Nome da escola</label><input name="school" value="{esc(u['school'])}"></p><p><label>Cidade</label><input name="city" value="{esc(u['city'])}"></p><p><label>UF</label><input name="state" value="{esc(u['state'])}"></p></div><div class="grid"><p><label>Estilo dos materiais</label><select name="teaching_style">{style_opts}</select></p><p><label>URL da imagem do perfil</label><input name="avatar" value="{esc(u['avatar'])}" placeholder="https://..."></p></div><p><label>Contexto da turma/escola</label><textarea name="local_context" rows="4" placeholder="Ex.: turma com dificuldade de leitura, escola indígena, comunidade rural, EJA noturno...">{esc(u['local_context'])}</textarea></p><p><label>Orientações padrão do professor</label><textarea name="default_instructions" rows="3" placeholder="Ex.: usar linguagem simples, colocar exemplos do cotidiano, evitar textos longos...">{esc(u['default_instructions'])}</textarea></p><button class="btn primary big">Salvar perfil pedagógico</button></form></div>''')

def premium_dashboard():
    u=user(); recent=q('SELECT * FROM materials WHERE user_id=? ORDER BY id DESC LIMIT 6',(u['id'],))
    recent_html=''.join([f'<a class="mini-link" href="/professor/material/{m["id"]}">{esc(m["type"])} • {esc(m["title"])}<small>{esc(m["created_at"])}</small></a>' for m in recent]) or '<p class="muted">Nenhum material gerado ainda.</p>'
    cards=f'''<div class="cards"><div class="card"><small>Questões</small><strong>{q('SELECT COUNT(*) c FROM questions',one=True)['c']}</strong><p>banco pedagógico</p></div><div class="card"><small>Conteúdos</small><strong>{q('SELECT COUNT(*) c FROM topics',one=True)['c']}</strong><p>por turma</p></div><div class="card"><small>Materiais</small><strong>{q('SELECT COUNT(*) c FROM materials WHERE user_id=?',(u['id'],),one=True)['c']}</strong><p>gerados por você</p></div><div class="card"><small>Estilo</small><strong>OK</strong><p>{esc(u['teaching_style'] or 'Acolhedor')}</p></div></div>'''
    actions='''<div class="layout-2"><div class="panel"><h2>O que você quer preparar hoje?</h2><div class="action-grid"><a class="action" href="/professor/atividade"><b>Criar uma atividade</b><span>Folha do aluno com texto, questões e gabarito.</span></a><a class="action" href="/professor/avaliacao"><b>Criar uma avaliação</b><span>Prova com critérios e gabarito.</span></a><a class="action" href="/professor/plano"><b>Planejar uma aula</b><span>Plano completo e contextualizado.</span></a><a class="action" href="/professor/parecer"><b>Escrever parecer</b><span>Relatório pedagógico personalizado.</span></a></div></div><div class="panel"><h2>Materiais recentes</h2>'''+recent_html+'</div></div>'
    return render(f'<div class="hero"><div><span>AulaPronta Pro Web v2.3</span><h1>Estúdio pedagógico premium</h1><p>Agora o banco está maior e os materiais seguem o estilo do professor, a etapa de ensino e a realidade da turma.</p></div><a class="btn primary big" href="/professor/atividade">Gerar material agora</a></div>{cards}{actions}')

def premium_atividade():
    if request.method=='POST':
        u=user(); sub,gr,top=get_sel()
        if not (sub and gr and top): flash('Escolha matéria, turma e conteúdo válidos.'); return redirect('/professor/atividade')
        qty=request.form.get('quantity',10); qs=premium_build_questions(sub,gr,top,qty,request.form.get('difficulty','Todas'))
        student=premium_header(u,sub,gr,f'Atividade de {top["name"]}')+premium_instruction(u,gr)
        if request.form.get('text'):
            tx=q('SELECT * FROM texts WHERE topic_id=? ORDER BY RANDOM() LIMIT 1',(top['id'],),one=True)
            if tx: student+=f"TEXTO DE APOIO\n{tx['title']}\n{tx['body']}\n\n"
        student += f"CONTEÚDO: {top['name']}\nOBJETIVO: {top['bncc'] or premium_skill(premium_stage_label(gr), sub['name'], top['name'])}\n\nQUESTÕES\n\n"
        teacher=premium_teacher_cover(u,sub,gr,top,'atividade',qty)
        for i,qq in enumerate(qs,1): student+=premium_q_student(qq,i)+'\n'; teacher+=premium_q_teacher(qq,i)+'\n'
        teacher += '\nCHECKLIST DE QUALIDADE\n- Material adaptado à etapa/série.\n- Linguagem alinhada ao perfil do professor.\n- Gabarito incluído.\n- Orientações para retomada incluídas.\n'
        mid=material_insert(u['id'],'Atividade',f'Atividade de {top["name"]}',student,teacher); return redirect(f'/professor/material/{mid}')
    extra='<p class="quantity"><label>Quantidade</label><input name="quantity" type="number" value="10" min="1" max="60"></p><label class="toggle"><input type="checkbox" name="text" checked><span>Adicionar texto de apoio</span></label>'
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Criar Atividade</h1><p>Atividade completa com texto, questões, objetivo e gabarito.</p></div></div><div class="panel"><form method="post">'+form_selector(extra)+'<div class="preview-note"><b>Personalização:</b> o material usa seu perfil em Minha Escola, a série selecionada e o conteúdo do banco premium.</div><button class="btn primary big">Gerar atividade agora</button></form></div>')

def premium_avaliacao():
    if request.method=='POST':
        u=user(); sub,gr,top=get_sel()
        if not (sub and gr and top): flash('Escolha matéria, turma e conteúdo válidos.'); return redirect('/professor/avaliacao')
        total=safe_int(request.form.get('quantity',10),10,1,60); obj=safe_int(request.form.get('obj',5),5,0,60)
        qobj=premium_build_questions(sub,gr,top,obj,request.form.get('difficulty','Todas'),['MULTIPLA'])
        qdisc=premium_build_questions(sub,gr,top,max(0,total-len(qobj)),request.form.get('difficulty','Todas'),['DISCURSIVA','VF','LACUNAS','TEXTO'])
        qs=(qobj+qdisc)[:total]
        student=premium_header(u,sub,gr,f'Avaliação de {top["name"]}')+premium_instruction(u,gr)+f"Valor: ________    Nota: ________\n\nCONTEÚDO: {top['name']}\n\nQUESTÕES\n\n"
        teacher=premium_teacher_cover(u,sub,gr,top,'avaliação',total)+'Critérios: considerar acerto conceitual, clareza, organização e justificativa quando solicitada.\n\n'
        for i,qq in enumerate(qs,1): student+=premium_q_student(qq,i)+'\n'; teacher+=premium_q_teacher(qq,i)+'\n'
        mid=material_insert(u['id'],'Avaliação',f'Avaliação de {top["name"]}',student,teacher); return redirect(f'/professor/material/{mid}')
    extra='<p class="quantity"><label>Total</label><input name="quantity" type="number" value="10" min="1" max="60"></p><p class="quantity"><label>Questões de marcar</label><input name="obj" type="number" value="5" min="0" max="60"></p>'
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Criar Avaliação</h1><p>Avaliação com critérios, folha do aluno e gabarito.</p></div></div><div class="panel"><form method="post">'+form_selector(extra)+'<div class="preview-note"><b>Dica:</b> use questões objetivas e discursivas para avaliar melhor a aprendizagem.</div><button class="btn primary big">Gerar avaliação agora</button></form></div>')

def premium_plano():
    if request.method=='POST':
        u=user(); sub,gr,top=get_sel()
        if not (sub and gr and top): flash('Escolha matéria, turma e conteúdo válidos.'); return redirect('/professor/plano')
        pl=q('SELECT * FROM lessons WHERE topic_id=? ORDER BY RANDOM() LIMIT 1',(top['id'],),one=True)
        txt=f'''PLANO DE AULA PERSONALIZADO\n\nProfessor(a): {u['name']}\nEscola: {u['school'] or '________________'}\nDisciplina: {sub['name']}\nTurma: {gr['name']}\nEtapa: {premium_stage_label(gr)}\nTema: {top['name']}\nDuração: {(pl['duration'] if pl else '50 minutos')}\n\nPerfil pedagógico do professor:\n{premium_professor_note(u,gr)}\n\nObjetivo de aprendizagem:\n{(pl['objective'] if pl else premium_skill(premium_stage_label(gr), sub['name'], top['name']))}\n\nMetodologia:\n{(pl['methodology'] if pl else premium_methodology(premium_stage_label(gr)))}\n\nRecursos:\n{(pl['resources'] if pl else 'Quadro, caderno, material impresso e exemplos do cotidiano.')}\n\nDesenvolvimento da aula:\n{(pl['development'] if pl else premium_development(premium_stage_label(gr), sub['name'], top['name']))}\n\nAvaliação:\n{(pl['evaluation'] if pl else premium_evaluation(premium_stage_label(gr)))}\n\nTarefa / continuidade:\n{(pl['homework'] if pl else premium_homework(premium_stage_label(gr), top['name']))}\n'''
        mid=material_insert(u['id'],'Plano de aula',f'Plano de aula - {top["name"]}',txt,''); return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Planejar Aula</h1><p>Plano contextualizado pela série e pelo estilo do professor.</p></div></div><div class="panel"><form method="post">'+form_selector()+'<div class="preview-note"><b>O plano inclui:</b> perfil pedagógico, objetivo, metodologia, desenvolvimento, avaliação e tarefa.</div><button class="btn primary big">Gerar plano de aula</button></form></div>')

def premium_parecer():
    if request.method=='POST':
        u=user(); aluno=request.form.get('student','Aluno(a)'); sit=request.form.get('situation','bom'); turma=request.form.get('turma','')
        frases={'excelente':'apresenta excelente participação, demonstra autonomia e realiza as propostas com segurança.','bom':'participa das atividades propostas, demonstra interesse e vem desenvolvendo as aprendizagens esperadas.','regular':'participa quando solicitado, mas precisa ampliar autonomia, organização e constância nas atividades.','dificuldade':'apresenta dificuldades em alguns conteúdos e necessita de acompanhamento mais próximo, retomadas graduadas e incentivo contínuo.'}
        txt=f'''RELATÓRIO PEDAGÓGICO PERSONALIZADO\n\nAluno(a): {aluno}\nTurma/Série: {turma or '________________'}\nProfessor(a): {u['name']}\nEscola: {u['school'] or '________________'}\nData: {datetime.now().strftime('%d/%m/%Y')}\n\nParecer:\nO(a) estudante {frases.get(sit,frases['bom'])}\n\nObservação do professor:\n{u['default_instructions'] or 'Recomenda-se manter acompanhamento contínuo, valorizando avanços e retomando os pontos de maior dificuldade.'}\n\nIntervenções sugeridas:\n- Retomar conteúdos com exemplos práticos e linguagem clara.\n- Propor atividades graduadas, respeitando o ritmo do estudante.\n- Incentivar leitura dos enunciados, organização das respostas e participação oral.\n- Registrar avanços para acompanhar o desenvolvimento ao longo do período.\n'''
        mid=material_insert(u['id'],'Parecer',f'Parecer - {aluno}',txt,''); return redirect(f'/professor/material/{mid}')
    return render('<div class="header"><div><span>AulaPronta Pro</span><h1>Pareceres</h1><p>Relatórios pedagógicos com a linguagem do professor.</p></div></div><div class="panel"><form method="post"><div class="grid"><p><label>Nome do aluno</label><input name="student" value="Aluno(a)"></p><p><label>Turma/Série</label><input name="turma" placeholder="Ex.: 7º ano A"></p><p><label>Situação</label><select name="situation"><option value="excelente">Excelente</option><option value="bom" selected>Bom</option><option value="regular">Regular</option><option value="dificuldade">Dificuldade</option></select></p></div><button class="btn primary big">Gerar parecer</button></form></div>')

def premium_admin():
    return render(f'<div class="header"><div><span>Admin</span><h1>Painel Administrativo</h1><p>Controle do SaaS e do banco pedagógico.</p></div></div><div class="cards"><div class="card"><small>Usuários</small><strong>{q("SELECT COUNT(*) c FROM users",one=True)["c"]}</strong></div><div class="card"><small>Seriais</small><strong>{q("SELECT COUNT(*) c FROM serials",one=True)["c"]}</strong></div><div class="card"><small>Questões</small><strong>{q("SELECT COUNT(*) c FROM questions",one=True)["c"]}</strong></div><div class="card"><small>Conteúdos</small><strong>{q("SELECT COUNT(*) c FROM topics",one=True)["c"]}</strong></div></div><div class="panel"><a class="btn primary" href="/admin/seriais">Gerar seriais</a><a class="btn" href="/admin/usuarios">Ver usuários</a><a class="btn" href="/admin/checkup">Reconstruir banco premium</a><a class="btn" href="/admin/banco">Ver banco</a><a class="btn" href="/admin/diagnostico">Diagnóstico</a></div>')

def premium_admin_checkup():
    premium_seed(True); flash('Banco pedagógico premium reconstruído e atualizado para v2.3.'); return redirect('/admin')

@app.route('/admin/banco')
@admin_required
def premium_admin_banco():
    rows=q('''SELECT s.name subject, g.name grade, COUNT(t.id) topics FROM topics t JOIN subjects s ON s.id=t.subject_id JOIN grades g ON g.id=t.grade_id GROUP BY s.name,g.name ORDER BY g.ord,s.name LIMIT 500''')
    html='<div class="header"><div><span>Admin</span><h1>Banco pedagógico</h1><p>Resumo dos conteúdos por disciplina e série.</p></div></div><div class="panel table"><table><tr><th>Turma</th><th>Disciplina</th><th>Conteúdos</th></tr>'
    html+=''.join([f'<tr><td>{esc(r["grade"])}</td><td>{esc(r["subject"])}</td><td>{r["topics"]}</td></tr>' for r in rows])+'</table></div>'
    return render(html)


@app.route('/admin/diagnostico')
@admin_required
def admin_diagnostico():
    checks=[]
    for table in ['users','serials','grades','subjects','topics','texts','questions','alternatives','lessons','materials']:
        try:
            checks.append((table, q(f'SELECT COUNT(*) c FROM {table}', one=True)['c'], 'OK'))
        except Exception as e:
            checks.append((table, '-', 'ERRO: '+esc(e)))
    html='<div class="header"><div><span>Admin</span><h1>Diagnóstico do sistema</h1><p>Conferência rápida das tabelas principais.</p></div></div><div class="panel table"><table><tr><th>Tabela</th><th>Registros</th><th>Status</th></tr>'
    html+=''.join([f'<tr><td>{esc(t)}</td><td>{c}</td><td>{esc(st)}</td></tr>' for t,c,st in checks])
    html+='</table></div>'
    return render(html)

# troca as telas antigas pelas premium sem alterar as URLs
app.view_functions['perfil'] = login_required(premium_perfil)
app.view_functions['dashboard'] = login_required(premium_dashboard)
app.view_functions['atividade'] = login_required(premium_atividade)
app.view_functions['avaliacao'] = login_required(premium_avaliacao)
app.view_functions['plano'] = login_required(premium_plano)
app.view_functions['parecer'] = login_required(premium_parecer)
app.view_functions['admin'] = admin_required(premium_admin)
app.view_functions['admin_checkup'] = admin_required(premium_admin_checkup)



exec(open(os.path.join(os.path.dirname(__file__),'custom_v24_patch.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v25_final_comercial.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v30_comercial_completo.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v31_professor_sem_admin.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v33_checkup_corrigido.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v34_login_deploy.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v35_trial_period.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v36_login_cadastro_fix.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v37_secure_signup.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v38_bncc_premium.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v39_pix_whatsapp.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v310_phone_format.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v400_final_ready.py'), encoding='utf-8').read())


exec(open(os.path.join(os.path.dirname(__file__),'custom_v410_profissional.py'), encoding='utf-8').read())

if __name__=='__main__': app.run(host='0.0.0.0', debug=os.getenv('FLASK_DEBUG','0')=='1', port=int(os.getenv('PORT', 5000)))
