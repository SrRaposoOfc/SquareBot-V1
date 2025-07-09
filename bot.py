import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import os
from config import *
import shutil
import squarecloud as square
import time

if DISCORD_TOKEN == "seu_token_do_discord_aqui":
    print("❌ ERRO: Token do Discord não configurado!")
    print("📝 Edite o arquivo config.py e substitua 'seu_token_do_discord_aqui' pelo seu token real")
    print("\n🔗 Para obter seu token:")
    print("1. Acesse https://discord.com/developers/applications")
    print("2. Crie uma aplicação ou selecione uma existente")
    print("3. Vá para a seção 'Bot'")
    print("4. Clique em 'Reset Token' e copie o token")
    print("5. Cole o token no arquivo config.py")
    exit(1)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.CommandInvokeError):
        original_error = error.original
        if isinstance(original_error, discord.errors.NotFound) and original_error.code == 10062:
            print(f"❌ Interação desconhecida para comando {interaction.command.name} - usuário {interaction.user.name}")
            return
        elif isinstance(original_error, discord.errors.InteractionResponded):
            print(f"❌ Interação já respondida para comando {interaction.command.name} - usuário {interaction.user.name}")
            return
    
    print(f"❌ Erro não tratado no comando {interaction.command.name if interaction.command else 'desconhecido'}: {error}")
    try:
        if not interaction.response.is_done():
            embed = discord.Embed(
                title="❌ Erro Interno",
                description="Ocorreu um erro interno. Tente novamente em alguns segundos.",
                color=COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        pass

user_keys = {}

def load_user_keys():
    try:
        with open(SERVER_KEYS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_keys():
    with open(SERVER_KEYS_FILE, 'w') as f:
        json.dump(user_keys, f, indent=2)

user_keys = load_user_keys()


TICKET_CONFIG_FILE = 'ticket_config.json'

def load_ticket_config():
    try:
        with open(TICKET_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_ticket_config(config):
    with open(TICKET_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

ticket_config = load_ticket_config()

ticket_open = {}

def get_guild_ticket_category(guild_id):
    config = ticket_config.get(str(guild_id))
    if config:
        return config.get('category_id')
    return None



def get_client(api_key):
    return square.Client(api_key)

async def list_apps(api_key):
    client = get_client(api_key)
    return await client.all_apps()

async def get_app_status(api_key, app_id):
    client = get_client(api_key)
    return await client.app_status(app_id=app_id)

async def start_app(api_key, app_id):
    client = get_client(api_key)
    return await client.app_start(app_id=app_id)

async def stop_app(api_key, app_id):
    client = get_client(api_key)
    return await client.app_stop(app_id=app_id)

async def restart_app(api_key, app_id):
    client = get_client(api_key)
    return await client.app_restart(app_id=app_id)

async def delete_app(api_key, app_id):
    client = get_client(api_key)
    app = await client.app(app_id)
    return await app.delete()

async def upload_app(api_key, zip_path):
    client = get_client(api_key)
    file = square.File(zip_path)
    return await client.upload_app(file=file)

async def get_app_logs(api_key, app_id):
    client = get_client(api_key)
    return await client.app_logs(app_id=app_id)

async def create_backup(api_key, app_id):
    client = get_client(api_key)
    return await client.app_backup(app_id=app_id)

async def list_backups(api_key, app_id):
    client = get_client(api_key)
    return await client.app_backups(app_id=app_id)




def get_square_api_key(user_id):
    return user_keys.get(str(user_id))

def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    print(f'🆔 ID do Bot: {bot.user.id}')
    print(f'🌐 Servidores conectados: {len(bot.guilds)}')
    print(f'📋 Versão: {BOT_VERSION}')
    try:
        synced = await bot.tree.sync()
        print(f'📋 Slash commands sincronizados: {len(synced)}')
    except Exception as e:
        print(f'❌ Erro ao sincronizar comandos: {e}')

@bot.tree.command(name='ping', description='Teste se o bot está online')
async def ping(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏓 Pong!",
        description="Bot está online e funcionando perfeitamente!",
        color=COLORS["success"]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='key', description='Configurar sua chave da Square Cloud')
async def key(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    print(f"🔑 Comando /key executado por {interaction.user.name} (ID: {user_id})")
    
    if user_id in user_keys:
        embed = discord.Embed(
            title="🔑 Chave Já Configurada",
            description=f"Você já possui uma chave da Square Cloud configurada.\n\n"
                       f"**Chave atual:** `{user_keys[user_id][:10]}...`\n\n"
                       f"Deseja desvincular a chave atual?",
            color=COLORS["warning"]
        )
        unlink_button = discord.ui.Button(
            label="❌ Desvincular",
            style=discord.ButtonStyle.danger
        )
        async def unlink_callback(button_interaction):
            await button_interaction.response.defer(ephemeral=True)
            if button_interaction.user.id != interaction.user.id:
                await button_interaction.followup.send(
                    "❌ Apenas quem executou o comando pode desvincular a chave!", 
                    ephemeral=True
                )
                return
            
            del user_keys[user_id]
            save_user_keys()
            print(f"🗑️ Chave desvinculada do usuário {user_id}")
            embed = discord.Embed(
                title="✅ Chave Desvinculada",
                description="Sua chave da Square Cloud foi desvinculada.\n\nExecute `/key` novamente para configurar uma nova chave.",
                color=COLORS["success"]
            )
            await button_interaction.followup.send(embed=embed, ephemeral=True)
        
        unlink_button.callback = unlink_callback
        view = discord.ui.View()
        view.add_item(unlink_button)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        return
    
    class KeyModal(discord.ui.Modal, title="🔑 Configurar Chave Square Cloud"):
        key_input = discord.ui.TextInput(
            label="Sua API Key da Square Cloud",
            placeholder="Cole sua API key aqui...",
            required=True,
            min_length=10,
            max_length=100
        )
        
        async def on_submit(self, modal_interaction: discord.Interaction):
            await modal_interaction.response.defer(ephemeral=True)
            api_key = self.key_input.value.strip()
            print(f"🔍 Validando chave para usuário {user_id}")
            print(f"🔑 Chave fornecida: {api_key[:10]}...")
            
            try:
                client = square.Client(api_key)
                apps = await client.all_apps()
                
                user_keys[user_id] = api_key
                save_user_keys()
                
                embed = discord.Embed(
                    title="✅ Chave Configurada",
                    description=f"Sua chave da Square Cloud foi configurada com sucesso!\n\n"
                               f"**Usuário:** {interaction.user.name}\n"
                               f"**Chave:** `{api_key[:10]}...`\n"
                               f"**Aplicações encontradas:** {len(apps)}\n\n"
                               f"Agora você pode usar os comandos `/status`, `/deploy` e `/delete`!",
                    color=COLORS["success"]
                )
                await modal_interaction.followup.send(embed=embed, ephemeral=True)
                
            except Exception as e:
                print(f"❌ Erro ao validar chave para usuário {user_id}: {e}")
                embed = discord.Embed(
                    title="❌ Erro ao validar chave",
                    description=f"Erro ao validar a chave da Square Cloud:\n```{str(e)}```\n\nVerifique se a chave está correta e tente novamente.",
                    color=COLORS["error"]
                )
                await modal_interaction.followup.send(embed=embed, ephemeral=True)
    
    await interaction.response.send_modal(KeyModal())


ticket_uploads = {}

@bot.tree.command(name='deploy', description='Abrir ticket para enviar ZIP de deploy')
async def deploy(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild_id)
    category_id = get_guild_ticket_category(guild_id)
    
    if not category_id:
        embed = discord.Embed(
            title="❌ Categoria não configurada",
            description="O administrador precisa configurar a categoria de tickets usando `/config`.",
            color=COLORS["error"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if user_id in ticket_open:
        channel = interaction.guild.get_channel(ticket_open[user_id])
        if channel:
            embed = discord.Embed(
                title="🔔 Ticket já aberto",
                description=f"Você já possui um ticket aberto: {channel.mention}",
                color=COLORS["warning"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        else:
            del ticket_open[user_id]
    
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="🎫 Ticket de Deploy",
        description="Seu ticket está sendo criado... aguarde!",
        color=COLORS["info"]
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
    category = interaction.guild.get_channel(int(category_id))
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
        interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
    }
    channel = await interaction.guild.create_text_channel(
        name=f"ticket-deploy-{interaction.user.name}",
        category=category,
        overwrites=overwrites,
        reason=f"Ticket de deploy para {interaction.user}"
    )
    ticket_open[user_id] = channel.id
    embed_ticket = discord.Embed(
        title="🚀 Ticket de Deploy Aberto",
        description=(
            f"Olá {interaction.user.mention}!\n\n"
            "Envie o arquivo **.zip** da sua aplicação aqui neste canal.\n"
            "O ticket será fechado automaticamente em **10 minutos**.\n"
            "Você só pode ter **1 ticket aberto** por vez.\n\n"
            ":information_source: Certifique-se que:\n"
            "O zip contenha um arquivo squarecloud.config ou squarecloud.app no formato:\n"
            "```env\n"
            "DISPLAY_NAME=nome da aplicação\n"
            "MAIN=Arquivo principal\n"
            "VERSION=recommended\n"
            "MEMORY=Minimo 512 para sites e 256 para bots\n"
            "AUTORESTART=true\n"
            "# Se for site ou API, adicione também:\n"
            "SUBDOMAIN=subdominio do seu site\n"
            "```\n"
            "O zip contenha um arquivo de dependências (requirements.txt, package.json, etc)."
        ),
        color=COLORS["info"]
    )
    embed_ticket.set_footer(text="Square Cloud • Upload seguro e privado")
    

    close_button = discord.ui.Button(
        label="🔒 Fechar Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒"
    )
    
    async def close_ticket_callback(button_interaction):
        if button_interaction.user.id != interaction.user.id:
            await button_interaction.response.send_message(
                "❌ Apenas quem abriu o ticket pode fechá-lo!", 
                ephemeral=True
            )
            return
        
        await button_interaction.response.defer(ephemeral=True)
        

        if user_id in ticket_open and ticket_open[user_id] == channel.id:
            del ticket_open[user_id]
        
        embed_close = discord.Embed(
            title="🔒 Ticket Fechado",
            description="O ticket foi fechado manualmente pelo usuário.",
            color=COLORS["warning"]
        )
        await channel.send(embed=embed_close)
        

        await asyncio.sleep(3)
        await channel.delete(reason="Ticket fechado manualmente")
    
    close_button.callback = close_ticket_callback
    view = discord.ui.View()
    view.add_item(close_button)
    
    await channel.send(embed=embed_ticket, view=view)

    async def close_ticket_later():
        await asyncio.sleep(600)
        if channel and channel.id in [c.id for c in interaction.guild.text_channels]:
            embed_close = discord.Embed(
                title="⏰ Ticket Fechado",
                description="O ticket foi fechado automaticamente após 10 minutos.",
                color=COLORS["warning"]
            )
            await channel.send(embed=embed_close)
            await channel.delete(reason="Ticket expirado")
            if user_id in ticket_open and ticket_open[user_id] == channel.id:
                del ticket_open[user_id]
    bot.loop.create_task(close_ticket_later())


UPLOADS_DIR = 'deploy_uploads'

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print(f'[DEBUG] on_message: {message.author} | Attachments: {message.attachments} | Content: {message.content}')
    user_id = str(message.author.id)
    if user_id in ticket_open and message.channel.id == ticket_open[user_id]:
        if message.attachments:
            for att in message.attachments:
                print(f'[DEBUG] Attachment filename: {att.filename}')
                if att.filename.lower().endswith('.zip'):

                    user_dir = os.path.join(UPLOADS_DIR, user_id)
                    os.makedirs(user_dir, exist_ok=True)
                    zip_path = os.path.join(user_dir, att.filename)
                    await att.save(zip_path)
                    embed1 = discord.Embed(
                        title="📦 ZIP recebido",
                        description=f"Arquivo salvo em `{zip_path}`.",
                        color=COLORS["info"]
                    )
                    await message.channel.send(embed=embed1)

                    embed2 = discord.Embed(
                        title="☁️ Enviando para a Square Cloud...",
                        description="Aguarde enquanto enviamos sua aplicação...",
                        color=COLORS["info"]
                    )
                    await message.channel.send(embed=embed2)

                    api_key = get_square_api_key(user_id)
                    if not api_key:
                        embed_err = discord.Embed(
                            title="❌ Chave não configurada",
                            description="Configure sua chave da Square Cloud com `/key` antes de fazer deploy.",
                            color=COLORS["error"]
                        )
                        await message.channel.send(embed=embed_err)
                        return
                    try:
                        result = await upload_app(api_key, zip_path)
                        

                        if hasattr(result, 'id') or (isinstance(result, dict) and result.get("status") == "success"):

                            if hasattr(result, 'id'):
                                app_id = result.id
                                app_name = getattr(result, 'name', 'N/A')
                                language = getattr(result, 'language', {})
                                ram = getattr(result, 'ram', 'N/A')
                                cpu = getattr(result, 'cpu', 'N/A')
                            else:
                                app_id = result.get('response', {}).get('id', 'N/A')
                                app_name = 'N/A'
                                language = {}
                                ram = 'N/A'
                                cpu = 'N/A'
                            
                            embed3 = discord.Embed(
                                title="✅ Aplicação enviada!",
                                description=f"Deploy realizado com sucesso!\n\n**ID da aplicação:** `{app_id}`\n**Nome:** `{app_name}`\n**Arquivo:** `{att.filename}`",
                                color=COLORS["success"]
                            )
                            embed3.add_field(name="Linguagem", value=f"`{language.get('name', 'N/A')} {language.get('version', '')}`", inline=True)
                            embed3.add_field(name="RAM", value=f"`{ram}MB`", inline=True)
                            embed3.add_field(name="CPU", value=f"`{cpu}%`", inline=True)
                            embed3.add_field(name="Resposta da API", value=f"```{result}```"[:1024], inline=False)
                        else:
                            error_msg = str(result.get('response', result)) if isinstance(result, dict) else str(result)
                            embed3 = discord.Embed(
                                title="❌ Erro no deploy",
                                description=f"Erro ao enviar aplicação:\n```{error_msg}```",
                                color=COLORS["error"]
                            )
                        await message.channel.send(embed=embed3)
                    except Exception as e:
                        print(f"[ERROR] Erro no upload: {e}")
                        embed3 = discord.Embed(
                            title="❌ Erro inesperado",
                            description=f"Erro ao enviar aplicação:\n```{str(e)}```",
                            color=COLORS["error"]
                        )
                        await message.channel.send(embed=embed3)
                    finally:

                        try:
                            shutil.rmtree(user_dir, ignore_errors=True)
                        except Exception as e:
                            print(f"[WARNING] Erro ao remover pasta temporária: {e}")
                    
                    ticket_uploads[user_id] = True
                    return
            embed_err = discord.Embed(
                title="❌ Arquivo inválido",
                description="Por favor, envie um arquivo **.zip** válido.",
                color=COLORS["error"]
            )
            await message.channel.send(embed=embed_err)
        else:
            print('[DEBUG] Nenhum anexo detectado na mensagem do ticket.')
            embed_err = discord.Embed(
                title="❌ Nenhum arquivo enviado",
                description="Envie o arquivo **.zip** da sua aplicação como anexo.",
                color=COLORS["error"]
            )
            await message.channel.send(embed=embed_err)
    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if after.author.bot:
        return
    print(f'[DEBUG] on_message_edit: {after.author} | Attachments: {after.attachments} | Content: {after.content}')
    user_id = str(after.author.id)
    if user_id in ticket_open and after.channel.id == ticket_open[user_id]:
        if after.attachments:
            for att in after.attachments:
                print(f'[DEBUG] (edit) Attachment filename: {att.filename}')
                if att.filename.lower().endswith('.zip'):

                    user_dir = os.path.join(UPLOADS_DIR, user_id)
                    os.makedirs(user_dir, exist_ok=True)
                    zip_path = os.path.join(user_dir, att.filename)
                    await att.save(zip_path)
                    embed1 = discord.Embed(
                        title="📦 ZIP recebido (edit)",
                        description=f"Arquivo salvo em `{zip_path}`.",
                        color=COLORS["info"]
                    )
                    await after.channel.send(embed=embed1)
                    embed2 = discord.Embed(
                        title="☁️ Enviando para a Square Cloud...",
                        description="Aguarde enquanto enviamos sua aplicação...",
                        color=COLORS["info"]
                    )
                    await after.channel.send(embed=embed2)
                    

                    api_key = get_square_api_key(user_id)
                    if not api_key:
                        embed_err = discord.Embed(
                            title="❌ Chave não configurada",
                            description="Configure sua chave da Square Cloud com `/key` antes de fazer deploy.",
                            color=COLORS["error"]
                        )
                        await after.channel.send(embed=embed_err)
                        return
                    
                    try:
                        result = await upload_app(api_key, zip_path)
                        

                        if hasattr(result, 'id') or (isinstance(result, dict) and result.get("status") == "success"):

                            if hasattr(result, 'id'):
                                app_id = result.id
                                app_name = getattr(result, 'name', 'N/A')
                                language = getattr(result, 'language', {})
                                ram = getattr(result, 'ram', 'N/A')
                                cpu = getattr(result, 'cpu', 'N/A')
                            else:
                                app_id = result.get('response', {}).get('id', 'N/A')
                                app_name = 'N/A'
                                language = {}
                                ram = 'N/A'
                                cpu = 'N/A'
                            
                            embed3 = discord.Embed(
                                title="✅ Aplicação enviada!",
                                description=f"Deploy realizado com sucesso!\n\n**ID da aplicação:** `{app_id}`\n**Nome:** `{app_name}`\n**Arquivo:** `{att.filename}`",
                                color=COLORS["success"]
                            )
                            embed3.add_field(name="Linguagem", value=f"`{language.get('name', 'N/A')} {language.get('version', '')}`", inline=True)
                            embed3.add_field(name="RAM", value=f"`{ram}MB`", inline=True)
                            embed3.add_field(name="CPU", value=f"`{cpu}%`", inline=True)
                            embed3.add_field(name="Resposta da API", value=f"```{result}```"[:1024], inline=False)
                        else:
                            error_msg = str(result.get('response', result)) if isinstance(result, dict) else str(result)
                            embed3 = discord.Embed(
                                title="❌ Erro no deploy",
                                description=f"Erro ao enviar aplicação:\n```{error_msg}```",
                                color=COLORS["error"]
                            )
                        await after.channel.send(embed=embed3)
                    except Exception as e:
                        print(f"[ERROR] Erro no upload (edit): {e}")
                        embed3 = discord.Embed(
                            title="❌ Erro inesperado",
                            description=f"Erro ao enviar aplicação:\n```{str(e)}```",
                            color=COLORS["error"]
                        )
                        await after.channel.send(embed=embed3)
                    finally:

                        try:
                            shutil.rmtree(user_dir, ignore_errors=True)
                        except Exception as e:
                            print(f"[WARNING] Erro ao remover pasta temporária (edit): {e}")
                    
                    ticket_uploads[user_id] = True
                    return







@bot.tree.command(name='status', description='Ver status das suas aplicações')
async def status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    print(f"📊 Comando /status executado por {interaction.user.name} (ID: {user_id})")
    
    api_key = get_square_api_key(user_id)
    if not api_key:
        print(f"❌ Usuário {user_id} não possui chave configurada")
        embed = discord.Embed(
            title="❌ Chave Não Configurada",
            description="Você não possui uma chave da Square Cloud configurada.\n\nUse o comando `/key` para configurar sua chave primeiro.",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    try:
        print(f"📡 Buscando aplicações para usuário {user_id}...")
        apps = await list_apps(api_key)
        print(f"✅ Encontradas {len(apps)} aplicações para usuário {user_id}")
        
        if not apps:
            embed = discord.Embed(
                title="📋 Status das Aplicações",
                description="Você não possui aplicações na Square Cloud.",
                color=COLORS["warning"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        options = []
        for app in apps:
            try:

                try:
                    app_name = app.tag
                except AttributeError:

                    app_str = str(app)

                    import re
                    match = re.search(r'tag=(.*?) id=', app_str)
                    app_name = match.group(1) if match else 'Sem nome'
                app_id = getattr(app, 'id', 'N/A')
                status_emoji = "🟢" if getattr(app, 'status', None) == "running" else "🔴" if getattr(app, 'status', None) == "stopped" else "🟡"
                options.append(discord.SelectOption(
                    label=app_name,
                    description=f"ID: {app_id}",
                    value=app_id,
                    emoji=status_emoji
                ))
            except Exception as e:
                print(f"[WARNING] Erro ao processar app: {e}")
                continue
        
        if not options:
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao processar as aplicações encontradas.",
                color=COLORS["error"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        select = discord.ui.Select(
            placeholder="Escolha uma aplicação para ver detalhes...",
            options=options[:25]
        )
        
        async def select_callback(select_interaction):
            await select_interaction.response.defer(ephemeral=True)
            app_id = select_interaction.data["values"][0]
            

            app = next((a for a in apps if getattr(a, 'id', None) == app_id), None)
            if not app:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Aplicação não encontrada na lista.",
                    color=COLORS["error"]
                )
                await select_interaction.followup.send(embed=embed, ephemeral=True)
                return

            try:
                app_name = app.tag
            except AttributeError:
                app_str = str(app)
                import re
                match = re.search(r'tag=(.*?) id=', app_str)
                app_name = match.group(1) if match else 'Sem nome'
            try:
                status = await app.status()
                
                embed = discord.Embed(
                    title=f"📊 Status da Aplicação: {app_name}",
                    color=COLORS["info"]
                )
                embed.add_field(name="ID", value=getattr(app, 'id', 'N/A'), inline=False)
                embed.add_field(name="Tag", value=app_name, inline=False)
                embed.add_field(name="Status", value=getattr(status, 'status', 'N/A'), inline=False)
                embed.add_field(name="CPU", value=getattr(status, 'cpu', 'N/A'), inline=False)
                embed.add_field(name="Memória", value=getattr(status, 'ram', 'N/A'), inline=False)
                embed.add_field(name="Armazenamento", value=getattr(status, 'storage', 'N/A'), inline=False)
                embed.add_field(name="Uptime", value=format_uptime(getattr(status, 'uptime', None)), inline=False)
                

                client = get_client(api_key)
                
                start_button = discord.ui.Button(label="▶️ Iniciar", style=discord.ButtonStyle.success)
                stop_button = discord.ui.Button(label="⏹️ Parar", style=discord.ButtonStyle.danger)
                restart_button = discord.ui.Button(label="🔄 Reiniciar", style=discord.ButtonStyle.primary)
                
                async def start_callback(button_interaction):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message(
                            "❌ Apenas o dono da chave pode iniciar suas aplicações!", ephemeral=True)
                        return
                    try:
                        await button_interaction.response.defer(ephemeral=True)
                        app_obj = await client.app(app_id)
                        await app_obj.start()
                        
                        embed2 = discord.Embed(
                            title="✅ Aplicação Iniciada",
                            description=f"A aplicação `{app_name}` foi iniciada com sucesso!",
                            color=COLORS["success"]
                        )
                        await button_interaction.followup.send(embed=embed2, ephemeral=True)
                    except Exception as e:
                        print(f"[ERROR] Erro ao iniciar app {app_id}: {e}")
                        embed2 = discord.Embed(
                            title="❌ Erro",
                            description=f"Erro ao iniciar aplicação:\n```{str(e)}```",
                            color=COLORS["error"]
                        )
                        await button_interaction.followup.send(embed=embed2, ephemeral=True)
                
                async def stop_callback(button_interaction):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message(
                            "❌ Apenas o dono da chave pode parar suas aplicações!", ephemeral=True)
                        return
                    try:
                        await button_interaction.response.defer(ephemeral=True)
                        app_obj = await client.app(app_id)
                        await app_obj.stop()
                        
                        embed2 = discord.Embed(
                            title="⏹️ Aplicação Parada",
                            description=f"A aplicação `{app_name}` foi parada com sucesso!",
                            color=COLORS["warning"]
                        )
                        await button_interaction.followup.send(embed=embed2, ephemeral=True)
                    except Exception as e:
                        print(f"[ERROR] Erro ao parar app {app_id}: {e}")
                        embed2 = discord.Embed(
                            title="❌ Erro",
                            description=f"Erro ao parar aplicação:\n```{str(e)}```",
                            color=COLORS["error"]
                        )
                        await button_interaction.followup.send(embed=embed2, ephemeral=True)
                
                async def restart_callback(button_interaction):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message(
                            "❌ Apenas o dono da chave pode reiniciar suas aplicações!", ephemeral=True)
                        return
                    try:
                        await button_interaction.response.defer(ephemeral=True)
                        app_obj = await client.app(app_id)
                        await app_obj.restart()
                        
                        embed2 = discord.Embed(
                            title="🔄 Aplicação Reiniciada",
                            description=f"A aplicação `{app_name}` foi reiniciada com sucesso!",
                            color=COLORS["info"]
                        )
                        await button_interaction.followup.send(embed=embed2, ephemeral=True)
                    except Exception as e:
                        print(f"[ERROR] Erro ao reiniciar app {app_id}: {e}")
                        embed2 = discord.Embed(
                            title="❌ Erro",
                            description=f"Erro ao reiniciar aplicação:\n```{str(e)}```",
                            color=COLORS["error"]
                        )
                        await button_interaction.followup.send(embed=embed2, ephemeral=True)
                
                start_button.callback = start_callback
                stop_button.callback = stop_callback
                restart_button.callback = restart_callback
                
                view = discord.ui.View()
                view.add_item(start_button)
                view.add_item(stop_button)
                view.add_item(restart_button)
                
                await select_interaction.followup.send(embed=embed, view=view, ephemeral=True)
                
            except Exception as e:
                print(f"[ERROR] Erro ao buscar status do app {app_id}: {e}")
                embed = discord.Embed(
                    title="❌ Erro",
                    description=f"Erro ao buscar status da aplicação:\n```{str(e)}```",
                    color=COLORS["error"]
                )
                await select_interaction.followup.send(embed=embed, ephemeral=True)
        
        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        
        embed = discord.Embed(
            title="📋 Suas Aplicações",
            description=f"Encontradas {len(apps)} aplicação(ões). Selecione uma para ver detalhes:",
            color=COLORS["info"]
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        print(f"❌ Erro ao buscar aplicações para usuário {user_id}: {e}")
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao buscar aplicações:\n```{str(e)}```",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='delete', description='Excluir uma aplicação')
async def delete(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    print(f"🗑️ Comando /delete executado por {interaction.user.name} (ID: {user_id})")
    
    api_key = get_square_api_key(user_id)
    if not api_key:
        print(f"❌ Usuário {user_id} não possui chave configurada")
        embed = discord.Embed(
            title="❌ Chave Não Configurada",
            description="Você não possui uma chave da Square Cloud configurada.\n\nUse o comando `/key` para configurar sua chave primeiro.",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    try:
        print(f"📡 Buscando aplicações para exclusão para usuário {user_id}...")
        apps = await list_apps(api_key)
        print(f"✅ Encontradas {len(apps)} aplicações para exclusão")
        
        if not apps:
            embed = discord.Embed(
                title="🗑️ Excluir Aplicação",
                description="Você não possui aplicações para excluir.",
                color=COLORS["warning"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        options = []
        for app in apps:
            try:

                try:
                    app_name = app.tag
                except AttributeError:

                    app_str = str(app)
                    import re
                    match = re.search(r'tag=(.*?) id=', app_str)
                    app_name = match.group(1) if match else 'Sem nome'
                app_id = getattr(app, 'id', 'N/A')
                
                options.append(discord.SelectOption(
                    label=app_name,
                    description=f"ID: {app_id}",
                    value=app_id
                ))
            except Exception as e:
                print(f"[WARNING] Erro ao processar app para exclusão: {e}")
                continue
        
        if not options:
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao processar as aplicações encontradas.",
                color=COLORS["error"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        select = discord.ui.Select(
            placeholder="Escolha uma aplicação para excluir...",
            options=options[:25]
        )
        
        async def select_callback(select_interaction):
            if select_interaction.user.id != interaction.user.id:
                await select_interaction.response.send_message(
                    "❌ Apenas o dono da chave pode excluir suas aplicações!", ephemeral=True)
                return
            
            await select_interaction.response.defer(ephemeral=True)
            app_id = select_interaction.data["values"][0]
            

            app = next((a for a in apps if getattr(a, 'id', None) == app_id), None)
            if app:
                try:
                    app_name = app.tag
                except AttributeError:
                    app_str = str(app)
                    import re
                    match = re.search(r'tag=(.*?) id=', app_str)
                    app_name = match.group(1) if match else app_id
            else:
                app_name = app_id
            
            embed = discord.Embed(
                title="⚠️ Confirmar Exclusão",
                description=f"Tem certeza que deseja excluir a aplicação **`{app_name}`**?\n\n**ID:** `{app_id}`\n\n**⚠️ Esta ação não pode ser desfeita!**",
                color=COLORS["warning"]
            )
            
            confirm_button = discord.ui.Button(label="✅ Confirmar", style=discord.ButtonStyle.danger)
            cancel_button = discord.ui.Button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
            
            async def confirm_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Apenas o dono da chave pode excluir suas aplicações!", ephemeral=True)
                    return
                
                try:
                    await button_interaction.response.defer(ephemeral=True)
                    
                    result = await delete_app(api_key, app_id)
                    

                    embed = discord.Embed(
                        title="✅ Aplicação Excluída",
                        description=f"A aplicação **`{app_name}`** foi excluída com sucesso!",
                        color=COLORS["success"]
                    )
                    
                    await button_interaction.followup.send(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    print(f"❌ Erro ao excluir aplicação {app_id}: {e}")
                    embed = discord.Embed(
                        title="❌ Erro",
                        description=f"Erro ao excluir aplicação:\n```{str(e)}```",
                        color=COLORS["error"]
                    )
                    await button_interaction.followup.send(embed=embed, ephemeral=True)
            
            async def cancel_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Apenas o dono da chave pode cancelar esta exclusão!", ephemeral=True)
                    return
                
                print(f"❌ Exclusão da aplicação {app_id} cancelada")
                embed = discord.Embed(
                    title="❌ Operação Cancelada",
                    description="A exclusão foi cancelada.",
                    color=COLORS["neutral"]
                )
                await button_interaction.response.edit_message(embed=embed, view=None)
            
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            
            view = discord.ui.View()
            view.add_item(confirm_button)
            view.add_item(cancel_button)
            
            await select_interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        
        embed = discord.Embed(
            title="🗑️ Excluir Aplicação",
            description="Selecione uma aplicação para excluir:",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        print(f"❌ Erro no comando delete para usuário {user_id}: {e}")
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao buscar aplicações:\n```{str(e)}```",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='info', description='Informações sobre o bot')
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"🤖 {BOT_NAME}",
        description="Bot oficial para gerenciamento de aplicações na Square Cloud via Discord!",
        color=COLORS["info"]
    )
    embed.add_field(name="📋 Comandos", value="`/ping` - Teste de conectividade\n`/key` - Configurar chave Square Cloud\n`/status` - Status das aplicações\n`/deploy` - Abrir ticket para deploy\n`/backup` - Gerenciar backups das aplicações\n`/domain` - Gerenciar domínios personalizados\n`/delete` - Excluir aplicações\n`/config` - Configurar categoria de tickets *(Admin)*\n`/info` - Informações do bot", inline=False)
    embed.add_field(name="🔗 Links", value="[Square Cloud](https://squarecloud.app)\n[Documentação](https://docs.squarecloud.app)", inline=False)
    embed.add_field(name="⚡ Status", value="✅ Online e funcionando", inline=False)
    embed.add_field(name="🔐 Permissões", value="Comando `/config` requer permissões de Administrador.", inline=False)
    embed.add_field(name="📊 Versão", value=f"v{BOT_VERSION}", inline=False)
    embed.set_footer(text="Desenvolvido para a competição oficial da Square Cloud")
    await interaction.response.send_message(embed=embed, ephemeral=True)


def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

@bot.tree.command(name='config', description='Configurar categoria de tickets para deploy (apenas ADM)')
@app_commands.describe(categoria='Categoria onde os tickets serão criados')
async def config(interaction: discord.Interaction, categoria: discord.CategoryChannel):
    if not is_admin(interaction):
        embed = discord.Embed(
            title="❌ Permissão Negada",
            description="Apenas administradores podem usar este comando.",
            color=COLORS["error"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    guild_id = str(interaction.guild_id)
    ticket_config[guild_id] = {"category_id": categoria.id}
    save_ticket_config(ticket_config)
    embed = discord.Embed(
        title="✅ Categoria Configurada",
        description=f"A categoria {categoria.mention} foi configurada para tickets de deploy.",
        color=COLORS["success"]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='backup', description='Gerenciar backups das suas aplicações')
async def backup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    print(f"📦 Comando /backup executado por {interaction.user.name} (ID: {user_id})")
    
    api_key = get_square_api_key(user_id)
    if not api_key:
        print(f"❌ Usuário {user_id} não possui chave configurada")
        embed = discord.Embed(
            title="❌ Chave Não Configurada",
            description="Você não possui uma chave da Square Cloud configurada.\n\nUse o comando `/key` para configurar sua chave primeiro.",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    try:
        print(f"📡 Buscando aplicações para backup...")
        apps = await list_apps(api_key)
        print(f"✅ Encontradas {len(apps)} aplicações para backup")
        
        if not apps:
            embed = discord.Embed(
                title="📦 Gerenciar Backups",
                description="Você não possui aplicações para gerenciar backups.",
                color=COLORS["warning"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        

        options = []
        for app in apps:
            try:

                try:
                    app_name = app.tag
                except AttributeError:

                    app_str = str(app)
                    import re
                    match = re.search(r'tag=(.*?) id=', app_str)
                    app_name = match.group(1) if match else 'Sem nome'
                app_id = getattr(app, 'id', 'N/A')
                
                options.append(discord.SelectOption(
                    label=app_name,
                    description=f"ID: {app_id}",
                    value=app_id
                ))
            except Exception as e:
                print(f"[WARNING] Erro ao processar app para backup: {e}")
                continue
        
        if not options:
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao processar as aplicações encontradas.",
                color=COLORS["error"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        

        def create_app_selection_embed():
            embed = discord.Embed(
                title="📦 Gerenciar Backups",
                description="Selecione uma aplicação para gerenciar seus backups:",
                color=COLORS["info"]
            )
            embed.add_field(
                name="ℹ️ Como funciona",
                value="• **Criar backup**: Gera um arquivo ZIP da aplicação\n"
                      "• **Listar backups**: Mostra todos os backups disponíveis\n"
                      "• **Download**: URL para baixar o backup\n"
                      "• **Expiração**: Backups expiram em 30 dias",
                inline=False
            )
            return embed
        

        async def create_app_info_embed(app_id, app_name):
            embed = discord.Embed(
                title=f"📦 Backups - {app_name}",
                description=f"Gerenciando backups da aplicação **{app_name}**",
                color=COLORS["info"]
            )
            
            try:

                client = get_client(api_key)
                app = await client.app(app_id)
                

                try:
                    backups = await app.all_backups()
                    backup_count = len(backups) if backups else 0
                    last_backup = "Nunca" if backup_count == 0 else "Informação não disponível"
                    
                    if backups and len(backups) > 0:

                        last_backup_obj = backups[0]
                        if hasattr(last_backup_obj, 'created_at'):
                            last_backup = str(last_backup_obj.created_at)
                        elif hasattr(last_backup_obj, 'date'):
                            last_backup = str(last_backup_obj.date)
                except:
                    backup_count = "Erro ao carregar"
                    last_backup = "Erro ao carregar"
                
                embed.add_field(name="📊 Estatísticas", value=f"**Total de backups:** {backup_count}\n**Último backup:** {last_backup}", inline=False)
                embed.add_field(name="⚠️ Limitações", value="• Máximo 12 backups por 24h\n• Rate limit: 1 backup a cada 60s\n• Expiração: 30 dias", inline=False)
                
            except Exception as e:
                embed.add_field(name="❌ Erro", value=f"Erro ao carregar informações: {str(e)}", inline=False)
            
            return embed
        

        async def create_backups_list_embed(app_id, app_name):
            embed = discord.Embed(
                title=f"📋 Lista de Backups - {app_name}",
                description=f"Backups disponíveis para **{app_name}**",
                color=COLORS["info"]
            )
            
            try:
                client = get_client(api_key)
                app = await client.app(app_id)
                
                try:
                    backups = await app.all_backups()
                    if backups and len(backups) > 0:
                        for i, backup in enumerate(backups[:10]):
                            backup_id = getattr(backup, 'id', f'Backup {i+1}')
                            created_at = getattr(backup, 'created_at', 'Data desconhecida')
                            size = getattr(backup, 'size', 'Tamanho desconhecido')
                            
                            embed.add_field(
                                name=f"📦 {backup_id}",
                                value=f"**Criado:** {created_at}\n**Tamanho:** {size}\n**Expira:** 30 dias após criação",
                                inline=True
                            )
                    else:
                        embed.add_field(name="📭 Nenhum backup", value="Esta aplicação não possui backups.", inline=False)
                        
                except Exception as e:
                    embed.add_field(name="❌ Erro", value=f"Erro ao carregar backups: {str(e)}", inline=False)
                    
            except Exception as e:
                embed.add_field(name="❌ Erro", value=f"Erro ao acessar aplicação: {str(e)}", inline=False)
            
            return embed
        

        select = discord.ui.Select(
            placeholder="Escolha uma aplicação...",
            options=options[:25]
        )
        
        async def select_callback(select_interaction):
            await select_interaction.response.defer(ephemeral=True)
            app_id = select_interaction.data["values"][0]
            

            app = next((a for a in apps if getattr(a, 'id', None) == app_id), None)
            if app:
                try:
                    app_name = app.tag
                except AttributeError:
                    app_str = str(app)
                    import re
                    match = re.search(r'tag=(.*?) id=', app_str)
                    app_name = match.group(1) if match else app_id
            else:
                app_name = app_id
            

            embed = await create_app_info_embed(app_id, app_name)
            

            create_backup_button = discord.ui.Button(label="📦 Criar Backup", style=discord.ButtonStyle.success)
            list_backups_button = discord.ui.Button(label="📋 Listar Backups", style=discord.ButtonStyle.primary)
            back_button = discord.ui.Button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary)
            
            async def create_backup_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Apenas quem executou o comando pode criar backups!", ephemeral=True)
                    return
                
                try:
                    await button_interaction.response.defer(ephemeral=True)
                    
                    client = get_client(api_key)
                    app = await client.app(app_id)
                    backup = await app.backup()
                    
                    embed_success = discord.Embed(
                        title="✅ Backup Criado!",
                        description=f"Backup da aplicação **{app_name}** foi criado com sucesso!",
                        color=COLORS["success"]
                    )
                    
                    if hasattr(backup, 'url'):
                        embed_success.add_field(name="🔗 Download", value=f"[Clique aqui para baixar]({backup.url})", inline=False)
                    else:
                        embed_success.add_field(name="📦 Backup", value=f"```{backup}```", inline=False)
                    
                    embed_success.add_field(name="⚠️ Importante", value="• O backup expira em 30 dias\n• Baixe o arquivo o quanto antes", inline=False)
                    
                    await button_interaction.followup.send(embed=embed_success, ephemeral=True)
                    
                except Exception as e:
                    print(f"[ERROR] Erro ao criar backup: {e}")
                    embed_error = discord.Embed(
                        title="❌ Erro",
                        description=f"Erro ao criar backup:\n```{str(e)}```",
                        color=COLORS["error"]
                    )
                    await button_interaction.followup.send(embed=embed_error, ephemeral=True)
            
            async def list_backups_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Apenas quem executou o comando pode listar backups!", ephemeral=True)
                    return
                
                await button_interaction.response.defer(ephemeral=True)
                
                embed_list = await create_backups_list_embed(app_id, app_name)
                

                back_to_app_button = discord.ui.Button(label="⬅️ Voltar à Aplicação", style=discord.ButtonStyle.secondary)
                
                async def back_to_app_callback(back_button_interaction):
                    if back_button_interaction.user.id != interaction.user.id:
                        await back_button_interaction.response.send_message(
                            "❌ Apenas quem executou o comando pode navegar!", ephemeral=True)
                        return
                    
                    await back_button_interaction.response.defer(ephemeral=True)
                    embed_app = await create_app_info_embed(app_id, app_name)
                    
                    view = discord.ui.View()
                    view.add_item(create_backup_button)
                    view.add_item(list_backups_button)
                    view.add_item(back_button)
                    
                    await back_button_interaction.followup.edit_message(message_id, embed=embed_app, view=view)
                
                back_to_app_button.callback = back_to_app_callback
                view_list = discord.ui.View()
                view_list.add_item(back_to_app_button)
                
                await button_interaction.followup.edit_message(message_id, embed=embed_list, view=view_list)
            
            async def back_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Apenas quem executou o comando pode navegar!", ephemeral=True)
                    return
                
                await button_interaction.response.defer(ephemeral=True)
                embed_selection = create_app_selection_embed()
                
                view_selection = discord.ui.View()
                view_selection.add_item(select)
                
                await button_interaction.followup.edit_message(message_id, embed=embed_selection, view=view_selection)
            
            create_backup_button.callback = create_backup_callback
            list_backups_button.callback = list_backups_callback
            back_button.callback = back_callback
            
            view = discord.ui.View()
            view.add_item(create_backup_button)
            view.add_item(list_backups_button)
            view.add_item(back_button)
            
            await select_interaction.followup.edit_message(message_id, embed=embed, view=view)
        
        select.callback = select_callback
        

        embed = create_app_selection_embed()
        view = discord.ui.View()
        view.add_item(select)
        

        message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        message_id = message.id
        
    except Exception as e:
        print(f"❌ Erro no comando backup para usuário {user_id}: {e}")
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao buscar aplicações:\n```{str(e)}```",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='domain', description='Gerenciar domínios personalizados das suas aplicações')
async def domain(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)
    print(f"🌐 Comando /domain executado por {interaction.user.name} (ID: {user_id})")
    
    api_key = get_square_api_key(user_id)
    if not api_key:
        print(f"❌ Usuário {user_id} não possui chave configurada")
        embed = discord.Embed(
            title="❌ Chave Não Configurada",
            description="Você não possui uma chave da Square Cloud configurada.\n\nUse o comando `/key` para configurar sua chave primeiro.",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    try:
        print(f"📡 Buscando aplicações para gerenciar domínios...")
        apps = await list_apps(api_key)
        print(f"✅ Encontradas {len(apps)} aplicações")
        
        if not apps:
            embed = discord.Embed(
                title="🌐 Gerenciar Domínios",
                description="Você não possui aplicações para gerenciar domínios.",
                color=COLORS["warning"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        

        options = []
        for app in apps:
            try:

                try:
                    app_name = app.tag
                except AttributeError:

                    app_str = str(app)
                    import re
                    match = re.search(r'tag=(.*?) id=', app_str)
                    app_name = match.group(1) if match else 'Sem nome'
                app_id = getattr(app, 'id', 'N/A')
                


                options.append(discord.SelectOption(
                    label=app_name,
                    description=f"ID: {app_id}",
                    value=app_id
                ))
            except Exception as e:
                print(f"[WARNING] Erro ao processar app para domínio: {e}")
                continue
        
        if not options:
            embed = discord.Embed(
                title="❌ Erro",
                description="Erro ao processar as aplicações encontradas.",
                color=COLORS["error"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        

        def create_app_selection_embed():
            embed = discord.Embed(
                title="🌐 Gerenciar Domínios",
                description="Selecione uma aplicação para gerenciar seu domínio personalizado:",
                color=COLORS["info"]
            )
            embed.add_field(
                name="ℹ️ Como funciona",
                value="• **Ver domínio atual**: Mostra o domínio configurado\n"
                      "• **Configurar domínio**: Define um novo domínio personalizado\n"
                      "• **Remover domínio**: Remove o domínio personalizado\n"
                      "• **Apenas sites**: Funciona apenas com aplicações web",
                inline=False
            )
            return embed
        

        async def create_domain_info_embed(app_id, app_name):
            embed = discord.Embed(
                title=f"🌐 Domínio - {app_name}",
                description=f"Gerenciando domínio da aplicação **{app_name}**",
                color=COLORS["info"]
            )
            
            try:

                client = get_client(api_key)
                app = await client.app(app_id)
                

                try:
                    domain_info = await app.domain()
                    current_domain = getattr(domain_info, 'domain', 'Nenhum') if domain_info else 'Nenhum'
                    subdomain = getattr(domain_info, 'subdomain', 'Nenhum') if domain_info else 'Nenhum'
                    
                    embed.add_field(name="🌐 Domínio Atual", value=f"**Personalizado:** `{current_domain}`\n**Subdomínio:** `{subdomain}`", inline=False)
                except:
                    embed.add_field(name="🌐 Domínio Atual", value="**Personalizado:** `Nenhum`\n**Subdomínio:** `Informação não disponível`", inline=False)
                
                embed.add_field(name="⚠️ Importante", value="• Apenas aplicações web podem ter domínio personalizado\n• O domínio deve estar configurado no DNS\n• Pode levar alguns minutos para propagar", inline=False)
                
            except Exception as e:
                embed.add_field(name="❌ Erro", value=f"Erro ao carregar informações: {str(e)}", inline=False)
            
            return embed
        

        select = discord.ui.Select(
            placeholder="Escolha uma aplicação...",
            options=options[:25]
        )
        
        async def select_callback(select_interaction):
            await select_interaction.response.defer(ephemeral=True)
            app_id = select_interaction.data["values"][0]
            

            app = next((a for a in apps if getattr(a, 'id', None) == app_id), None)
            if app:
                try:
                    app_name = app.tag
                except AttributeError:
                    app_str = str(app)
                    import re
                    match = re.search(r'tag=(.*?) id=', app_str)
                    app_name = match.group(1) if match else app_id
            else:
                app_name = app_id
            

            embed = await create_domain_info_embed(app_id, app_name)
            

            set_domain_button = discord.ui.Button(label="🌐 Configurar Domínio", style=discord.ButtonStyle.success)
            remove_domain_button = discord.ui.Button(label="🗑️ Remover Domínio", style=discord.ButtonStyle.danger)
            back_button = discord.ui.Button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary)
            
            async def set_domain_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Apenas quem executou o comando pode configurar domínios!", ephemeral=True)
                    return
                

                class DomainModal(discord.ui.Modal, title="🌐 Configurar Domínio Personalizado"):
                    domain_input = discord.ui.TextInput(
                        label="Domínio personalizado",
                        placeholder="exemplo: meusite.com.br",
                        required=True,
                        min_length=3,
                        max_length=100
                    )
                    
                    async def on_submit(self, modal_interaction: discord.Interaction):
                        await modal_interaction.response.defer(ephemeral=True)
                        domain = self.domain_input.value.strip()
                        
                        try:
                            client = get_client(api_key)
                            app = await client.app(app_id)
                            await app.set_custom_domain(domain)
                            
                            embed_success = discord.Embed(
                                title="✅ Domínio Configurado!",
                                description=f"Domínio **`{domain}`** foi configurado para **{app_name}**!",
                                color=COLORS["success"]
                            )
                            embed_success.add_field(name="⚠️ Importante", value="• Configure o DNS para apontar para a Square Cloud\n• Pode levar alguns minutos para propagar\n• Verifique se o domínio está ativo", inline=False)
                            
                            await modal_interaction.followup.send(embed=embed_success, ephemeral=True)
                            
                        except Exception as e:
                            print(f"[ERROR] Erro ao configurar domínio: {e}")
                            embed_error = discord.Embed(
                                title="❌ Erro",
                                description=f"Erro ao configurar domínio:\n```{str(e)}```",
                                color=COLORS["error"]
                            )
                            await modal_interaction.followup.send(embed=embed_error, ephemeral=True)
                
                await button_interaction.response.send_modal(DomainModal())
            
            async def remove_domain_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Apenas quem executou o comando pode remover domínios!", ephemeral=True)
                    return
                
                try:
                    await button_interaction.response.defer(ephemeral=True)
                    
                    client = get_client(api_key)
                    app = await client.app(app_id)

                    try:
                        await app.set_custom_domain(None)
                        embed_success = discord.Embed(
                            title="✅ Domínio Removido!",
                            description=f"Domínio personalizado foi removido de **{app_name}**!",
                            color=COLORS["success"]
                        )
                    except:
                        embed_success = discord.Embed(
                            title="ℹ️ Informação",
                            description=f"Para remover o domínio, configure um novo domínio ou entre em contato com o suporte.",
                            color=COLORS["info"]
                        )
                    
                    await button_interaction.followup.send(embed=embed_success, ephemeral=True)
                    
                except Exception as e:
                    print(f"[ERROR] Erro ao remover domínio: {e}")
                    embed_error = discord.Embed(
                        title="❌ Erro",
                        description=f"Erro ao remover domínio:\n```{str(e)}```",
                        color=COLORS["error"]
                    )
                    await button_interaction.followup.send(embed=embed_error, ephemeral=True)
            
            async def back_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message(
                        "❌ Apenas quem executou o comando pode navegar!", ephemeral=True)
                    return
                
                await button_interaction.response.defer(ephemeral=True)
                embed_selection = create_app_selection_embed()
                
                view_selection = discord.ui.View()
                view_selection.add_item(select)
                
                await button_interaction.followup.edit_message(message_id, embed=embed_selection, view=view_selection)
            
            set_domain_button.callback = set_domain_callback
            remove_domain_button.callback = remove_domain_callback
            back_button.callback = back_callback
            
            view = discord.ui.View()
            view.add_item(set_domain_button)
            view.add_item(remove_domain_button)
            view.add_item(back_button)
            
            await select_interaction.followup.edit_message(message_id, embed=embed, view=view)
        
        select.callback = select_callback
        

        embed = create_app_selection_embed()
        view = discord.ui.View()
        view.add_item(select)
        

        message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        message_id = message.id
        
    except Exception as e:
        print(f"❌ Erro no comando domain para usuário {user_id}: {e}")
        embed = discord.Embed(
            title="❌ Erro",
            description=f"Erro ao buscar aplicações:\n```{str(e)}```",
            color=COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

def format_uptime(uptime):
    if not uptime or not isinstance(uptime, (int, float)):
        return "N/A"
    now_ms = int(time.time() * 1000)

    if uptime > now_ms // 2:
        seconds = int((now_ms - uptime) // 1000)
    else:
        seconds = int(uptime // 1000)
    if seconds < 0:
        seconds = 0
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d > 0:
        return f"{d}d {h}h {m}m {s}s"
    elif h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    else:
        return f"{s}s"

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN) 
