
# ============================================================
# AulaPronta Pro v3.10 - Telefone Pix/WhatsApp formatado
# Mostra telefone bonito: (98) 99612-7032
# Mantém a cópia da chave Pix em número limpo: 98996127032
# Mantém WhatsApp com DDI para abrir link: 5598996127032
# ============================================================

V310_VERSION = "v3.10-telefone-formatado"

def v310_format_br_phone(value):
    digits = v39_digits(value)
    # Remove DDI 55 quando vier em número de WhatsApp.
    if digits.startswith("55") and len(digits) >= 12:
        digits = digits[2:]

    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return value

def pagamento_professor_v310(order_id):
    u = user()
    o = q("SELECT * FROM payment_orders WHERE id=? AND user_id=?", (order_id, u["id"]), True)
    if not o:
        flash("Pedido não encontrado.")
        return redirect("/assinatura")

    pix_raw = v39_pix_key()
    pix_display = v310_format_br_phone(pix_raw)
    whatsapp_display = v310_format_br_phone(v39_whatsapp_number())
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

          <p>
            <label>Chave Pix — telefone</label>
            <input id="pixDisplayV310" readonly value="{esc(pix_display)}">
            <input id="pixKeyV39" type="hidden" value="{esc(pix_raw)}">
          </p>

          <p><label>Nome completo</label><input readonly value="{esc(pix_holder)}"></p>
          <p><label>Banco</label><input readonly value="{esc(pix_bank)}"></p>

          <div class="phone-note-v310">
            <b>Chave limpa para copiar:</b> {esc(pix_raw)}
          </div>

          <button class="btn" type="button" onclick="navigator.clipboard && navigator.clipboard.writeText(document.getElementById('pixKeyV39').value); alert('Chave Pix copiada: ' + document.getElementById('pixKeyV39').value)">Copiar chave Pix</button>
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
        <p><b>Pix:</b><br>{esc(pix_display)}</p>
        <p><b>Banco:</b><br>{esc(pix_bank)}</p>
        <p><b>WhatsApp:</b><br>{esc(whatsapp_display)}</p>
        <a class="btn primary" href="{whats_url}" target="_blank">Abrir WhatsApp direto</a>
      </div>
    </div>
    '''
    return render(content, "Pedido de renovação")

if "pagamento_page" in app.view_functions:
    app.view_functions["pagamento_page"] = login_required(pagamento_professor_v310)
