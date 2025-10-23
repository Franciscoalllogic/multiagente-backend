from flask import Blueprint, request, jsonify
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import db
from src.models.atendimento import Agente, Atendimento

agente_bp = Blueprint('agente', __name__)

@agente_bp.route('/agentes', methods=['GET'])
def listar_agentes():
    """Lista todos os agentes"""
    try:
        agentes = Agente.query.all()
        return jsonify([a.to_dict() for a in agentes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/<int:agente_id>', methods=['GET'])
def obter_agente(agente_id):
    """Obtém detalhes de um agente específico"""
    try:
        agente = Agente.query.get_or_404(agente_id)
        return jsonify(agente.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes', methods=['POST'])
def criar_agente():
    """Cria um novo agente"""
    try:
        data = request.json
        
        # Verificar se email já existe
        if Agente.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        agente = Agente(
            nome=data['nome'],
            email=data['email'],
            senha_hash=generate_password_hash(data['senha']),
            max_atendimentos=data.get('max_atendimentos', 3)
        )
        
        db.session.add(agente)
        db.session.commit()
        
        return jsonify(agente.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/<int:agente_id>', methods=['PUT'])
def atualizar_agente(agente_id):
    """Atualiza dados de um agente"""
    try:
        agente = Agente.query.get_or_404(agente_id)
        data = request.json
        
        if 'nome' in data:
            agente.nome = data['nome']
        if 'email' in data:
            agente.email = data['email']
        if 'senha' in data:
            agente.senha_hash = generate_password_hash(data['senha'])
        if 'max_atendimentos' in data:
            agente.max_atendimentos = data['max_atendimentos']
        if 'status' in data:
            agente.status = data['status']
        
        db.session.commit()
        
        return jsonify(agente.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/<int:agente_id>', methods=['DELETE'])
def deletar_agente(agente_id):
    """Deleta um agente"""
    try:
        agente = Agente.query.get_or_404(agente_id)
        db.session.delete(agente)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/login', methods=['POST'])
def login_agente():
    """Realiza login de um agente"""
    try:
        data = request.json
        
        agente = Agente.query.filter_by(email=data['email']).first()
        
        if not agente or not check_password_hash(agente.senha_hash, data['senha']):
            return jsonify({'error': 'Email ou senha inválidos'}), 401
        
        # Atualizar status e último acesso
        agente.status = 'online'
        agente.ultimo_acesso = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'agente': agente.to_dict(),
            'token': f'token_{agente.id}'  # Implementar JWT real em produção
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/<int:agente_id>/logout', methods=['POST'])
def logout_agente(agente_id):
    """Realiza logout de um agente"""
    try:
        agente = Agente.query.get_or_404(agente_id)
        agente.status = 'offline'
        db.session.commit()
        
        return jsonify({'message': 'Logout realizado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/<int:agente_id>/status', methods=['PUT'])
def atualizar_status_agente(agente_id):
    """Atualiza o status de um agente (online, offline, ocupado)"""
    try:
        agente = Agente.query.get_or_404(agente_id)
        data = request.json
        
        agente.status = data['status']
        agente.ultimo_acesso = datetime.utcnow()
        db.session.commit()
        
        return jsonify(agente.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/<int:agente_id>/atendimentos', methods=['GET'])
def listar_atendimentos_agente(agente_id):
    """Lista atendimentos de um agente específico"""
    try:
        agente = Agente.query.get_or_404(agente_id)
        
        status = request.args.get('status')
        
        query = Atendimento.query.filter_by(agente_id=agente_id)
        
        if status:
            query = query.filter_by(status=status)
        
        atendimentos = query.order_by(Atendimento.iniciado_em.desc()).all()
        
        return jsonify({
            'agente': agente.to_dict(),
            'atendimentos': [a.to_dict() for a in atendimentos]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/<int:agente_id>/estatisticas', methods=['GET'])
def obter_estatisticas_agente(agente_id):
    """Obtém estatísticas de desempenho de um agente"""
    try:
        agente = Agente.query.get_or_404(agente_id)
        
        # Atendimentos finalizados
        atendimentos_finalizados = Atendimento.query.filter_by(
            agente_id=agente_id,
            status='finalizado'
        ).all()
        
        # Tempo médio de atendimento
        tempo_medio = 0
        if atendimentos_finalizados:
            tempos = [a.tempo_atendimento for a in atendimentos_finalizados if a.tempo_atendimento]
            if tempos:
                tempo_medio = sum(tempos) / len(tempos)
        
        # Avaliação média
        avaliacoes = [a.avaliacao for a in atendimentos_finalizados if a.avaliacao]
        avaliacao_media = sum(avaliacoes) / len(avaliacoes) if avaliacoes else 0
        
        return jsonify({
            'agente': agente.to_dict(),
            'total_atendimentos': agente.total_atendimentos,
            'atendimentos_ativos': agente.atendimentos_ativos,
            'atendimentos_finalizados': len(atendimentos_finalizados),
            'tempo_medio_atendimento': int(tempo_medio),
            'avaliacao_media': round(avaliacao_media, 2),
            'total_avaliacoes': len(avaliacoes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agente_bp.route('/agentes/disponiveis', methods=['GET'])
def listar_agentes_disponiveis():
    """Lista agentes disponíveis para receber atendimentos"""
    try:
        agentes = Agente.query.filter(
            Agente.status == 'online',
            Agente.atendimentos_ativos < Agente.max_atendimentos
        ).all()
        
        return jsonify([a.to_dict() for a in agentes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

