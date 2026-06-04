
# ============================================================
# AulaPronta Pro v3.0 - Comercial Completo
# Pagamentos manuais Pix, aprovação admin, renovação de assinatura,
# troca de senha e preparação para venda.
# ============================================================

import os, secrets, shutil
from pathlib import Path
from datetime import datetime, timedelta
from flask import request, redirect, flash, send_file, session
from werkzeug.security import generate_password_hash, check_password_hash

COMMERCIAL_VERSION = "v3.0-comercial-completo"
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

PLAN_TABLE = {
    "mensal": {"name": "MENSAL", "label": "Mensal", "amount": "19,90", "days": 30},
    "semestral": {"name": "SEMESTRAL", "label": "Semestral", "amount": "99,90", "days": 180},
    "anual": {"name": "ANUAL", "label": "Anual", "amount": "179,90", "days": 365},
    "escola": {"name": "ESCOLA", "label": "Escola", "amount": "Sob consulta", "days": 365},
}

def commercial_setup():
    with conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS payment_orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            amount TEXT,
            days INTEGER,
            status TEXT DEFAULT 'pendente',
            pix_key TEXT DEFAULT '',
            reference TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            paid_at TEXT DEFAULT '',
            approved_by INTEGER DEFAULT 0,
            note TEXT DEFAULT ''
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            detail TEXT,
            created_at TEXT
        )
        """)
        c.commit()

def pix_key_value():
    return os.getenv("PIX_KEY") or os.getenv("CHAVE_PIX") or "CONFIGURE-SUA-CHAVE-PIX-NO-ENV"

def commercial_log(action, detail=""):
    try:
        q("INSERT INTO admin_logs(user_id,action,detail,created_at) VALUES(?,?,?,?)", (session.get("uid") or 0, action, detail, datetime.now().isoformat()))
    except Exception:
        pass

def plan_by_label(label):
    for key, item in PLAN_TABLE.items():
        if item["label"] == label or item["name"] == label:
            return key, item
    return "mensal", PLAN_TABLE["mensal"]

def extend_user_license(user_id, plan_key, days):
    target = q("SELECT * FROM users WHERE id=?", (user_id,), True)
    if not target:
        return ""
    today = datetime.now().date()
    try:
        current = datetime.fromisoformat(target["valid_until"]).date()
    except Exception:
        current = today
    base = current if current > today else today
    new_until = (base + timedelta(days=int(days))).isoformat()
    plan = PLAN_TABLE.get(plan_key, PLAN_TABLE["mensal"])
    q("UPDATE users SET plan=?, valid_until=? WHERE id=?", (plan["name"], new_until, user_id))
    return new_until

def assinatura_page():
    u = user()
    d = None
    try:
        d = (datetime.fromisoformat(u["valid_until"]).date() - datetime.now().date()).days
    except Exception:
        pass
    status = "Ativa"
    if d is not None and d < 0:
        status = "Expirada"
    elif d is not None and d <= 7:
        status = "Vencendo"
    cards = []
    for key, p in PLAN_TABLE.items():
        valor = p["amount"] if p["amount"].startswith("Sob") else "R$ " + p["amount"]
        cards.append(f'<div class="card"><small>{p["label"]}</small><strong>{valor}</strong><p>{p["days"]} dias de acesso</p><a class="btn primary" href="/comprar/{key}">Escolher plano</a></div>')
    orders = q("SELECT * FROM payment_orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (u["id"],))
    order_html = ""
    for o in orders:
        order_html += f'<div class="commercial-order"><div><b>Pedido #{o["id"]} - {esc(o["plan"])}</b><span>Valor: {esc(o["amount"])} - Status: {esc(o["status"])} - {esc(o["created_at"])}</span></div><a class="btn" href="/pagamento/{o["id"]}">Ver</a></div>'
    if not order_html:
        order_html = '<p class="muted">Nenhum pedido de renovação criado ainda.</p>'
    html = []
    html.append('<div class="header"><div><span>Assinatura</span><h1>Minha assinatura</h1><p>Veja validade, renove o plano e acompanhe pagamentos.</p></div></div>')
    html.append('<div class="cards">')
    html.append(f'<div class="card"><small>Status</small><strong>{status}</strong><p>situação da conta</p></div>')
    html.append(f'<div class="card"><small>Plano</small><strong>{esc(u["plan"] or "---")}</strong><p>plano atual</p></div>')
    html.append(f'<div class="card"><small>Validade</small><strong>{esc(u["valid_until"] or "---")}</strong><p>data de expiração</p></div>')
    html.append(f'<div class="card"><small>Dias</small><strong>{d if d is not None else "---"}</strong><p>dias restantes</p></div>')
    html.append('</div>')
    html.append('<div class="panel"><h2>Renovar assinatura</h2><div class="cards">' + "".join(cards) + '</div></div>')
    html.append('<div class="panel"><h2>Pedidos de pagamento</h2>' + order_html + '</div>')
    return render("".join(html), "Minha assinatura")

def comprar_plano(plan_key):
    u = user()
    if plan_key not in PLAN_TABLE:
        flash("Plano inválido.")
        return redirect("/assinatura")
    p = PLAN_TABLE[plan_key]
    ref = "AP-" + secrets.token_hex(4).upper()
    q("INSERT INTO payment_orders(user_id,plan,amount,days,status,pix_key,reference,created_at) VALUES(?,?,?,?,?,?,?,?)", (u["id"], p["label"], p["amount"], p["days"], "pendente", pix_key_value(), ref, datetime.now().isoformat()))
    row = q("SELECT id FROM payment_orders WHERE reference=?", (ref,), True)
    return redirect(f"/pagamento/{row['id']}")

def pagamento_page(order_id):
    u = user()
    o = q("SELECT * FROM payment_orders WHERE id=? AND user_id=?", (order_id, u["id"]), True)
    if not o and u["is_admin"]:
        o = q("SELECT * FROM payment_orders WHERE id=?", (order_id,), True)
    if not o:
        flash("Pedido não encontrado.")
        return redirect("/assinatura")
    msg = f"AulaPronta Pro | Pedido {o['reference']} | Plano {o['plan']} | Valor {o['amount']} | Email {u['email']}"
    html = []
    html.append(f'<div class="header"><div><span>Pagamento</span><h1>Pedido #{o["id"]}</h1><p>Faça o Pix e aguarde a aprovação no painel administrativo.</p></div></div>')
    html.append('<div class="panel payment-box">')
    html.append(f'<h2>Plano {esc(o["plan"])}</h2>')
    html.append(f'<p><b>Valor:</b> {esc(o["amount"])}</p>')
    html.append(f'<p><b>Status:</b> {esc(o["status"])}</p>')
    html.append(f'<p><b>Referência:</b> {esc(o["reference"])}</p>')
    html.append(f'<p><label>Chave Pix</label><input readonly value="{esc(o["pix_key"])}"></p>')
    html.append(f'<p><label>Mensagem do comprovante</label><textarea readonly rows="3">{esc(msg)}</textarea></p>')
    html.append('<p class="muted">Após o pagamento, envie o comprovante ao administrador. Ele aprova o pedido e a validade é renovada automaticamente.</p>')
    html.append('<a class="btn" href="/assinatura">Voltar</a>')
    html.append('</div>')
    return render("".join(html), "Pagamento")

def admin_pagamentos():
    rows = q("SELECT payment_orders.*, users.name as uname, users.email as uemail FROM payment_orders LEFT JOIN users ON users.id=payment_orders.user_id ORDER BY payment_orders.id DESC LIMIT 100")
    html = []
    html.append('<div class="header"><div><span>Pagamentos</span><h1>Pedidos e renovações</h1><p>Aprove pagamentos manuais e libere acesso.</p></div></div>')
    html.append('<div class="panel list-table"><table><tr><th>ID</th><th>Professor</th><th>Plano</th><th>Valor</th><th>Status</th><th>Ação</th></tr>')
    for r in rows:
        action = f'<a class="btn primary" href="/admin/pagamento/{r["id"]}/aprovar">Aprovar</a>' if r["status"] == "pendente" else '<span class="muted">Aprovado</span>'
        html.append(f'<tr><td>#{r["id"]}</td><td>{esc(r["uname"] or "---")}<br><small>{esc(r["uemail"] or "")}</small></td><td>{esc(r["plan"])}</td><td>{esc(r["amount"])}</td><td>{esc(r["status"])}</td><td>{action}</td></tr>')
    html.append('</table></div>')
    return render("".join(html), "Pagamentos")

def admin_aprovar_pagamento(order_id):
    o = q("SELECT * FROM payment_orders WHERE id=?", (order_id,), True)
    if not o:
        flash("Pedido não encontrado.")
        return redirect("/admin/pagamentos")
    if o["status"] == "aprovado":
        flash("Pedido já aprovado.")
        return redirect("/admin/pagamentos")
    plan_key, plan = plan_by_label(o["plan"])
    new_until = extend_user_license(o["user_id"], plan_key, o["days"])
    q("UPDATE payment_orders SET status='aprovado', paid_at=?, approved_by=? WHERE id=?", (datetime.now().isoformat(), session.get("uid") or 0, order_id))
    commercial_log("aprovar_pagamento", f"pedido={order_id}; validade={new_until}")
    flash(f"Pagamento aprovado. Nova validade: {new_until}")
    return redirect("/admin/pagamentos")

def trocar_senha():
    u = user()
    if request.method == "POST":
        atual = request.form.get("atual", "")
        nova = request.form.get("nova", "")
        repetir = request.form.get("repetir", "")
        if not check_password_hash(u["password"], atual):
            flash("Senha atual incorreta.")
            return redirect("/trocar-senha")
        if len(nova) < 6 or nova != repetir:
            flash("Nova senha inválida ou não confere.")
            return redirect("/trocar-senha")
        q("UPDATE users SET password=? WHERE id=?", (generate_password_hash(nova), u["id"]))
        flash("Senha alterada com sucesso.")
        return redirect("/professor")
    return render('<div class="header"><div><span>Segurança</span><h1>Trocar senha</h1><p>Use uma senha forte antes de colocar online.</p></div></div><div class="panel"><form method="post"><p><label>Senha atual</label><input type="password" name="atual"></p><p><label>Nova senha</label><input type="password" name="nova"></p><p><label>Repetir nova senha</label><input type="password" name="repetir"></p><button class="btn primary big">Alterar senha</button></form></div>', "Trocar senha")

def admin_backup_v30():
    db_path = Path("aulapronta.db")
    if not db_path.exists():
        flash("Banco não encontrado.")
        return redirect("/admin")
    out = BACKUP_DIR / f"backup_aulapronta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, out)
    return send_file(out, as_attachment=True, download_name=out.name)

commercial_setup()

try:
    if "Minha assinatura" not in BASE_HTML:
        BASE_HTML = BASE_HTML.replace(
            '<a href="/perfil"><span>PF</span><div><b>Perfil Profissional</b><small>Escola, foto e estilo</small></div></a>',
            '<a href="/perfil"><span>PF</span><div><b>Perfil Profissional</b><small>Escola, foto e estilo</small></div></a><a href="/assinatura"><span>AS</span><div><b>Minha assinatura</b><small>Plano, validade e renovação</small></div></a><a href="/trocar-senha"><span>SE</span><div><b>Segurança</b><small>Trocar senha</small></div></a>'
        )
        BASE_HTML = BASE_HTML.replace(
            '<a href="/admin"><span>AD</span><div><b>Gestão Premium</b><small>Seriais, usuários e banco</small></div></a>',
            '<a href="/admin"><span>AD</span><div><b>Gestão Premium</b><small>Seriais, usuários e banco</small></div></a><a href="/admin/pagamentos"><span>PG</span><div><b>Pagamentos</b><small>Aprovar renovações</small></div></a>'
        )
except Exception:
    pass

app.add_url_rule("/assinatura", "assinatura", login_required(assinatura_page))
app.add_url_rule("/comprar/<plan_key>", "comprar_plano", login_required(comprar_plano))
app.add_url_rule("/pagamento/<int:order_id>", "pagamento_page", login_required(pagamento_page))
app.add_url_rule("/admin/pagamentos", "admin_pagamentos", admin_required(admin_pagamentos))
app.add_url_rule("/admin/pagamento/<int:order_id>/aprovar", "admin_aprovar_pagamento", admin_required(admin_aprovar_pagamento))
app.add_url_rule("/trocar-senha", "trocar_senha", login_required(trocar_senha), methods=["GET", "POST"])
app.add_url_rule("/admin/backup-v30", "admin_backup_v30", admin_required(admin_backup_v30))
