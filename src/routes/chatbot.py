from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.atendimento import ConfiguracaoChatbot, Webhook, Atendimento, Cliente, Mensagem
import json
import requests

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chatbot/config', methods=['GET'])
def obter_config_chatbot():
    """Obtém configuração do chatbot"""
    try:
        config = ConfiguracaoChatbot.query.first()
        if not config:
            # Criar configuração padrão
            config = ConfiguracaoChatbot(
                ativo=True,
                mensagem_boas_vindas="Olá! Bem-vindo ao nosso atendimento. Como posso ajudá-lo?",
                mensagem_fora_horario="Desculpe, estamos fora do horário de atendimento. Nosso horário é de segunda a sexta, das 9h às 18h.",
                horario_inicio="09:00",
                horario_fim="18:00",
                dias_semana=json.dumps([1, 2, 3, 4, 5]),  # Segunda a sexta
                timeout_inatividade=300,
                max_tentativas_bot=3,
                departamentos=json.dumps([
                    {"id": "vendas", "nome": "Vendas"},
                    {"id": "suporte", "nome": "Suporte Técnico"},
                    {"id": "financeiro", "nome": "Financeiro"}
                ]),
                perguntas_frequentes=json.dumps([
                    {"pergunta": "Qual o horário de atendimento?", "resposta": "Atendemos de segunda a sexta, das 9h às 18h."},
                    {"pergunta": "Como faço para falar com um atendente?", "resposta": "Digite 'atendente' a qualquer momento para ser direcionado."}
                ])
            )
            db.session.add(config)
            db.session.commit()
        
        return jsonify(config.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/chatbot/config', methods=['PUT'])
def atualizar_config_chatbot():
    """Atualiza configuração do chatbot"""
    try:
        config = ConfiguracaoChatbot.query.first()
        if not config:
            return jsonify({'error': 'Configuração não encontrada'}), 404
        
        data = request.json
        
        if 'ativo' in data:
            config.ativo = data['ativo']
        if 'mensagem_boas_vindas' in data:
            config.mensagem_boas_vindas = data['mensagem_boas_vindas']
        if 'mensagem_fora_horario' in data:
            config.mensagem_fora_horario = data['mensagem_fora_horario']
        if 'horario_inicio' in data:
            config.horario_inicio = data['horario_inicio']
        if 'horario_fim' in data:
            config.horario_fim = data['horario_fim']
        if 'dias_semana' in data:
            config.dias_semana = json.dumps(data['dias_semana'])
        if 'timeout_inatividade' in data:
            config.timeout_inatividade = data['timeout_inatividade']
        if 'max_tentativas_bot' in data:
            config.max_tentativas_bot = data['max_tentativas_bot']
        if 'departamentos' in data:
            config.departamentos = json.dumps(data['departamentos'])
        if 'perguntas_frequentes' in data:
            config.perguntas_frequentes = json.dumps(data['perguntas_frequentes'])
        
        db.session.commit()
        
        return jsonify(config.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/chatbot/processar', methods=['POST'])
def processar_mensagem_bot():
    """Processa uma mensagem recebida pelo chatbot"""
    try:
        data = request.json
        telefone = data['telefone']
        mensagem = data['mensagem'].lower().strip()
        
        # Buscar ou criar cliente
        cliente = Cliente.query.filter_by(telefone=telefone).first()
        if not cliente:
            cliente = Cliente(
                nome=data.get('nome', 'Cliente'),
                telefone=telefone
            )
            db.session.add(cliente)
            db.session.flush()
        
        # Buscar atendimento ativo ou criar novo
        atendimento = Atendimento.query.filter_by(
            cliente_id=cliente.id,
            status='bot'
        ).first()
        
        if not atendimento:
            atendimento = Atendimento(
                cliente_id=cliente.id,
                status='bot'
            )
            db.session.add(atendimento)
            db.session.flush()
        
        # Salvar mensagem do cliente
        msg_cliente = Mensagem(
            atendimento_id=atendimento.id,
            cliente_id=cliente.id,
            remetente='cliente',
            conteudo=data['mensagem']
        )
        db.session.add(msg_cliente)
        
        # Processar resposta do bot
        resposta = processar_intencao(mensagem, atendimento)
        
        # Salvar resposta do bot
        msg_bot = Mensagem(
            atendimento_id=atendimento.id,
            cliente_id=cliente.id,
            remetente='bot',
            conteudo=resposta['mensagem']
        )
        db.session.add(msg_bot)
        
        # Se solicitou atendente, mover para fila
        if resposta.get('transferir_atendente'):
            atendimento.status = 'fila'
            atendimento.departamento = resposta.get('departamento')
        
        db.session.commit()
        
        return jsonify({
            'mensagem': resposta['mensagem'],
            'atendimento_id': atendimento.id,
            'transferir_atendente': resposta.get('transferir_atendente', False),
            'opcoes': resposta.get('opcoes', [])
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def processar_intencao(mensagem, atendimento):
    """Processa a intenção da mensagem e retorna resposta apropriada"""
    config = ConfiguracaoChatbot.query.first()
    
    # Palavras-chave para transferir para atendente
    palavras_atendente = ['atendente', 'humano', 'pessoa', 'falar com alguém', 'operador']
    if any(palavra in mensagem for palavra in palavras_atendente):
        return {
            'mensagem': 'Vou transferir você para um de nossos atendentes. Por favor, aguarde um momento.',
            'transferir_atendente': True
        }
    
    # Saudações
    saudacoes = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'alo']
    if any(saudacao in mensagem for saudacao in saudacoes):
        return {
            'mensagem': config.mensagem_boas_vindas if config else 'Olá! Como posso ajudá-lo?',
            'opcoes': ['Falar com atendente', 'Ver horário de atendimento', 'Dúvidas frequentes']
        }
    
    # Horário de atendimento
    if 'horário' in mensagem or 'horario' in mensagem or 'funciona' in mensagem:
        return {
            'mensagem': f'Nosso horário de atendimento é de {config.horario_inicio} às {config.horario_fim}, de segunda a sexta-feira.'
        }
    
    # Departamentos
    if 'vendas' in mensagem or 'comprar' in mensagem or 'produto' in mensagem:
        return {
            'mensagem': 'Vou transferir você para o departamento de Vendas.',
            'transferir_atendente': True,
            'departamento': 'vendas'
        }
    
    if 'suporte' in mensagem or 'problema' in mensagem or 'ajuda' in mensagem or 'erro' in mensagem:
        return {
            'mensagem': 'Vou transferir você para o Suporte Técnico.',
            'transferir_atendente': True,
            'departamento': 'suporte'
        }
    
    if 'financeiro' in mensagem or 'boleto' in mensagem or 'pagamento' in mensagem or 'fatura' in mensagem:
        return {
            'mensagem': 'Vou transferir você para o departamento Financeiro.',
            'transferir_atendente': True,
            'departamento': 'financeiro'
        }
    
    # Resposta padrão
    return {
        'mensagem': 'Desculpe, não entendi sua solicitação. Você pode:\n1. Falar com um atendente\n2. Ver nosso horário de atendimento\n3. Escolher um departamento: Vendas, Suporte ou Financeiro',
        'opcoes': ['Atendente', 'Horário', 'Vendas', 'Suporte', 'Financeiro']
    }


# Webhooks

@chatbot_bp.route('/webhooks', methods=['GET'])
def listar_webhooks():
    """Lista todos os webhooks cadastrados"""
    try:
        webhooks = Webhook.query.all()
        return jsonify([w.to_dict() for w in webhooks])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/webhooks', methods=['POST'])
def criar_webhook():
    """Cria um novo webhook"""
    try:
        data = request.json
        
        webhook = Webhook(
            nome=data['nome'],
            url=data['url'],
            evento=data['evento'],
            ativo=data.get('ativo', True),
            headers=json.dumps(data.get('headers', {}))
        )
        
        db.session.add(webhook)
        db.session.commit()
        
        return jsonify(webhook.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/webhooks/<int:webhook_id>', methods=['PUT'])
def atualizar_webhook(webhook_id):
    """Atualiza um webhook"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)
        data = request.json
        
        if 'nome' in data:
            webhook.nome = data['nome']
        if 'url' in data:
            webhook.url = data['url']
        if 'evento' in data:
            webhook.evento = data['evento']
        if 'ativo' in data:
            webhook.ativo = data['ativo']
        if 'headers' in data:
            webhook.headers = json.dumps(data['headers'])
        
        db.session.commit()
        
        return jsonify(webhook.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/webhooks/<int:webhook_id>', methods=['DELETE'])
def deletar_webhook(webhook_id):
    """Deleta um webhook"""
    try:
        webhook = Webhook.query.get_or_404(webhook_id)
        db.session.delete(webhook)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def disparar_webhook(evento, dados):
    """Dispara webhooks cadastrados para um evento específico"""
    try:
        webhooks = Webhook.query.filter_by(evento=evento, ativo=True).all()
        
        for webhook in webhooks:
            try:
                headers = json.loads(webhook.headers) if webhook.headers else {}
                headers['Content-Type'] = 'application/json'
                
                response = requests.post(
                    webhook.url,
                    json=dados,
                    headers=headers,
                    timeout=10
                )
                
                webhook.ultima_execucao = datetime.utcnow()
                webhook.total_execucoes += 1
                db.session.commit()
                
            except Exception as e:
                print(f"Erro ao disparar webhook {webhook.id}: {str(e)}")
                continue
    except Exception as e:
        print(f"Erro ao processar webhooks: {str(e)}")


@chatbot_bp.route('/webhook', methods=['POST'])
def receber_webhook_whatsapp():
    """
    Endpoint para receber mensagens do WhatsApp (Twilio) localmente.
    Permite testes com curl sem precisar do ngrok.
    """
    try:
        # Twilio envia os dados como form-urlencoded
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        body = request.form.get('Body')

        print(f"📩 Mensagem recebida de {from_number} -> {to_number}: {body}")

        # Normaliza número para formato simples
        telefone = from_number.replace("whatsapp:", "") if from_number else "desconhecido"

        # Monta payload para o processador interno do bot
        data = {
            'telefone': telefone,
            'mensagem': body or '',
            'nome': 'Cliente WhatsApp'
        }

        # Processa usando a função existente
        resposta = processar_intencao(body.lower().strip(), None)

        print(f"🤖 Resposta do bot: {resposta['mensagem']}")

        # Monta resposta Twilio (XML)
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{resposta['mensagem']}</Message>
</Response>"""

        return twiml, 200, {'Content-Type': 'application/xml'}

    except Exception as e:
        print(f"❌ Erro no webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500
