"""Site local de Cálculo III; execute python app.py."""
from pathlib import Path
from io import BytesIO
from threading import Lock
import json
import math
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, jsonify, render_template, request, send_file
from modelo_original import MATERIAIS, Material, Parametros, validar, estimar, integracao_numerica, desenhar_modelo, desenhar_corte

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024
app.config['DATABASE'] = str(ROOT / 'materiais.sqlite3')
plot_lock = Lock()

def db():
    connection = sqlite3.connect(app.config['DATABASE'])
    connection.execute('CREATE TABLE IF NOT EXISTS materiais (id INTEGER PRIMARY KEY, dados TEXT NOT NULL)')
    return connection

def materiais():
    result = []
    for i, m in enumerate(MATERIAIS):
        result.append(dict(id=f'exemplo-{i}', nome=m.nome, tipo=m.tipo, cor=m.cor,
            consumo=m.consumo_tipico, demaos=m.demaos, espessura=m.espessura_mm,
            embalagem=m.embalagem_kg, fonte='', origem='Exemplo didático do código enviado',
            observacoes='Valores ilustrativos, sem ficha técnica verificada. Adequação ao uso, cura e aplicação dependem do produto específico.'))
    with db() as con:
        for key, data in con.execute('SELECT id,dados FROM materiais ORDER BY id'):
            result.append(dict(json.loads(data), id=f'cadastro-{key}'))
    return result

def number(value, name, minimum, maximum):
    try:
        value = float(str(value).replace(',', '.'))
    except (TypeError, ValueError):
        raise ValueError(f'{name}: informe um número válido.')
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{name}: use um valor entre {minimum:g} e {maximum:g}.')
    return value

def parameters(data):
    material = next((m for m in materiais() if m['id'] == data.get('material')), None)
    if material is None:
        raise ValueError('Selecione um material cadastrado.')
    radius = number(data.get('raio'), 'Raio (m)', .001, 1000)
    height = number(data.get('altura'), 'Altura (m)', .001, 1000)
    coats = number(data.get('demaos'), 'Demãos', 1, 20)
    if coats != int(coats):
        raise ValueError('Demãos deve ser um número inteiro.')
    for field in ('lateral', 'fundo'):
        if type(data.get(field)) is not bool:
            raise ValueError('Informe as superfícies selecionadas.')
    consumption = number(data.get('consumo'), 'Consumo (kg/m²)', .001, 1000)
    basis = data.get('base')
    if basis not in ('total', 'demao'):
        raise ValueError('Informe a base do consumo.')
    total = consumption * coats if basis == 'demao' else consumption
    # Cor é apenas uma convenção visual; não representa a cor comercial.
    from dataclasses import replace
    display = replace(MATERIAIS[0], nome=material['nome'], cor=material['cor'])
    p = Parametros.de_material(display, raio_m=radius, altura_m=height,
        revestir_lateral=data['lateral'], revestir_fundo=data['fundo'],
        perdas_percent=number(data.get('perdas'), 'Perdas (%)', 0, 100),
        consumo_kg_m2=total, demaos=int(coats),
        espessura_mm=number(data.get('espessura'), 'Espessura (mm)', .001, 100),
        embalagem_kg=number(data.get('embalagem'), 'Embalagem (kg)', .001, 10000))
    validar(p)
    return p

@app.errorhandler(ValueError)
def invalid(error):
    return jsonify(erro=str(error)), 400

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/api/materiais')
def list_materials():
    return jsonify(materiais())

@app.post('/api/materiais')
def add_material():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Cadastro inválido.')
    name = str(data.get('nome', '')).strip()
    if not 2 <= len(name) <= 150:
        raise ValueError('Nome: use de 2 a 150 caracteres.')
    source = str(data.get('fonte', '')).strip()
    if not source or len(source) > 1000:
        raise ValueError('Informe a fonte dos dados: ficha técnica, fabricante ou referência.')
    coats = number(data.get('demaos'), 'Demãos', 1, 20)
    if coats != int(coats):
        raise ValueError('Demãos deve ser inteiro.')
    entry = dict(nome=name, tipo=str(data.get('tipo', 'Personalizado'))[:150], cor='#168b83',
        consumo=number(data.get('consumo'), 'Consumo total', .001, 1000), demaos=int(coats),
        espessura=number(data.get('espessura'), 'Espessura', .001, 100),
        embalagem=number(data.get('embalagem'), 'Embalagem', .001, 10000),
        fonte=source, origem='Cadastro do usuário — fonte informada, não verificada automaticamente',
        observacoes=str(data.get('observacoes', ''))[:3000])
    with db() as con:
        cursor = con.execute('INSERT INTO materiais(dados) VALUES (?)', (json.dumps(entry, ensure_ascii=False),))
        key = cursor.lastrowid
    return jsonify(dict(entry, id=f'cadastro-{key}')), 201

@app.post('/api/calcular')
def calculate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Parâmetros inválidos.')
    p = parameters(data)
    result = estimar(p)
    # Não converter kg em litros usando densidade/espessura seca: grandezas de bases distintas.
    result.pop('volume_L', None)
    area = integracao_numerica(p)
    numerical = (area['A_lat'] if p.revestir_lateral else 0) + (area['A_fun'] if p.revestir_fundo else 0)
    result.update(area_numerica=numerical, erro_numerico=abs(numerical-result['A_tot']), consumo_total=p.consumo_kg_m2)
    return jsonify(result)

@app.post('/api/figura')
def figure():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Parâmetros inválidos.')
    p = parameters(data)
    coat = number(data.get('aplicadas', p.demaos), 'Demãos aplicadas', 0, p.demaos)
    if coat != int(coat):
        raise ValueError('Demãos aplicadas deve ser inteiro.')
    angle = number(data.get('angulo', 25), 'Ângulo', -180, 180)
    with plot_lock:
        fig = plt.figure(figsize=(11, 5), facecolor='#f8faf9')
        try:
            model = fig.add_subplot(121, projection='3d')
            desenhar_modelo(model, p, int(coat))
            model.view_init(elev=24, azim=angle)
            model.set_title('Superfícies internas • corte de visualização')
            cut = fig.add_subplot(122)
            desenhar_corte(cut, p, int(coat))
            fig.tight_layout()
            output = BytesIO()
            fig.savefig(output, format='png', dpi=130)
        finally:
            plt.close(fig)
    output.seek(0)
    return send_file(output, mimetype='image/png')

if __name__ == '__main__':
    print('Abra http://127.0.0.1:5000 no navegador. Ctrl+C encerra.')
    app.run(host='127.0.0.1', port=5000, debug=False)
