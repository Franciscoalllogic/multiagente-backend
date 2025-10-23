from datetime import datetime
from src.models.user import db

class Agente(db.Model):
    """Modelo para agentes de atendimento"""
    __tablename__ = 'agentes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='offline')  # online, offline, ocupado
    max_atendimentos = db.Column(db.Integer, default=3)
    atendimentos_ativos = db.Column(db.Integer, default=0)
    total_atendimentos = db.Column(db.Integer, default=0)
    avaliacao_media = db.Column(db.Float, default=0.0)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime)
    
    # Relacionamentos
    atendimentos = db.relationship('Atendimento', backref='agente', lazy=True)
    mensagens = db.relationship('Mensagem', backref='agente', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'status': self.status,
            'max_atendimentos': self.max_atendimentos,
            'atendimentos_ativos': self.atendimentos_ativos,
            'total_atendimentos': self.total_atendimentos,
            'avaliacao_media': self.avaliacao_media,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None
        }


class Cliente(db.Model):
    """Modelo para clientes/contatos"""
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    telefone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120))
    tags = db.Column(db.String(500))  # JSON string com tags
    notas = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_interacao = db.Column(db.DateTime)
    
    # Relacionamentos
    atendimentos = db.relationship('Atendimento', backref='cliente', lazy=True)
    mensagens = db.relationship('Mensagem', backref='cliente', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'telefone': self.telefone,
            'email': self.email,
            'tags': self.tags,
            'notas': self.notas,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'ultima_interacao': self.ultima_interacao.isoformat() if self.ultima_interacao else None
        }


class Atendimento(db.Model):
    """Modelo para sessões de atendimento"""
    __tablename__ = 'atendimentos'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    agente_id = db.Column(db.Integer, db.ForeignKey('agentes.id'))
    status = db.Column(db.String(20), default='fila')  # fila, em_atendimento, finalizado, bot
    prioridade = db.Column(db.Integer, default=0)  # 0=normal, 1=alta, 2=urgente
    departamento = db.Column(db.String(50))
    assunto = db.Column(db.String(200))
    iniciado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atribuido_em = db.Column(db.DateTime)
    finalizado_em = db.Column(db.DateTime)
    tempo_espera = db.Column(db.Integer)  # segundos
    tempo_atendimento = db.Column(db.Integer)  # segundos
    avaliacao = db.Column(db.Integer)  # 1-5 estrelas
    comentario_avaliacao = db.Column(db.Text)
    tags = db.Column(db.String(500))  # JSON string com tags
    
    # Relacionamentos
    mensagens = db.relationship('Mensagem', backref='atendimento', lazy=True, order_by='Mensagem.enviada_em')
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'cliente': self.cliente.to_dict() if self.cliente else None,
            'agente_id': self.agente_id,
            'agente': self.agente.to_dict() if self.agente else None,
            'status': self.status,
            'prioridade': self.prioridade,
            'departamento': self.departamento,
            'assunto': self.assunto,
            'iniciado_em': self.iniciado_em.isoformat() if self.iniciado_em else None,
            'atribuido_em': self.atribuido_em.isoformat() if self.atribuido_em else None,
            'finalizado_em': self.finalizado_em.isoformat() if self.finalizado_em else None,
            'tempo_espera': self.tempo_espera,
            'tempo_atendimento': self.tempo_atendimento,
            'avaliacao': self.avaliacao,
            'comentario_avaliacao': self.comentario_avaliacao,
            'tags': self.tags,
            'total_mensagens': len(self.mensagens) if self.mensagens else 0
        }


class Mensagem(db.Model):
    """Modelo para mensagens trocadas"""
    __tablename__ = 'mensagens'
    
    id = db.Column(db.Integer, primary_key=True)
    atendimento_id = db.Column(db.Integer, db.ForeignKey('atendimentos.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    agente_id = db.Column(db.Integer, db.ForeignKey('agentes.id'))
    tipo = db.Column(db.String(20), default='texto')  # texto, imagem, audio, video, documento
    remetente = db.Column(db.String(20), nullable=False)  # cliente, agente, bot
    conteudo = db.Column(db.Text, nullable=False)
    arquivo_url = db.Column(db.String(500))
    lida = db.Column(db.Boolean, default=False)
    enviada_em = db.Column(db.DateTime, default=datetime.utcnow)
    lida_em = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'atendimento_id': self.atendimento_id,
            'cliente_id': self.cliente_id,
            'agente_id': self.agente_id,
            'tipo': self.tipo,
            'remetente': self.remetente,
            'conteudo': self.conteudo,
            'arquivo_url': self.arquivo_url,
            'lida': self.lida,
            'enviada_em': self.enviada_em.isoformat() if self.enviada_em else None,
            'lida_em': self.lida_em.isoformat() if self.lida_em else None
        }


class ConfiguracaoChatbot(db.Model):
    """Configurações do chatbot"""
    __tablename__ = 'configuracao_chatbot'
    
    id = db.Column(db.Integer, primary_key=True)
    ativo = db.Column(db.Boolean, default=True)
    mensagem_boas_vindas = db.Column(db.Text)
    mensagem_fora_horario = db.Column(db.Text)
    horario_inicio = db.Column(db.String(5))  # HH:MM
    horario_fim = db.Column(db.String(5))  # HH:MM
    dias_semana = db.Column(db.String(50))  # JSON array
    timeout_inatividade = db.Column(db.Integer, default=300)  # segundos
    max_tentativas_bot = db.Column(db.Integer, default=3)
    departamentos = db.Column(db.Text)  # JSON array
    perguntas_frequentes = db.Column(db.Text)  # JSON array
    
    def to_dict(self):
        return {
            'id': self.id,
            'ativo': self.ativo,
            'mensagem_boas_vindas': self.mensagem_boas_vindas,
            'mensagem_fora_horario': self.mensagem_fora_horario,
            'horario_inicio': self.horario_inicio,
            'horario_fim': self.horario_fim,
            'dias_semana': self.dias_semana,
            'timeout_inatividade': self.timeout_inatividade,
            'max_tentativas_bot': self.max_tentativas_bot,
            'departamentos': self.departamentos,
            'perguntas_frequentes': self.perguntas_frequentes
        }


class Webhook(db.Model):
    """Registro de webhooks para integrações"""
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    evento = db.Column(db.String(50), nullable=False)  # nova_mensagem, atendimento_iniciado, etc
    ativo = db.Column(db.Boolean, default=True)
    headers = db.Column(db.Text)  # JSON string
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_execucao = db.Column(db.DateTime)
    total_execucoes = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'url': self.url,
            'evento': self.evento,
            'ativo': self.ativo,
            'headers': self.headers,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'ultima_execucao': self.ultima_execucao.isoformat() if self.ultima_execucao else None,
            'total_execucoes': self.total_execucoes
        }

