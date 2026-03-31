<div align="center">

# 📈 Stock Dashboard

**Dashboard moderno para acompanhamento de ativos financeiros em tempo real**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Testes](https://img.shields.io/badge/Testes-Pytest-009688?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)
[![License](https://img.shields.io/badge/Licença-MIT-green?style=for-the-badge)](LICENSE)

Dashboard de aplicação dual (Terminal / Interface Web) focada em analisar e exibir as movimentações do mercado financeiro, garantindo acesso em tempo real a ações e criptomoedas com grande ênfase em dados e visualização de alta performance.

</div>

---

## 🎯 Por que este projeto se destaca? (Arquitetura & Clean Code)

Criado voltado para aplicar fundamentos reais exigidos na Engenharia de Software Moderna:
- **Arquitetura Modular:** Responsabilidades claramente separadas. O módulo de obtenção de dados e regras de negócio se comunica nativamente com o banco local e com a API HTTP baseada em Flask, favorecendo escalabilidade para microserviços.
- **Cobertura de Testes Elevada:** Múltiplas rotinas de testes garantidas pela suíte **pytest**, que asseguram a confiança no processamento assíncrono e na estruturação de bases (Pandas).
- **Integração Constante e Tratamento de Erros:** O sistema lida graciosamente com quedas de conectividade, limites externos na API do Yahoo Finance ou requisições de tickers inválidos (ex: ações deslistadas e erros na formatação BR / EUA).
- **Design UI/UX:** O projeto adota a vanguarda visual de _Glassmorphism_ sem pesar com bibliotecas complexas, tudo feito com Javascript assíncrono modular e Vanilla CSS para resposta imediata.

## ✨ Funcionalidades Adicionais

- 🔍 Busca de ativos na **bolsa americana** (ex: AAPL, MSFT), **brasileira (B3)** (ex: PETR4, VALE3) e rastreio de **Criptomoedas** em tempo real.
- 📊 **Modelagem Gráfica Avançada:** Separação precisa entre preços de Fechamento / Abertura, além do mapa de calor para volume de transações ao longo de recortes de tempo interativos (7D, 1M, 6M, 1Y).
- 💾 **Persistência Inteligente:** A engine automaticamente faz o cache do histórico consumido utilizando os `DataFrames` do Pandas e arquiva localmente (formato CSV) economizando requisições externas e garantindo uso off-line no Dashboard Web e Terminal.

## 📸 Apresentação (Interface)

### Dashboard Web — Central Financeira Em Tempo Real
<p align="center">
  <img src="docs/screenshot_cards.png" alt="Cards de cotações com sparklines" width="700">
</p>

### Dashboard Web — Gráfico Interativo de Alta Frequência
<p align="center">
  <img src="docs/screenshot_chart.png" alt="Gráfico de preços com Chart.js" width="700">
</p>

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.10 ou superior.

### Instalação em 3 Passos

1. Clone o repositório e acesse a pasta:
   ```bash
   git clone https://github.com/DarkRocha/Dashboard-de-Cotacoes.git
   cd Dashboard-de-Cotacoes
   ```

2. Configure seu ambiente isolado de pacotes (Virtual Env):
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # MacOS e Linux:
   # source venv/bin/activate
   ```

3. Instale a Stack de dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Iniciando a Aplicação

#### 🌐 Ativar Dashboard Web (Servidor Flask)
```bash
python web/app.py
# O portal iniciará em: http://localhost:5000
```

#### 🖥️ Ativar Dashboard pelo Terminal (CLI UI)
```bash
python -m stock_dashboard.main
```

## 🛠️ Stack Tecnológica Utilizada

| Tecnologia | Papel no Desenvolvimento |
|------------|------------|
| **Python** | Engine central da aplicação, modelagem de serviços. |
| **Flask** | Micro-framework web construindo os Endpoints da RESTful API. |
| **Pandas** | Otimização e manipulação do estado financeiro e de transações em arrays. |
| **Yahoo Finance API** | Fornecimento confiável e bruto de dados financeiros e históricos. |
| **Pytest** | Infraestrutura e garantia de qualidade na cobertura de testes. |
| **Chart.js** | Visualização estendida, baseada em canvas HMTL5 visando alta performance. |
| **Rich & Plotext** | Módulos responsáveis pela exibição complexa e painéis robustos para a experiência via Terminal. |

<br/>

<div align="center">
  Desenvolvido por <strong>Gabriel Rocha</strong>.<br>
  Pronto para impactos sérios em engenharia de software e análise de dados.
</div>
