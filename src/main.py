import os
import sys
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.agente import agente_bp
from src.routes.cliente import cliente_bp
from src.routes.atendimento import atendimento_bp
from src.routes.chatbot import chatbot_bp

# Garantir caminho correto dos módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Carrega variáveis do .env
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configurações da aplicação
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave_default_segura')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Habilitar CORS
CORS(app)

# Inicializar banco
db.init_app(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(agente_bp, url_prefix='/api')
app.register_blueprint(cliente_bp, url_prefix='/api')
app.register_blueprint(atendimento_bp, url_prefix='/api')
app.register_blueprint(chatbot_bp, url_prefix='/api')

# Criar tabelas e agente demo
with app.app_context():
    from src.models.atendimento import (
        Agente, Cliente, Atendimento, Mensagem,
        ConfiguracaoChatbot, Webhook
    )
    db.create_all()

    if not Agente.query.first():
        from werkzeug.security import generate_password_hash
        agente_demo = Agente(
            nome='Agente Demo',
            email='agente@demo.com',
            senha_hash=generate_password_hash('demo123'),
            status='online',
            max_atendimentos=5
        )
        db.session.add(agente_demo)
        db.session.commit()
        print("✅ Agente demo criado: agente@demo.com / demo123")

@app.route('/api/health')
def health():
    return {'status': 'healthy', 'service': 'sistema-atendimento-multiagente'}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
