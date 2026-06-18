# ==============================================================================
# 1. PREPARACIÓN DEL SISTEMA PARA VERCEL
# ==============================================================================
print("📦 Instalando dependencias necesarias para Vercel...")
!pip install flask yfinance gunicorn -q
print("✅ Dependencias instaladas.\n")

# ==============================================================================
# 2. CONFIGURACIÓN DE LA APLICACIÓN FLASK
# ==============================================================================
import smtplib
import yfinance as yf
from flask import Flask, render_template_string, request, flash, redirect, session
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta_bursatil_compartida_sin_bloqueos"

# Diccionario original de nombres de empresas y tickers conocidos
name_ticker_map = {
    "APPLE": "AAPL", "MICROSOFT": "MSFT", "GOOGLE": "GOOGL", "ALPHABET": "GOOGL",
    "AMAZON": "AMZN", "TESLA": "TSLA", "NVIDIA": "NVDA", "FACEBOOK": "META", "META": "META",
    "AAPL": "AAPL", "MSFT": "MSFT", "GOOGL": "GOOGL", "AMZN": "AMZN", "TSLA": "TSLA", "NVDA": "NVDA",
    "YPF": "YPFD.BA", "YPF (YPF)": "YPFD.BA", "YPFD.BA": "YPFD.BA",
    "GRUPO FINANCIERO GALICIA": "GGAL.BA", "GALICIA": "GGAL.BA", "GGAL.BA": "GGAL.BA",
    "LOMA NEGRA": "LOMA.BA", "LOMA.BA": "LOMA.BA",
    "PAMPA ENERGIA": "PAMP.BA", "PAMPA ENERGIA (PAMP)": "PAMP.BA", "PAMP.BA": "PAMP.BA",
    "MERCADO LIBRE": "MELI", "MELI": "MELI",
    "BANCO MACRO": "BMA.BA", "BMA.BA": "BMA.BA",
    "CENTRAL PUERTO": "CEPU.BA", "CEPU.BA": "CEPU.BA",
    "VISTA ENERGY": "VIST.BA", "VIST.BA": "VIST.BA",
    "BANCO SUPERVIELLE": "SUPV.BA", "SUPV.BA": "SUPV.BA",
    "BBVA ARGENTINA": "BBAR.BA", "BBAR.BA": "BBAR.BA",
    "BYMA": "BYMA.BA", "BYMA.BA": "BYMA.BA",
    "TELECOM ARGENTINA": "TECO2.BA", "TECO2.BA": "TECO2.BA",
    "TRANSPORTADORA GAS DEL SUR": "TGSU2.BA", "TGSU2.BA": "TGSU2.BA",
    "TERNIUM": "TXAR.BA", "TERNIUM ARGENTINA": "TXAR.BA", "TXAR.BA": "TXAR.BA",
}

def get_stock_data(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="2d")
        if len(hist) >= 1:
            latest = hist.iloc[-1]
            date = latest.name.strftime('%Y-%m-%d')
            open_price = latest['Open']
            close_price = latest['Close']
            variation = ((close_price - open_price) / open_price) * 100
            return open_price, close_price, variation, date
    except Exception:
        return None, None, None, None
    return None, None, None, None

def send_stock_report_email(recipient_email, subject, body, sender_email, sender_password, smtp_server, smtp_port):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = Header(subject, 'utf-8')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error SMTP: {e}")
        return False

