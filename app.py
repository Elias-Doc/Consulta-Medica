from flask import Flask, render_template, request, redirect, send_from_directory
import os
import sqlite3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def init_db():
    with sqlite3.connect('documentos.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS pessoas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT NOT NULL,
                            cpf TEXT NOT NULL)
                        ''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS documentos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome_arquivo TEXT NOT NULL,
                            caminho TEXT NOT NULL,
                            pessoa_id INTEGER,
                            FOREIGN KEY(pessoa_id) REFERENCES pessoas(id))
                        ''')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro-pessoa', methods=['GET', 'POST'])
def cadastro_pessoa():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        with sqlite3.connect('documentos.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO pessoas (nome, cpf) VALUES (?, ?)', (nome, cpf))
        return redirect('/')
    return render_template('cadastro_pessoa.html')

@app.route('/upload-documento', methods=['GET', 'POST'])
def upload_documento():
    with sqlite3.connect('documentos.db') as conn:
        pessoas = conn.execute('SELECT id, nome FROM pessoas').fetchall()

    if request.method == 'POST':
        arquivo = request.files['arquivo']
        pessoa_id = request.form['pessoa_id']
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
        arquivo.save(caminho)
        with sqlite3.connect('documentos.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO documentos (nome_arquivo, caminho, pessoa_id) VALUES (?, ?, ?)',
                           (arquivo.filename, caminho, pessoa_id))
        return redirect('/')

    return render_template('upload_documento.html', pessoas=pessoas)

@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    resultados = []
    if request.method == 'POST':
        termo = request.form['termo']
        query = '''SELECT d.id, d.nome_arquivo, p.nome
                   FROM documentos d
                   JOIN pessoas p ON d.pessoa_id = p.id
                   WHERE p.nome LIKE ? OR d.nome_arquivo LIKE ?'''
        like_termo = f"%{termo}%"
        with sqlite3.connect('documentos.db') as conn:
            resultados = conn.execute(query, (like_termo, like_termo)).fetchall()
    return render_template('buscar.html', resultados=resultados)

@app.route('/documento/<int:doc_id>')
def documento(doc_id):
    with sqlite3.connect('documentos.db') as conn:
        doc = conn.execute('SELECT caminho, nome_arquivo FROM documentos WHERE id = ?', (doc_id,)).fetchone()
    if doc:
        pasta, nome = os.path.split(doc[0])
        return send_from_directory(pasta, nome, as_attachment=True)
    return "Documento não encontrado", 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
