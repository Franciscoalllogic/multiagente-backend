from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.atendimento import Cliente, Atendimento
import json

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/clientes', methods=['GET'])
def listar_clientes():
    """Lista todos os clientes"""
    try:
        clientes = Cliente.query.order_by(Cliente.ultima_interacao.desc()).all()
        return jsonify([c.to_dict() for c in clientes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
def obter_cliente(cliente_id):
    """Obtém detalhes de um cliente específico"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        return jsonify(cliente.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes/telefone/<telefone>', methods=['GET'])
def obter_cliente_por_telefone(telefone):
    """Obtém cliente por número de telefone"""
    try:
        cliente = Cliente.query.filter_by(telefone=telefone).first()
        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404
        return jsonify(cliente.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes', methods=['POST'])
def criar_cliente():
    """Cria um novo cliente"""
    try:
        data = request.json
        
        # Verificar se telefone já existe
        if Cliente.query.filter_by(telefone=data['telefone']).first():
            return jsonify({'error': 'Telefone já cadastrado'}), 400
        
        cliente = Cliente(
            nome=data.get('nome', 'Cliente'),
            telefone=data['telefone'],
            email=data.get('email'),
            tags=json.dumps(data.get('tags', [])) if 'tags' in data else None,
            notas=data.get('notas')
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        return jsonify(cliente.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])
def atualizar_cliente(cliente_id):
    """Atualiza dados de um cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        data = request.json
        
        if 'nome' in data:
            cliente.nome = data['nome']
        if 'email' in data:
            cliente.email = data['email']
        if 'tags' in data:
            cliente.tags = json.dumps(data['tags'])
        if 'notas' in data:
            cliente.notas = data['notas']
        
        db.session.commit()
        
        return jsonify(cliente.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>', methods=['DELETE'])
def deletar_cliente(cliente_id):
    """Deleta um cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        db.session.delete(cliente)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>/atendimentos', methods=['GET'])
def listar_atendimentos_cliente(cliente_id):
    """Lista histórico de atendimentos de um cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        atendimentos = Atendimento.query.filter_by(cliente_id=cliente_id).order_by(Atendimento.iniciado_em.desc()).all()
        
        return jsonify({
            'cliente': cliente.to_dict(),
            'total_atendimentos': len(atendimentos),
            'atendimentos': [a.to_dict() for a in atendimentos]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>/tags', methods=['POST'])
def adicionar_tag_cliente(cliente_id):
    """Adiciona uma tag a um cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        data = request.json
        
        tags = json.loads(cliente.tags) if cliente.tags else []
        nova_tag = data['tag']
        
        if nova_tag not in tags:
            tags.append(nova_tag)
            cliente.tags = json.dumps(tags)
            db.session.commit()
        
        return jsonify(cliente.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes/<int:cliente_id>/tags/<tag>', methods=['DELETE'])
def remover_tag_cliente(cliente_id, tag):
    """Remove uma tag de um cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        
        tags = json.loads(cliente.tags) if cliente.tags else []
        
        if tag in tags:
            tags.remove(tag)
            cliente.tags = json.dumps(tags)
            db.session.commit()
        
        return jsonify(cliente.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@cliente_bp.route('/clientes/buscar', methods=['GET'])
def buscar_clientes():
    """Busca clientes por nome, telefone ou email"""
    try:
        termo = request.args.get('q', '')
        
        clientes = Cliente.query.filter(
            (Cliente.nome.ilike(f'%{termo}%')) |
            (Cliente.telefone.ilike(f'%{termo}%')) |
            (Cliente.email.ilike(f'%{termo}%'))
        ).all()
        
        return jsonify([c.to_dict() for c in clientes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

