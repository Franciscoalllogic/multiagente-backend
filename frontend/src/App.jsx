import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Avatar, AvatarFallback } from '@/components/ui/avatar.jsx'
import { 
  MessageSquare, Users, Clock, CheckCircle2, AlertCircle, 
  Send, Phone, Mail, Tag, BarChart3, Settings, LogOut,
  UserCircle, Bot, Zap, TrendingUp, Activity
} from 'lucide-react'
import './App.css'

// Configuração da API
const API_URL = '/api'

function App() {
  const [agente, setAgente] = useState(null)
  const [loginForm, setLoginForm] = useState({ email: 'agente@demo.com', senha: 'demo123' })
  const [atendimentos, setAtendimentos] = useState([])
  const [atendimentoAtivo, setAtendimentoAtivo] = useState(null)
  const [mensagens, setMensagens] = useState([])
  const [novaMensagem, setNovaMensagem] = useState('')
  const [fila, setFila] = useState([])
  const [estatisticas, setEstatisticas] = useState({})
  const [loading, setLoading] = useState(false)

  // Login
  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/agentes/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      })
      const data = await response.json()
      if (response.ok) {
        setAgente(data.agente)
        carregarDados()
      } else {
        alert(data.error || 'Erro ao fazer login')
      }
    } catch (error) {
      alert('Erro ao conectar com o servidor')
    }
    setLoading(false)
  }

  // Carregar dados
  const carregarDados = async () => {
    try {
      // Carregar fila
      const filaRes = await fetch(`${API_URL}/fila`)
      const filaData = await filaRes.json()
      setFila(filaData.atendimentos || [])

      // Carregar estatísticas
      const statsRes = await fetch(`${API_URL}/estatisticas`)
      const statsData = await statsRes.json()
      setEstatisticas(statsData)

      // Carregar atendimentos do agente
      if (agente) {
        const atendRes = await fetch(`${API_URL}/agentes/${agente.id}/atendimentos?status=em_atendimento`)
        const atendData = await atendRes.json()
        setAtendimentos(atendData.atendimentos || [])
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
    }
  }

  // Pegar próximo da fila
  const pegarProximoFila = async () => {
    if (!agente) return
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/fila/proximo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agente_id: agente.id })
      })
      const data = await response.json()
      if (response.ok) {
        setAtendimentoAtivo(data)
        carregarMensagens(data.id)
        carregarDados()
      } else {
        alert(data.error || data.message || 'Erro ao pegar atendimento')
      }
    } catch (error) {
      alert('Erro ao conectar com o servidor')
    }
    setLoading(false)
  }

  // Carregar mensagens
  const carregarMensagens = async (atendimentoId) => {
    try {
      const response = await fetch(`${API_URL}/atendimentos/${atendimentoId}/mensagens`)
      const data = await response.json()
      setMensagens(data)
    } catch (error) {
      console.error('Erro ao carregar mensagens:', error)
    }
  }

  // Enviar mensagem
  const enviarMensagem = async (e) => {
    e.preventDefault()
    if (!novaMensagem.trim() || !atendimentoAtivo) return

    try {
      const response = await fetch(`${API_URL}/atendimentos/${atendimentoAtivo.id}/mensagens`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          remetente: 'agente',
          conteudo: novaMensagem,
          agente_id: agente.id
        })
      })
      const data = await response.json()
      if (response.ok) {
        setMensagens([...mensagens, data])
        setNovaMensagem('')
      }
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error)
    }
  }

  // Finalizar atendimento
  const finalizarAtendimento = async () => {
    if (!atendimentoAtivo) return
    
    try {
      const response = await fetch(`${API_URL}/atendimentos/${atendimentoAtivo.id}/finalizar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      if (response.ok) {
        setAtendimentoAtivo(null)
        setMensagens([])
        carregarDados()
      }
    } catch (error) {
      console.error('Erro ao finalizar atendimento:', error)
    }
  }

  // Logout
  const handleLogout = async () => {
    if (agente) {
      await fetch(`${API_URL}/agentes/${agente.id}/logout`, { method: 'POST' })
    }
    setAgente(null)
    setAtendimentoAtivo(null)
    setMensagens([])
  }

  // Atualizar dados periodicamente
  useEffect(() => {
    if (agente) {
      carregarDados()
      const interval = setInterval(carregarDados, 5000) // A cada 5 segundos
      return () => clearInterval(interval)
    }
  }, [agente])

  // Tela de Login
  if (!agente) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl">Sistema de Atendimento</CardTitle>
            <CardDescription>Faça login para acessar o painel</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="seu@email.com"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="senha">Senha</Label>
                <Input
                  id="senha"
                  type="password"
                  placeholder="••••••••"
                  value={loginForm.senha}
                  onChange={(e) => setLoginForm({...loginForm, senha: e.target.value})}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Entrando...' : 'Entrar'}
              </Button>
              <p className="text-sm text-center text-muted-foreground">
                Demo: agente@demo.com / demo123
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Painel Principal
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                Painel de Atendimento
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Sistema Multiagente
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant="outline" className="gap-2">
              <Activity className="w-4 h-4 text-green-500" />
              Online
            </Badge>
            <div className="flex items-center gap-2">
              <Avatar>
                <AvatarFallback>{agente.nome.substring(0, 2).toUpperCase()}</AvatarFallback>
              </Avatar>
              <div className="text-right">
                <p className="text-sm font-medium">{agente.nome}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {agente.atendimentos_ativos}/{agente.max_atendimentos} atendimentos
                </p>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Sidebar - Estatísticas e Fila */}
        <aside className="w-80 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 p-4 overflow-y-auto">
          <Tabs defaultValue="fila" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="fila">Fila</TabsTrigger>
              <TabsTrigger value="stats">Estatísticas</TabsTrigger>
            </TabsList>

            <TabsContent value="fila" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Fila de Atendimento</h3>
                <Badge>{fila.length}</Badge>
              </div>

              <Button 
                onClick={pegarProximoFila} 
                className="w-full"
                disabled={loading || agente.atendimentos_ativos >= agente.max_atendimentos}
              >
                <Zap className="w-4 h-4 mr-2" />
                Pegar Próximo
              </Button>

              <ScrollArea className="h-[calc(100vh-300px)]">
                <div className="space-y-2">
                  {fila.map((item) => (
                    <Card key={item.id} className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800">
                      <CardContent className="p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-sm">{item.cliente?.nome || 'Cliente'}</p>
                            <p className="text-xs text-slate-600 dark:text-slate-400">
                              {item.cliente?.telefone}
                            </p>
                            {item.assunto && (
                              <p className="text-xs text-slate-500 mt-1">{item.assunto}</p>
                            )}
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            {item.prioridade > 0 && (
                              <Badge variant="destructive" className="text-xs">Alta</Badge>
                            )}
                            <span className="text-xs text-slate-500">
                              <Clock className="w-3 h-3 inline mr-1" />
                              {new Date(item.iniciado_em).toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'})}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {fila.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      <CheckCircle2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Nenhum atendimento na fila</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="stats" className="space-y-4">
              <h3 className="font-semibold">Estatísticas do Sistema</h3>
              
              <div className="grid grid-cols-2 gap-2">
                <Card>
                  <CardContent className="p-3 text-center">
                    <Users className="w-6 h-6 mx-auto mb-1 text-blue-500" />
                    <p className="text-2xl font-bold">{estatisticas.em_atendimento || 0}</p>
                    <p className="text-xs text-slate-600">Em Atendimento</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-3 text-center">
                    <Clock className="w-6 h-6 mx-auto mb-1 text-yellow-500" />
                    <p className="text-2xl font-bold">{estatisticas.em_fila || 0}</p>
                    <p className="text-xs text-slate-600">Na Fila</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-3 text-center">
                    <CheckCircle2 className="w-6 h-6 mx-auto mb-1 text-green-500" />
                    <p className="text-2xl font-bold">{estatisticas.finalizados || 0}</p>
                    <p className="text-xs text-slate-600">Finalizados</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-3 text-center">
                    <Activity className="w-6 h-6 mx-auto mb-1 text-purple-500" />
                    <p className="text-2xl font-bold">{estatisticas.agentes_online || 0}</p>
                    <p className="text-xs text-slate-600">Agentes Online</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader className="p-3">
                  <CardTitle className="text-sm">Tempo Médio</CardTitle>
                </CardHeader>
                <CardContent className="p-3 pt-0 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Espera:</span>
                    <span className="font-medium">
                      {Math.floor((estatisticas.tempo_medio_espera || 0) / 60)}min
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Atendimento:</span>
                    <span className="font-medium">
                      {Math.floor((estatisticas.tempo_medio_atendimento || 0) / 60)}min
                    </span>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </aside>

        {/* Área Principal - Chat */}
        <main className="flex-1 flex flex-col">
          {atendimentoAtivo ? (
            <>
              {/* Header do Chat */}
              <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarFallback>
                        <UserCircle className="w-6 h-6" />
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h3 className="font-semibold">{atendimentoAtivo.cliente?.nome || 'Cliente'}</h3>
                      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                        <Phone className="w-3 h-3" />
                        {atendimentoAtivo.cliente?.telefone}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">#{atendimentoAtivo.id}</Badge>
                    <Button variant="destructive" size="sm" onClick={finalizarAtendimento}>
                      Finalizar
                    </Button>
                  </div>
                </div>
              </div>

              {/* Mensagens */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4 max-w-4xl mx-auto">
                  {mensagens.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.remetente === 'agente' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[70%] rounded-lg p-3 ${
                          msg.remetente === 'agente'
                            ? 'bg-blue-500 text-white'
                            : msg.remetente === 'bot'
                            ? 'bg-purple-100 dark:bg-purple-900 text-slate-900 dark:text-white'
                            : 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-white'
                        }`}
                      >
                        {msg.remetente === 'bot' && (
                          <div className="flex items-center gap-1 mb-1 text-xs opacity-75">
                            <Bot className="w-3 h-3" />
                            <span>Bot</span>
                          </div>
                        )}
                        <p className="text-sm whitespace-pre-wrap">{msg.conteudo}</p>
                        <p className="text-xs opacity-75 mt-1">
                          {new Date(msg.enviada_em).toLocaleTimeString('pt-BR', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>

              {/* Input de Mensagem */}
              <div className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 p-4">
                <form onSubmit={enviarMensagem} className="flex gap-2 max-w-4xl mx-auto">
                  <Input
                    placeholder="Digite sua mensagem..."
                    value={novaMensagem}
                    onChange={(e) => setNovaMensagem(e.target.value)}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={!novaMensagem.trim()}>
                    <Send className="w-4 h-4" />
                  </Button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500">
              <div className="text-center">
                <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <h3 className="text-xl font-semibold mb-2">Nenhum atendimento ativo</h3>
                <p className="mb-4">Pegue um atendimento da fila para começar</p>
                <Button onClick={pegarProximoFila} disabled={loading}>
                  <Zap className="w-4 h-4 mr-2" />
                  Pegar Próximo da Fila
                </Button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App

