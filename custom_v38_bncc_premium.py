
from flask import request, jsonify

def bncc_count():
    try: return q("SELECT COUNT(*) c FROM bncc_habilidades", one=True)["c"]
    except Exception: return 0

def professor_bncc():
    etapa=request.args.get('etapa','').strip(); componente=request.args.get('componente','').strip(); busca=request.args.get('busca','').strip()
    sql='SELECT * FROM bncc_habilidades WHERE 1=1'; args=[]
    if etapa: sql+=' AND etapa=?'; args.append(etapa)
    if componente: sql+=' AND componente=?'; args.append(componente)
    if busca: sql+=' AND (codigo LIKE ? OR descricao LIKE ? OR ano_serie LIKE ?)'; args += [f'%{busca}%',f'%{busca}%',f'%{busca}%']
    sql+=' ORDER BY etapa, componente, codigo LIMIT 300'; rows=q(sql, tuple(args))
    comps=q('SELECT DISTINCT componente FROM bncc_habilidades ORDER BY componente'); etapas=q('SELECT DISTINCT etapa FROM bncc_habilidades ORDER BY etapa')
    comp_opts='<option value="">Todos</option>'+''.join([f'<option {"selected" if componente==r["componente"] else ""}>{esc(r["componente"])}</option>' for r in comps])
    etapa_opts='<option value="">Todas</option>'+''.join([f'<option {"selected" if etapa==r["etapa"] else ""}>{esc(r["etapa"])}</option>' for r in etapas])
    cards=''
    for r in rows:
        cards += '<div class="bncc-card"><b>'+esc(r['codigo'])+'</b><span>'+esc(r['etapa'])+' - '+esc(r['ano_serie'])+' - '+esc(r['componente'])+'</span><p>'+esc(r['descricao'])+'</p></div>'
    if not cards: cards='<p class="muted">Nenhuma habilidade encontrada.</p>'
    content=f'''<div class="header"><div><span>BNCC Premium</span><h1>Banco BNCC oficial</h1><p>Consulte habilidades, códigos e competências alinhadas à Base Nacional Comum Curricular.</p></div><div class="final-license"><b>{bncc_count()}</b><span>habilidades BNCC no banco</span></div></div><div class="panel"><form class="bncc-filter"><p><label>Etapa</label><select name="etapa">{etapa_opts}</select></p><p><label>Componente</label><select name="componente">{comp_opts}</select></p><p><label>Buscar código/termo</label><input name="busca" value="{esc(busca)}" placeholder="EF01LP01, Matemática, leitura..."></p><p><label>&nbsp;</label><button class="btn primary">Filtrar</button></p></form></div><div class="panel"><h2>Habilidades encontradas</h2>{cards}</div>'''
    return render(content,'BNCC')

def api_bncc_habilidades():
    rows=q('SELECT codigo,etapa,ano_serie,componente,descricao FROM bncc_habilidades ORDER BY codigo LIMIT 200')
    return jsonify([dict(r) for r in rows])
try:
    app.add_url_rule('/professor/bncc','professor_bncc',login_required(professor_bncc))
    app.add_url_rule('/api/bncc/habilidades','api_bncc_habilidades',login_required(api_bncc_habilidades))
except Exception: pass
try:
    if 'Banco BNCC' not in BASE_HTML:
        BASE_HTML=BASE_HTML.replace('<a href="/professor/materiais"><span>MT</span><div><b>Meus Materiais</b><small>Histórico e exportação</small></div></a>','<a href="/professor/materiais"><span>MT</span><div><b>Meus Materiais</b><small>Histórico e exportação</small></div></a><a href="/professor/bncc"><span>BN</span><div><b>Banco BNCC</b><small>Códigos e habilidades oficiais</small></div></a>')
except Exception: pass
