from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from db import get_db_connection
from reportlab.pdfgen import canvas
import os
import config

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessário para utilizar flash messages

# Garante que a pasta de PDFs existe
if not os.path.exists(config.DATA_DIR):
    os.makedirs(config.DATA_DIR)

# Página inicial (index com seções: dashboard, novo pedido, notas fiscais)
@app.route('/')
def index():
    return redirect(url_for('dashboard'))  # Redirecionando para o dashboard por padrão

# Página de Dashboard separada
@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome_cliente, valor_total, data_pedido
        FROM pedidos
        ORDER BY data_pedido DESC
    """)
    pedidos = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', pedidos=pedidos)

# Página de Novo Pedido
@app.route('/pedidos/novo')
def novo_pedido():
    return render_template('pedidos_novo.html')

# Registrar Pedido e gerar PDF
@app.route('/registrar_pedido', methods=['POST'])
def registrar_pedido():
    nome_cliente = request.form['nome_cliente']
    produtos = request.form['produtos']
    quantidade = int(request.form['quantidade'])
    valor_total = float(request.form['valor_total'])
    desconto = float(request.form['desconto'] or 0)
    numero_whatsapp = request.form['numero_whatsapp']
    forma_pagamento = request.form['forma_pagamento']
    endereco_entrega = request.form['endereco_entrega']

    # Salva no banco
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pedidos (
            nome_cliente, produtos, quantidade, valor_total, desconto,
            numero_whatsapp, forma_pagamento, endereco_entrega
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        nome_cliente, produtos, quantidade, valor_total, desconto,
        numero_whatsapp, forma_pagamento, endereco_entrega
    ))
    conn.commit()

    pedido_id = cursor.lastrowid

    # Gera o PDF da NFE
    pdf_path = gerar_pdf_nfe(
        pedido_id,
        nome_cliente,
        produtos,
        quantidade,
        valor_total,
        desconto,
        forma_pagamento,
        endereco_entrega
    )

    # Salva no histórico de envio
    cursor.execute("INSERT INTO historico_envio (id_pedido) VALUES (%s)", (pedido_id,))
    conn.commit()
    conn.close()

    # Mensagem flash para informar o sucesso
    flash(f'NFE gerada com sucesso! Arquivo: {pdf_path}', 'success')

    # Redireciona para o dashboard após o registro do pedido
    return redirect(url_for('dashboard'))

# Função para gerar PDF da NFE
def gerar_pdf_nfe(pedido_id, nome_cliente, produtos, quantidade, valor_total, desconto, forma_pagamento, endereco_entrega):
    filename = f"nfe_{pedido_id}.pdf"
    filepath = os.path.join(config.DATA_DIR, filename)

    c = canvas.Canvas(filepath)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "NOTA FISCAL ELETRÔNICA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 760, f"Nome do Cliente: {nome_cliente}")
    c.drawString(50, 740, f"Produtos: {produtos}")
    c.drawString(50, 720, f"Quantidade: {quantidade}")
    c.drawString(50, 700, f"Valor Total: R$ {valor_total:.2f}")
    c.drawString(50, 680, f"Desconto: R$ {desconto:.2f}")
    c.drawString(50, 660, f"Forma de Pagamento: {forma_pagamento}")
    c.drawString(50, 640, f"Endereço de Entrega: {endereco_entrega}")
    c.drawString(50, 600, "Obrigado pela sua compra!")
    c.save()

    return filepath

# Visualizar detalhes de um pedido
@app.route('/visualizar_pedido/<int:pedido_id>')
def visualizar_pedido(pedido_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
    pedido = cursor.fetchone()
    conn.close()
    return render_template('visualizar_pedido.html', pedido=pedido)

# Baixar o PDF da NFE
@app.route('/baixar_nfe/<int:pedido_id>')
def baixar_nfe(pedido_id):
    pdf_path = os.path.join(config.DATA_DIR, f"nfe_{pedido_id}.pdf")
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    flash('Arquivo não encontrado!', 'danger')  # Mensagem de erro se o arquivo não for encontrado
    return redirect(url_for('dashboard'))

# Página de configurações
@app.route('/configuracoes')
def configuracoes():
    return render_template('configuracoes.html')

# Inicia o app
if __name__ == '__main__':
    app.run(debug=True)
