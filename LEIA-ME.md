# Superfície — laboratório de Cálculo III

Projeto Python para executar no computador e acessar pelo navegador. Não foi publicado na internet.

## Como abrir no Windows

1. Instale Python 3.10 ou superior e marque a opção de adicionar Python ao PATH.
2. Extraia o ZIP. Abra o terminal na pasta `reservatorio_site`, onde está `app.py`.
3. Execute:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

4. Abra http://127.0.0.1:5000 no navegador. Mantenha o terminal aberto.
5. Para encerrar, pressione Ctrl+C. Para abrir novamente, execute apenas o último comando.

Linux/macOS: substitua `.venv\Scripts\python` por `.venv/bin/python`.

## Abas

- Fundamentos: problema, parametrizações e integrais de superfície escalar.
- Reservatório: raio, altura interna e seleção da lateral/fundo.
- Materiais: dez exemplos do código fornecido e cadastro de produtos com fonte.
- Aplicação visual: imagem 3D, vista em corte e controles de demãos e ângulo.
- Resultados: áreas, consumo, perdas, compra em embalagens inteiras e relatório JSON.

Os valores dos dez materiais são exemplos didáticos do arquivo enviado, não um banco técnico validado. A aplicação não declara adequação automática a água potável, submersão ou pressão negativa. Para uso real, cadastre um produto específico e use os valores de sua ficha técnica. O campo fonte registra uma referência informada pelo usuário; não significa verificação automática.

O cadastro usa SQLite: `materiais.sqlite3` é criado ao usar o site. Faça uma cópia desse arquivo para preservar seus produtos. Os exemplos são carregados do módulo `modelo_original.py`; os produtos cadastrados ficam no banco. As configurações de simulação não são salvas automaticamente: exporte o JSON para registrar parâmetros e resultados.

## Cálculo

Parede: r(θ,z) = (R cos θ, R sen θ, z), |r_θ × r_z| = R.
Fundo: r(ρ,θ) = (ρ cos θ, ρ sen θ, 0), |r_ρ × r_θ| = ρ.
A lateral = 2πRH; A fundo = πR². A soma considera somente superfícies selecionadas.
Q = ∬ c dS = c A para consumo uniforme.
Q estimado = Q (1 + perdas/100).
Embalagens = arredondamento para cima de Q estimado / massa da embalagem.

Se o consumo for por demão, c total = c por demão × número de demãos. Se for total do sistema, não é multiplicado novamente. Alterar as demãos não altera o consumo quando a base é o sistema completo.

A quadratura do código original faz ponto médio em θ e Gauss-Legendre em z e ρ, conferindo a área analítica. Para produto de consumo constante, essa comparação também confere a base da estimativa de massa. Espessura não define o consumo neste modelo. Não se converte massa em volume com os dados genéricos de densidade do arquivo original.

Visualização: imagens geradas por Matplotlib no servidor Python, atualizadas pelos controles. Não é um modelo 3D WebGL arrastável. O corte não desconta área. Cor, transparência e divisão uniforme em camadas são ilustrações; espessura exagerada. A água ilustrada representa o contato após a cura.

## Arquivos

- app.py: rotas web, validação e persistência SQLite.
- modelo_original.py: código original preservado como base de cálculo e desenho.
- templates/index.html: interface em cinco abas.
- static/style.css: aparência e adaptação para telas menores.
- static/app.js: interação, chamadas ao Python e exportação.
- requirements.txt: dependências.

## Verificação realizada

Rotas e arquivos estáticos, cálculo padrão e seleção de superfícies, consumo por demão versus total, rejeição de entradas inválidas, cadastro persistente e geração de PNG foram verificados por testes de integração. A interface não foi verificada em um navegador nesta entrega.

## Referência de desenvolvimento

Documentação oficial Flask: https://flask.palletsprojects.com/en/stable/

O servidor incluído atende uso local. Uma publicação requer configuração de hospedagem Python e servidor de produção.
