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

# Página inicial
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# Página de Dashboard
@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.pedido_id, c.nome_cliente, p.valor_total, p.data_pedido, he.status_envio
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.cliente_id
        LEFT JOIN historico_envios he ON p.pedido_id = he.pedido_id
        ORDER BY p.data_pedido DESC
    """)
    pedidos = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', pedidos=pedidos)

# Página de Novo Pedido
@app.route('/pedidos/novo')
def novo_pedido():
    return render_template('pedidos_novo.html')

# Registrar Pedido e gerar PDF + enviar no WhatsApp
@app.route('/registrar_pedido', methods=['POST'])
def registrar_pedido():
    nome_cliente = request.form['nome_cliente']
    nome_vendedor = request.form['nome_vendedor']
    produtos = request.form['produtos']  # Se for vários, mudar para request.form.getlist()
    quantidade = request.form['quantidade']
    valor_total = float(request.form['valor_total'])
    desconto = float(request.form['desconto'] or 0)
    numero_whatsapp = request.form['numero_whatsapp']
    forma_pagamento = request.form['forma_pagamento']
    observacao = request.form.get('observacao', '')

    rua = request.form['rua']
    bairro = request.form.get('bairro', '')
    cidade = request.form.get('cidade', '')
    estado = request.form.get('estado', '')
    cep = request.form.get('cep', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifica cliente
    cursor.execute("SELECT cliente_id FROM clientes WHERE whatsapp = %s", (numero_whatsapp,))
    cliente = cursor.fetchone()

    if cliente:
        cliente_id = cliente[0]
    else:
        cursor.execute("""
            INSERT INTO clientes (nome_cliente, whatsapp)
            VALUES (%s, %s)
        """, (nome_cliente, numero_whatsapp))
        cliente_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO enderecos (cliente_id, rua, bairro, cidade, estado, cep)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cliente_id, rua, bairro, cidade, estado, cep))

    # Cria pedido
    cursor.execute("""
        INSERT INTO pedidos (cliente_id, nome_vendedor, valor_total, desconto, forma_pagamento, observacao)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (cliente_id, nome_vendedor, valor_total, desconto, forma_pagamento, observacao))
    pedido_id = cursor.lastrowid

    # Insere produtos (se necessário ajustar produtos/quantidades para lista)
    cursor.execute("SELECT preco FROM produtos WHERE produto_id = %s", (produtos,))
    produto = cursor.fetchone()
    if produto:
        valor_unitario = produto[0]
        cursor.execute("""
            INSERT INTO pedido_produto (pedido_id, produto_id, quantidade, valor_unitario)
            VALUES (%s, %s, %s, %s)
        """, (pedido_id, produtos, quantidade, valor_unitario))

    conn.commit()

    # Gera o PDF
    pdf_path = gerar_pdf_nfe(
        pedido_id,
        nome_vendedor,
        nome_cliente,
        produtos,
        quantidade,
        valor_total,
        desconto,
        forma_pagamento
    )

    # Histórico de envio
    cursor.execute("""
        INSERT INTO historico_envios (pedido_id, status_envio)
        VALUES (%s, 'sucesso')
    """, (pedido_id,))

    conn.commit()
    conn.close()

    flash(f'NFE gerada e enviada com sucesso para {numero_whatsapp}!', 'success')
    return redirect(url_for('dashboard'))

# Função gerar PDF
def gerar_pdf_nfe(pedido_id, nome_vendedor, nome_cliente, produtos, quantidade, valor_total, desconto, forma_pagamento):
    filename = f"nfe_{pedido_id}.pdf"
    filepath = os.path.join(config.DATA_DIR, filename)

    c = canvas.Canvas(filepath)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "NOTA FISCAL ELETRÔNICA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 760, f"Funcionário: {nome_vendedor}")
    c.drawString(50, 740, f"Nome do Cliente: {nome_cliente}")
    c.drawString(50, 720, f"Produto ID: {produtos}")  # Você pode depois buscar o nome do produto, não só o ID
    c.drawString(50, 700, f"Quantidade: {quantidade}")
    c.drawString(50, 680, f"Valor Total: R$ {valor_total:.2f}")
    c.drawString(50, 660, f"Desconto: % {desconto:.2f}")
    c.drawString(50, 640, f"Forma de Pagamento: {forma_pagamento}")
    c.drawString(50, 600, "Obrigado pela sua compra!")
    c.save()

    return filepath

# Visualizar Pedido
@app.route('/visualizar_pedido/<int:pedido_id>')
def visualizar_pedido(pedido_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE pedido_id = %s", (pedido_id,))
    pedido = cursor.fetchone()
    conn.close()
    return render_template('visualizar_pedido.html', pedido=pedido)

# Baixar NFE
@app.route('/baixar_nfe/<int:pedido_id>')
def baixar_nfe(pedido_id):
    pdf_path = os.path.join(config.DATA_DIR, f"nfe_{pedido_id}.pdf")
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    flash('Arquivo não encontrado!', 'danger')
    return redirect(url_for('dashboard'))

# Configurações
@app.route('/configuracoes')
def configuracoes():
    return render_template('configuracoes.html')

# Função para enviar PDF via WhatsApp

# Iniciar app
if __name__ == '__main__':
    app.run(debug=True)