# Interfaz Visual HTML + CSS
html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Buscador de Cotizaciones Público</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 500px; width: 100%; margin-top: 20px; text-align: center; }
        h2 { color: #1e293b; margin-top: 0; margin-bottom: 5px; }
        .subtitle { color: #64748b; font-size: 14px; margin-bottom: 25px; }
        .section { background: #f8fafc; border: 1px solid #e2e8f0; padding: 18px; border-radius: 8px; margin-bottom: 20px; text-align: left; }
        .section h3 { margin-top: 0; color: #334155; font-size: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 12px; }
        .form-group { display: flex; gap: 10px; }
        input[type="text"], input[type="email"] { flex: 1; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; box-sizing: border-box; }
        button { padding: 10px 16px; font-size: 14px; font-weight: 600; border-radius: 6px; cursor: pointer; border: none; transition: background-color 0.15s; }
        .btn-primary { background-color: #2563eb; color: white; }
        .btn-primary:hover { background-color: #1d4ed8; }
        .btn-success { background-color: #16a34a; color: white; width: 100%; padding: 12px; font-size: 15px; margin-top: 5px; }
        .btn-success:hover { background-color: #15803d; }
        .btn-danger { background-color: #ef4444; color: white; padding: 5px 10px; font-size: 12px; border-radius: 4px; }
        .btn-danger:hover { background-color: #dc2626; }
        .ticker-list { list-style: none; padding: 0; margin: 0; }
        .ticker-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 6px; font-size: 14px; }
        .ticker-info { font-weight: 500; color: #1e293b; }
        .message { padding: 10px; border-radius: 6px; margin-bottom: 15px; font-size: 14px; text-align: left; }
        .success { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .error { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
        .empty-list { color: #64748b; font-size: 14px; margin: 0; text-align: center; padding: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📊 Buscador de Cotizaciones</h2>
        <div class="subtitle">Cada pestaña de navegador gestiona su propia lista de forma privada.</div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="message {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="section">
            <h3>🔍 Buscar y Añadir Acciones</h3>
            <form action="/add" method="POST" class="form-group">
                <input type="text" name="ticker_or_name" placeholder="Ej: AAPL, YPF, Apple, Galicia, GGAL.BA..." required>
                <button type="submit" class="btn-primary">Añadir</button>
            </form>
        </div>

        <div class="section">
            <h3>📋 Tu Lista de Reporte Actual</h3>
            <ul class="ticker-list">
                {% for t in tickers %}
                <li class="ticker-item">
                    <span class="ticker-info">{{ t.name }} ({{ t.ticker }})</span>
                    <form action="/remove/{{ t.ticker }}" method="POST" style="margin:0;">
                        <button type="submit" class="btn-danger">Quitar</button>
                    </form>
                </li>
                {% endfor %}
            </ul>
            {% if not tickers %}
                <p class="empty-list">Tu lista está vacía. Busca una acción arriba para empezar.</p>
            {% endif %}
        </div>

        <div class="section">
            <h3>✉️ Destinatario del Correo</h3>
            <form action="/send" method="POST">
                <input type="email" name="email" placeholder="correo@ejemplo.com" required style="width:100%; margin-bottom:12px;">
                <button type="submit" class="btn-success">Enviar Reporte Consolidado</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    if 'tickers' not in session:
        session['tickers'] = [
            {"name": "S&P500 (SPY)", "ticker": "SPY"},
            {"name": "NASDAQ (QQQ)", "ticker": "QQQ"},
            {"name": "MERVAL", "ticker": "^MERV"}
        ]
    return render_template_string(html_template, tickers=session['tickers'])

@app.route('/add', methods=['POST'])
def add_ticker():
    user_input = request.form.get('ticker_or_name', '').strip()
    if not user_input:
        return redirect('/')

    found_ticker = None
    resolved_display_name = None
    search_term_upper = user_input.upper()

    if search_term_upper in name_ticker_map:
        found_ticker = name_ticker_map[search_term_upper]

    if not found_ticker or (found_ticker and found_ticker.upper() != search_term_upper):
        try:
            temp_yf_ticker = yf.Ticker(user_input)
            info = temp_yf_ticker.info
            if 'symbol' in info and info['symbol'].upper() == user_input.upper():
                found_ticker = info['symbol']
        except Exception:
            pass

    if found_ticker:
        display_name_from_yf = None
        try:
            info = yf.Ticker(found_ticker).info
            if 'shortName' in info and info['shortName'] and info['shortName'].upper() != found_ticker.upper():
                display_name_from_yf = info['shortName']
        except Exception:
            pass

        if display_name_from_yf:
            resolved_display_name = display_name_from_yf
        elif search_term_upper in name_ticker_map and name_ticker_map[search_term_upper] == found_ticker:
            resolved_display_name = user_input.title()
        else:
            resolved_display_name = found_ticker

        tickers_list = session.get('tickers', [])

        if any(t['ticker'].upper() == found_ticker.upper() for t in tickers_list):
            flash(f"'{resolved_display_name}' ({found_ticker}) ya está en tu lista.", "error")
        else:
            tickers_list.append({"name": resolved_display_name, "ticker": found_ticker})
            session['tickers'] = tickers_list
            session.modified = True
            flash(f"'{resolved_display_name}' ({found_ticker}) añadido correctamente.", "success")
    else:
        flash(f"No se encontró ningún ticker o empresa para '{user_input}'.", "error")

    return redirect('/')

@app.route('/remove/<ticker>', methods=['POST'])
def remove_ticker(ticker):
    tickers_list = session.get('tickers', [])
    tickers_list = [t for t in tickers_list if t['ticker'].upper() != ticker.upper()]
    session['tickers'] = tickers_list
    session.modified = True
    flash(f"Acción {ticker} removida.", "success")
    return redirect('/')

@app.route('/send', methods=['POST'])
def send_report():
    email_destinatario = request.form.get('email', '').strip()
    tickers_list = session.get('tickers', [])

    if not tickers_list:
        flash("Tu lista está vacía.", "error")
        return redirect('/')

    if not email_destinatario or "@" not in email_destinatario or "." not in email_destinatario:
        flash("Introduce una dirección de email válida.", "error")
        return redirect('/')

    latest_data_date = None
    for t in tickers_list:
        _, _, _, date = get_stock_data(t['ticker'])
        if date:
            latest_data_date = date
            break

    report_output = f"Análisis de Cotizaciones (Fecha: {latest_data_date if latest_data_date else datetime.now().strftime('%Y-%m-%d')}):\n---------------------------\n"
    for t in tickers_list:
        op, cl, var, date = get_stock_data(t['ticker'])
        if op is not None:
            report_output += f"\n{t['name']} ({t['ticker']}):\n  Apertura: {op:.2f}\n  Cierre: {cl:.2f}\n  Variación: {var:.2f}%\n"
        else:
            report_output += f"\nNo se pudieron obtener datos para {t['name']} ({t['ticker']})\n"

    smtp_usuario = 'cotizacionesautomaticassimples@gmail.com'
    smtp_password = 'vctw cinv eqkn ivqi'
    subject = f"Reporte Diario de Cotizaciones - {datetime.now().strftime('%Y-%m-%d')}"

    if send_stock_report_email(email_destinatario, subject, report_output, smtp_usuario, smtp_password, "smtp.gmail.com", 587):
        flash(f"¡Reporte enviado exitosamente a {email_destinatario}!", "success")
    else:
        flash("Error al enviar el correo.", "error")

    return redirect('/')

# Aseguramos que Vercel encuentre la instancia de la aplicación
application = app

# ==============================================================================
# 3. PREPARACIÓN PARA DESPLIEGUE EN VERCEL
# ==============================================================================
print("📝 Generando archivos de configuración para Vercel...")

# Crear el archivo requirements.txt
requirements_content = """
flask
yfinance
gunicorn
"""
with open("requirements.txt", "w") as f:
    f.write(requirements_content)
print("  - 'requirements.txt' creado.")

# Crear el archivo vercel.json
vercel_json_content = """
{
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
"""
with open("vercel.json", "w") as f:
    f.write(vercel_json_content)
print("  - 'vercel.json' creado.")

# Mensaje para el usuario sobre los siguientes pasos
print("\n🎉 El código está preparado para ser desplegado en Vercel.")
print("Pasos para el despliegue:")
print("1. Descarga el contenido de esta celda y guárdalo como 'app.py' en tu máquina local.")
print("2. Descarga el archivo 'requirements.txt' generado en los archivos de Colab (panel de la izquierda).")
print("3. Descarga el archivo 'vercel.json' generado en los archivos de Colab.")
print("4. Coloca 'app.py', 'requirements.txt' y 'vercel.json' en la misma carpeta.")
print("5. Inicializa un repositorio Git (ej: `git init`, `git add .`, `git commit -m \"Initial commit\"`) en esa carpeta y enlaza con un servicio como GitHub.")
print("6. Conecta tu cuenta de Vercel con este repositorio (a través de la interfaz web de Vercel).")
print("7. ¡Despliega tu proyecto en Vercel! Vercel detectará automáticamente la configuración Python y Flask.")
print("\nUna vez desplegado en Vercel, no necesitarás ejecutar esta celda en Colab para acceder a la aplicación públicamente.")