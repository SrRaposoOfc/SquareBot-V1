# 🤖 Square Cloud Bot

Bot para gerenciamento de aplicações na Square Cloud via Discord usando o SDK oficial Python.

## ✨ Funcionalidades

- **🔑 Configuração de Chave API**: Configure sua chave da Square Cloud de forma segura
- **📊 Status das Aplicações**: Visualize status, CPU, memória, armazenamento e uptime
- **🚀 Deploy via Ticket**: Sistema de tickets para upload seguro de aplicações
- **📦 Gerenciamento de Backups**: Crie e liste backups das suas aplicações
- **🌐 Domínios Personalizados**: Configure domínios personalizados para suas aplicações web
- **⚡ Controle Total**: Iniciar, parar, reiniciar e excluir aplicações
- **🛡️ Segurança**: Comandos privados e validação de permissões

## 🚀 Comandos Disponíveis

| Comando | Descrição | Permissão |
|---------|-----------|-----------|
| `/ping` | Teste de conectividade | Todos |
| `/key` | Configurar chave Square Cloud | Todos |
| `/status` | Status das aplicações | Todos |
| `/deploy` | Abrir ticket para deploy | Todos |
| `/backup` | Gerenciar backups das aplicações | Todos |
| `/domain` | Gerenciar domínios personalizados | Todos |
| `/delete` | Excluir aplicações | Todos |
| `/info` | Informações do bot | Todos |
| `/config` | Configurar categoria de tickets | Admin |

## 🔧 Configuração

1. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

2. **Configure o arquivo `config.py`**:
```python
DISCORD_TOKEN = "seu_token_do_discord_aqui"  # Token do seu bot Discord
BOT_PREFIX = "!"
BOT_NAME = "SquareCloud Bot"
BOT_VERSION = "1.0.0"
```

3. **Execute o bot**:
```bash
python bot.py
```

4. **Configure sua chave da Square Cloud**:
   - Use o comando `/key` no Discord
   - Cole sua API key da Square Cloud
   - A chave será salva de forma segura

**⚠️ Importante**: Apenas o token do Discord precisa ser configurado no arquivo. A API key da Square Cloud é configurada via comando `/key` no Discord.

## 📋 Melhorias Implementadas

### 🔄 Migração Completa para SDK Oficial
- ✅ Implementado SDK oficial `squarecloud-api`
- ✅ Métodos assíncronos para todas as operações
- ✅ Tratamento correto de retornos da API

### 🛠️ Tratamento de Erros Aprimorado
- ✅ Logs detalhados para debug
- ✅ Mensagens de erro mais claras
- ✅ Validação robusta de dados
- ✅ Tratamento de exceções específicas

### 📊 Interface Melhorada
- ✅ Embeds com informações completas
- ✅ Resposta da API sempre visível para debug
- ✅ Botões de ação intuitivos
- ✅ Confirmações de segurança

### 🔐 Segurança e Validação
- ✅ Verificação de permissões
- ✅ Validação de chaves API
- ✅ Limpeza automática de arquivos temporários
- ✅ Controle de acesso por usuário

### 📦 Novas Funcionalidades
- ✅ Sistema completo de backups
- ✅ Gerenciamento de domínios personalizados
- ✅ Painéis interativos com botões
- ✅ Navegação entre telas

## 🎯 Funcionalidades Principais

### 📦 Sistema de Deploy
- Criação automática de tickets
- Upload seguro de arquivos ZIP
- Validação de formato de arquivo
- Limpeza automática de arquivos temporários

### 📊 Monitoramento
- Status em tempo real das aplicações
- Métricas de CPU, memória e armazenamento
- Uptime formatado legível
- Controles de start/stop/restart

### 📦 Gerenciamento de Backups
- Criação de backups das aplicações
- Listagem de backups disponíveis
- Informações de tamanho e data de criação
- Rate limiting e limitações respeitadas

### 🌐 Domínios Personalizados
- Configuração de domínios personalizados
- Visualização de domínio atual
- Remoção de domínios configurados
- Suporte para aplicações web

### 🗑️ Gerenciamento
- Exclusão segura com confirmação
- Listagem de todas as aplicações
- Busca por ID e nome
- Validação de propriedade

## 🔍 Debug e Logs

O bot agora inclui logs detalhados para facilitar o debug:

```
[DEBUG] Comando /status executado por Usuario (ID: 123456789)
[DEBUG] Buscando aplicações para usuário 123456789...
[DEBUG] App: MinhaApp (ID: abc123) - Status: running
[DEBUG] Usuário selecionou app ID: abc123
[DEBUG] Status obtido: <Status object>
```

## 🛡️ Tratamento de Erros

- **40060**: "Interaction has already been acknowledged" - Corrigido com defer imediato
- **404 10062**: "Unknown interaction" - Evitado com defer antes de operações demoradas
- **API Errors**: Tratados com mensagens claras e logs detalhados
- **Tratamento Global**: Handler global para capturar erros não tratados
- **Validação de Interações**: Verificação de estado antes de responder

## 📈 Performance

- ✅ Operações assíncronas
- ✅ Defer imediato para evitar timeouts
- ✅ Limpeza automática de recursos
- ✅ Cache de dados quando apropriado
- ✅ Tratamento de erros otimizado
- ✅ Interface responsiva com botões

## 🔗 Links Úteis

- [Square Cloud](https://squarecloud.app)
- [Documentação Square Cloud](https://docs.squarecloud.app)
- [SDK Python](https://pypi.org/project/squarecloud/)

## 📝 Versão

**v1.0.0** - Bot totalmente integrado ao SDK oficial da Square Cloud

---

Desenvolvido por Sr.Raposo para a competição oficial da Square Cloud 🏆 
