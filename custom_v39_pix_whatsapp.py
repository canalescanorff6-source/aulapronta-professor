
# ============================================================
# AulaPronta Pro v3.9 - Pix real + WhatsApp de comprovante
# Corrige a tela de renovação/pagamento do professor:
# - Chave Pix real
# - Nome do recebedor
# - Banco
# - Botão para confirmar e enviar comprovante no WhatsApp
# ============================================================

import os
from urllib.parse import quote
from datetime import datetime
from flask import redirect, flash

V39_VERSION = "v3.9-pix-whatsapp"

def v39_digits(s):
    return "".join(ch for ch in str(s or "") if ch.isdigit())

def v39_pix_key():
    return os.getenv("PIX_KEY", "98996127032")

def v39_pix_holder():
    return os.getenv("PIX_HOLDER", "LUIS TIAGO SANTOS MARQUES")

def v39_pix_bank():
    return os.getenv("PIX_BANK", "BANCO MERCADO PAGO")

def v39_whatsapp_number():
    return v39_digits(os.getenv("WHATSAPP_PAYMENT", "5598996127032"))

def v39_payment_message(u, o):
    return (
        "Olá, Luis Tiago! Fiz o pagamento da renovação do AulaPronta Pro.\\n\\n"
        f"Professor: {u['name'] or 'Professor(a)'}\\n"
        f"E-mail: {u['email']}\\n"
        f"Pedido: #{o['id']}\\n"
        f"Referência: {o['reference']}\\n"
        f"Plano: {o['plan']}\\n"
        f"Valor: R$ {o['amount']}\\n\\n"
        f"Pix usado: {v39_pix_key()}\\n"
        f"Nome: {v39_pix_holder()}\\n"
        f"Banco: {v39_pix_bank()}\\n\\n"
        "Segue o comprovante em anexo."
    )

def v39_whatsapp_url(u, o):
    return f"https://wa.me/{v39_whatsapp_number()}?text={quote(v39_payment_message(u, o))}"

def comprar_plano_professor_v39(plan_key):
    u = user()
    if plan_key not in PLANOS_PROFESSOR:
        flash("Plano inválido.")
        return redirect("/assinatura")
    p = PLANOS_PROFESSOR[plan_key]
    ref = "AP-" + secrets.token_hex(4).upper()
    q("INSERT INTO payment_orders(user_id,plan,amount,days,status,pix_key,reference,created_at) VALUES(?,?,?,?,?,?,?,?)",
      (u["id"], p["label"], p["amount"], p["days"], "pendente", v39_pix_key(), ref, datetime.now().isoformat()))
    row = q("SELECT id FROM payment_orders WHERE reference=?", (ref,), True)
    flash("Pedido de renovação criado. Faça o Pix e envie o comprovante pelo WhatsApp.")
    return redirect(f"/pagamento/{row['id']}")

def pagamento_professor_v39(order_id):
    u = user()
    o = q("SELECT * FROM payment_orders WHERE id=? AND user_id=?", (order_id, u["id"]), True)
    if not o:
        flash("Pedido não encontrado.")
        return redirect("/assinatura")

    pix_key = v39_pix_key()
    pix_holder = v39_pix_holder()
    pix_bank = v39_pix_bank()
    whats_url = v39_whatsapp_url(u, o)
    msg = v39_payment_message(u, o)

    status_label = esc(o["status"] or "pendente")
    content = f'''
    <div class="header">
      <div>
        <span>Renovação</span>
        <h1>Pedido #{o["id"]}</h1>
        <p>Faça o Pix, clique no botão do WhatsApp e envie o comprovante para liberação.</p>
      </div>
    </div>

    <div class="payment-premium-grid">
      <div class="panel payment-box">
        <h2>Plano {esc(o["plan"])}</h2>

        <div class="payment-summary-v39">
          <div><small>Valor</small><b>R$ {esc(o["amount"])}</b></div>
          <div><small>Status</small><b>{status_label}</b></div>
          <div><small>Referência</small><b>{esc(o["reference"])}</b></div>
        </div>

        <div class="pix-card-v39">
          <h3>Dados para pagamento Pix</h3>
          <p><label>Chave Pix — telefone</label><input id="pixKeyV39" readonly value="{esc(pix_key)}"></p>
          <p><label>Nome completo</label><input readonly value="{esc(pix_holder)}"></p>
          <p><label>Banco</label><input readonly value="{esc(pix_bank)}"></p>
          <button class="btn" type="button" onclick="navigator.clipboard && navigator.clipboard.writeText(document.getElementById('pixKeyV39').value); alert('Chave Pix copiada!')">Copiar chave Pix</button>
        </div>

        <div class="whatsapp-card-v39">
          <h3>Enviar comprovante</h3>
          <p class="muted">Depois de pagar, clique no botão abaixo. O WhatsApp abrirá com a mensagem do pedido pronta. Anexe o comprovante antes de enviar.</p>
          <p><label>Mensagem pronta</label><textarea id="msgWhatsV39" readonly rows="7">{esc(msg)}</textarea></p>

          <div class="action-row-v39">
            <a class="btn primary big" href="/pagamento/{o["id"]}/confirmar-whatsapp" target="_blank">Confirmar e enviar pelo WhatsApp</a>
            <button class="btn" type="button" onclick="navigator.clipboard && navigator.clipboard.writeText(document.getElementById('msgWhatsV39').value); alert('Mensagem copiada!')">Copiar mensagem</button>
            <a class="btn" href="/assinatura">Voltar</a>
          </div>
        </div>

        <p class="muted">A aprovação da renovação é feita no Admin Center separado após a conferência do comprovante.</p>
      </div>

      <div class="panel support-box-v39">
        <h2>Resumo do pagamento</h2>
        <p><b>Recebedor:</b><br>{esc(pix_holder)}</p>
        <p><b>Pix:</b><br>{esc(pix_key)}</p>
        <p><b>Banco:</b><br>{esc(pix_bank)}</p>
        <p><b>WhatsApp:</b><br>{esc(v39_whatsapp_number())}</p>
        <a class="btn primary" href="{whats_url}" target="_blank">Abrir WhatsApp direto</a>
      </div>
    </div>
    '''
    return render(content, "Pedido de renovação")

def confirmar_whatsapp_v39(order_id):
    u = user()
    o = q("SELECT * FROM payment_orders WHERE id=? AND user_id=?", (order_id, u["id"]), True)
    if not o:
        flash("Pedido não encontrado.")
        return redirect("/assinatura")

    if (o["status"] or "pendente") == "pendente":
        q("UPDATE payment_orders SET status=?, note=? WHERE id=?",
          ("comprovante_enviado", "Professor clicou para enviar comprovante pelo WhatsApp.", order_id))

    return redirect(v39_whatsapp_url(u, o))

if "comprar_plano" in app.view_functions:
    app.view_functions["comprar_plano"] = login_required(comprar_plano_professor_v39)
if "pagamento_page" in app.view_functions:
    app.view_functions["pagamento_page"] = login_required(pagamento_professor_v39)

try:
    app.add_url_rule("/pagamento/<int:order_id>/confirmar-whatsapp", "confirmar_whatsapp_v39", login_required(confirmar_whatsapp_v39))
except Exception:
    pass
