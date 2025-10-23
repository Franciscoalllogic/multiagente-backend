from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.user import db
from src.models.atendimento import Atendimento, Cliente, Agente, Mensagem
import json

atendimento_bp = Blueprint('atendimento', __name__)

@atendimento_bp.route('/atendimentos', methods=['GET'])
def listar_atendimentos():
    """Lista todos os atendimentos com filtros opcionais"""
    try:
        status = request.args.get('status')
        agente_id = request.args.get('agente_id')
        cliente_id = request.args.get('cliente_id')
        
        query = Atendimento.query
        
        if status:
            query = query.filter_by(status=status)
        if agente_id:
            query = query.filter_by(agente_id=agente_id)
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)
        
        atendimentos = query.order_by(Atendimento.iniciado_em.desc()).all()
        return jsonify([a.to_dict() for a in atendimentos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/atendimentos/<int:atendimento_id>', methods=['GET'])
def obter_atendimento(atendimento_id):
    """Obtém detalhes de um atendimento específico"""
    try:
        atendimento = Atendimento.query.get_or_404(atendimento_id)
        return jsonify(atendimento.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/atendimentos', methods=['POST'])
def criar_atendimento():
    """Cria um novo atendimento"""
    try:
        data = request.json
        
        # Verificar se cliente existe ou criar novo
        cliente = Cliente.query.filter_by(telefone=data['telefone']).first()
        if not cliente:
            cliente = Cliente(
                nome=data.get('nome', 'Cliente'),
                telefone=data['telefone'],
                email=data.get('email')
            )
            db.session.add(cliente)
            db.session.flush()
        
        # Criar atendimento
        atendimento = Atendimento(
            cliente_id=cliente.id,
            status='fila',
            prioridade=data.get('prioridade', 0),
            departamento=data.get('departamento'),
            assunto=data.get('assunto')
        )
        
        db.session.add(atendimento)
        db.session.commit()
        
        return jsonify(atendimento.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/atendimentos/<int:atendimento_id>/atribuir', methods=['POST'])
def atribuir_atendimento(atendimento_id):
    """Atribui um atendimento a um agente"""
    try:
        data = request.json
        agente_id = data.get('agente_id')
        
        atendimento = Atendimento.query.get_or_404(atendimento_id)
        agente = Agente.query.get_or_404(agente_id)
        
        # Verificar se agente pode receber mais atendimentos
        if agente.atendimentos_ativos >= agente.max_atendimentos:
            return jsonify({'error': 'Agente com capacidade máxima'}), 400
        
        # Atribuir atendimento
        atendimento.agente_id = agente_id
        atendimento.status = 'em_atendimento'
        atendimento.atribuido_em = datetime.utcnow()
        
        if atendimento.iniciado_em:
            atendimento.tempo_espera = int((atendimento.atribuido_em - atendimento.iniciado_em).total_seconds())
        
        # Atualizar contador do agente
        agente.atendimentos_ativos += 1
        agente.total_atendimentos += 1
        
        db.session.commit()
        
        return jsonify(atendimento.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/atendimentos/<int:atendimento_id>/finalizar', methods=['POST'])
def finalizar_atendimento(atendimento_id):
    """Finaliza um atendimento"""
    try:
        data = request.json
        
        atendimento = Atendimento.query.get_or_404(atendimento_id)
        atendimento.status = 'finalizado'
        atendimento.finalizado_em = datetime.utcnow()
        
        if atendimento.atribuido_em:
            atendimento.tempo_atendimento = int((atendimento.finalizado_em - atendimento.atribuido_em).total_seconds())
        
        # Avaliação opcional
        if 'avaliacao' in data:
            atendimento.avaliacao = data['avaliacao']
            atendimento.comentario_avaliacao = data.get('comentario')
        
        # Tags opcionais
        if 'tags' in data:
            atendimento.tags = json.dumps(data['tags'])
        
        # Atualizar contador do agente
        if atendimento.agente:
            atendimento.agente.atendimentos_ativos = max(0, atendimento.agente.atendimentos_ativos - 1)
        
        db.session.commit()
        
        return jsonify(atendimento.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/atendimentos/<int:atendimento_id>/mensagens', methods=['GET'])
def listar_mensagens(atendimento_id):
    """Lista todas as mensagens de um atendimento"""
    try:
        atendimento = Atendimento.query.get_or_404(atendimento_id)
        mensagens = Mensagem.query.filter_by(atendimento_id=atendimento_id).order_by(Mensagem.enviada_em).all()
        return jsonify([m.to_dict() for m in mensagens])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/atendimentos/<int:atendimento_id>/mensagens', methods=['POST'])
def enviar_mensagem(atendimento_id):
    """Envia uma nova mensagem em um atendimento"""
    try:
        data = request.json
        
        atendimento = Atendimento.query.get_or_404(atendimento_id)
        
        mensagem = Mensagem(
            atendimento_id=atendimento_id,
            cliente_id=atendimento.cliente_id,
            agente_id=data.get('agente_id'),
            tipo=data.get('tipo', 'texto'),
            remetente=data['remetente'],
            conteudo=data['conteudo'],
            arquivo_url=data.get('arquivo_url')
        )
        
        db.session.add(mensagem)
        
        # Atualizar última interação do cliente
        atendimento.cliente.ultima_interacao = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(mensagem.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/fila', methods=['GET'])
def obter_fila():
    """Obtém atendimentos na fila ordenados por prioridade e tempo de espera"""
    try:
        atendimentos = Atendimento.query.filter_by(status='fila').order_by(
            Atendimento.prioridade.desc(),
            Atendimento.iniciado_em
        ).all()
        
        return jsonify({
            'total': len(atendimentos),
            'atendimentos': [a.to_dict() for a in atendimentos]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/fila/proximo', methods=['POST'])
def pegar_proximo_fila():
    """Atribui o próximo atendimento da fila a um agente"""
    try:
        data = request.json
        agente_id = data.get('agente_id')
        
        agente = Agente.query.get_or_404(agente_id)
        
        # Verificar capacidade do agente
        if agente.atendimentos_ativos >= agente.max_atendimentos:
            return jsonify({'error': 'Agente com capacidade máxima'}), 400
        
        # Buscar próximo atendimento na fila
        atendimento = Atendimento.query.filter_by(status='fila').order_by(
            Atendimento.prioridade.desc(),
            Atendimento.iniciado_em
        ).first()
        
        if not atendimento:
            return jsonify({'message': 'Nenhum atendimento na fila'}), 404
        
        # Atribuir atendimento
        atendimento.agente_id = agente_id
        atendimento.status = 'em_atendimento'
        atendimento.atribuido_em = datetime.utcnow()
        
        if atendimento.iniciado_em:
            atendimento.tempo_espera = int((atendimento.atribuido_em - atendimento.iniciado_em).total_seconds())
        
        agente.atendimentos_ativos += 1
        agente.total_atendimentos += 1
        
        db.session.commit()
        
        return jsonify(atendimento.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@atendimento_bp.route('/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Obtém estatísticas gerais do sistema"""
    try:
        total_atendimentos = Atendimento.query.count()
        em_fila = Atendimento.query.filter_by(status='fila').count()
        em_atendimento = Atendimento.query.filter_by(status='em_atendimento').count()
        finalizados = Atendimento.query.filter_by(status='finalizado').count()
        
        agentes_online = Agente.query.filter_by(status='online').count()
        agentes_total = Agente.query.count()
        
        # Tempo médio de espera (últimas 24h)
        ontem = datetime.utcnow() - timedelta(days=1)
        atendimentos_recentes = Atendimento.query.filter(
            Atendimento.iniciado_em >= ontem,
            Atendimento.tempo_espera.isnot(None)
        ).all()
        
        tempo_medio_espera = 0
        if atendimentos_recentes:
            tempo_medio_espera = sum(a.tempo_espera for a in atendimentos_recentes) / len(atendimentos_recentes)
        
        # Tempo médio de atendimento
        atendimentos_finalizados = Atendimento.query.filter(
            Atendimento.iniciado_em >= ontem,
            Atendimento.tempo_atendimento.isnot(None)
        ).all()
        
        tempo_medio_atendimento = 0
        if atendimentos_finalizados:
            tempo_medio_atendimento = sum(a.tempo_atendimento for a in atendimentos_finalizados) / len(atendimentos_finalizados)
        
        return jsonify({
            'total_atendimentos': total_atendimentos,
            'em_fila': em_fila,
            'em_atendimento': em_atendimento,
            'finalizados': finalizados,
            'agentes_online': agentes_online,
            'agentes_total': agentes_total,
            'tempo_medio_espera': int(tempo_medio_espera),
            'tempo_medio_atendimento': int(tempo_medio_atendimento)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

