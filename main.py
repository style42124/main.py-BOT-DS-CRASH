import os
import random
import sqlite3
import json
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput

# ==================== КОНСТАНТЫ (ВСЁ В ОДНОМ ФАЙЛЕ) ====================

# Discord
DISCORD_TOKEN = "MTQ3MjYxMTY0MjM3NzUwNjk5Ng.GcSjel.HR_LkzhvKzoWbUb2n-O_4bI7vP8QZ-LqMqqceg"
PREFIX = "!"
OWNER_ID = 909100136074993694
DEPUTY_OWNER_IDS = [1471043344728850539, 987654321]
ADMIN_TICKET_ROLE_IDS = [1471043344728850539, 222222222]

# VK
VK_TOKEN = "vk1.a.ARTqCjL7kgSmW7tx7BrJQqmPPZzEYV9Vf4LXMLSputsvmMv3hQGquehJa-1N9HrHAOABCAVtXjs0pZftg75JCshpVaiXpu6cj66A2l62OdVRv6qBtMIiG0rheK6Qcsk9hYh2Q6ArTYwmJBaWnyTSIiKGWVciitm52ZYfKU_MH34oYx0n8j4nh7rIMh_SjjVBeWoJ-sec-bVDqE_CcpUo5A"
VK_PEER_ID = 2000000131  # ID конференции техподдержки

# База данных
DB_PATH = "data/bot.db"

# Цвета для embed
COLOR_SUCCESS = 0x2ecc71
COLOR_ERROR = 0xe74c3c
COLOR_INFO = 0x3498db
COLOR_WARN = 0xf39c12
COLOR_GOLD = 0xffd700
COLOR_ADMIN = 0x9b59b6
COLOR_PINK = 0xff9a9e
COLOR_PURPLE = 0x9b59b6

# Экономика
STARTING_BALANCE = 1000
DAILY_REWARD = 500
WORK_REWARD = (100, 300)
CRIME_REWARD = (200, 500)
BET_MIN = 100
BET_MAX = 10000

# Статусы для анимации (с аниме-тематикой)
STATUSES = [
    "👑 !help | Команды бота",
    "💰 !balance | Баланс",
    "🎮 !casino | Казино",
    "⚔️ Модерация",
    "🎫 Embed ticket",
    "🔐 Приватные комнаты",
    "📊 !serverinfo",
    "👥 !userinfo",
    "🛍️ !shop",
    "💎 !leaderboard",
    "🌟 !daily",
    "🎯 Админ-панель",
    "📞 !tech - поддержка",
    "✨ by styleniw"
]

# Уровни администрации (с красивыми названиями и эмодзи)
LEVELS = {
    1: {"name": "🌟 1 LVL Admin", "emoji": "🌟"},
    2: {"name": "🛡️ 2 LVL Admin", "emoji": "🛡️"},
    3: {"name": "⚔️ 3 LVL Admin", "emoji": "⚔️"},
    4: {"name": "🔥 4 LVL Admin", "emoji": "🔥"},
    5: {"name": "👑 5 LVL Admin", "emoji": "👑"},
    6: {"name": "📚 6 LVL Admin", "emoji": "📚"},
    7: {"name": "💻 7 LVL Admin", "emoji": "💻"},
    8: {"name": "🎯 8 LVL Admin", "emoji": "🎯"},
    9: {"name": "✨ Верховные Админы", "emoji": "✨"},
    10: {"name": "👑 Владелец бота", "emoji": "👑"}
}

# Аниме-иконки для embed (ссылки с Pinterest)
ANIME_ICONS = {
    "economy": "https://i.pinimg.com/originals/6d/8b/2e/6d8b2e5a7f5b3b8e6d8b2e5a7f5b3b8e.jpg",
    "admin": "https://i.pinimg.com/originals/7c/3d/9a/7c3d9a4f5e6d7c8b9a0b1c2d3e4f5a6b.jpg",
    "mod": "https://i.pinimg.com/originals/2a/4c/7d/2a4c7d8e9f0a1b2c3d4e5f6a7b8c9d0e.jpg",
    "fun": "https://i.pinimg.com/originals/8b/5d/2f/8b5d2f1a2b3c4d5e6f7a8b9c0d1e2f3a.jpg",
    "tech": "https://i.pinimg.com/originals/9c/7d/4e/9c7d4e5f6a7b8c9d0e1f2a3b4c5d6e7f.jpg",
    "ticket": "https://i.pinimg.com/originals/1b/3c/5d/1b3c5d6e7f8a9b0c1d2e3f4a5b6c7d8e.jpg",
    "profile": "https://i.pinimg.com/originals/3d/4e/5f/3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a.jpg",
    "leaderboard": "https://i.pinimg.com/originals/5e/6f/7a/5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b.jpg",
    "welcome": "https://i.pinimg.com/originals/7f/8a/9b/7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c.jpg"
}

# ==================== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ====================

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Таблица пользователей (экономика)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 1000,
            bank INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            last_daily TIMESTAMP,
            last_work TIMESTAMP,
            reputation INTEGER DEFAULT 0,
            title TEXT DEFAULT 'Новичок'
        )
    ''')

    # Таблица администраторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            level INTEGER DEFAULT 1,
            position TEXT DEFAULT 'Стажёр',
            access TEXT DEFAULT '{}',  -- JSON с правами
            appointed_by INTEGER,
            appointed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_promoted TIMESTAMP,
            last_demoted TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # История изменений администраторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,                -- promote, demote, setpost, setaccess, fire
            old_level INTEGER,
            new_level INTEGER,
            old_position TEXT,
            new_position TEXT,
            old_access TEXT,
            new_access TEXT,
            reason TEXT,
            moderator_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # История никнеймов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nickname_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            old_nick TEXT,
            new_nick TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Архив снятых администраторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            level INTEGER,
            position TEXT,
            access TEXT,
            fired_by INTEGER,
            fired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )
    ''')

    # Инвентарь
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            quantity INTEGER DEFAULT 1,
            rarity TEXT DEFAULT 'common',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Логи сервера
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            action TEXT,
            user_id INTEGER,
            target_id INTEGER,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Мьюты
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            muted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            muted_until TIMESTAMP,
            moderator_id INTEGER
        )
    ''')

    # Варны
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            warned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            moderator_id INTEGER
        )
    ''')

    # Розыгрыши
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            message_id INTEGER,
            channel_id INTEGER,
            prize TEXT,
            winners_count INTEGER,
            ends_at TIMESTAMP,
            host_id INTEGER,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # Приватные комнаты
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            channel_id INTEGER,
            voice_channel_id INTEGER,
            owner_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Жалобы на администраторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            ticket_number INTEGER,
            ticket_channel_id INTEGER,
            complainant_id INTEGER,
            target_admin_id INTEGER,
            reason TEXT,
            complaint_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'open',
            punishment_form_submitted BOOLEAN DEFAULT 0
        )
    ''')

    # Доказательства для жалоб
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            evidence_type TEXT,
            content TEXT,
            evidence_link TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES admin_tickets(id)
        )
    ''')

    # Форма наказания
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS punishment_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            punishment_type TEXT,
            evidence_text TEXT,
            evidence_link TEXT,
            submitted_by INTEGER,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES admin_tickets(id)
        )
    ''')

    # Настройки каналов для жалоб
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_ticket_settings (
            guild_id INTEGER PRIMARY KEY,
            ticket_channel_id INTEGER,
            ticket_category_id INTEGER,
            ticket_counter INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (utils) ====================

def get_user_balance(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else STARTING_BALANCE

def add_money(user_id: int, amount: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def remove_money(user_id: int, amount: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def log_action(guild_id: int, action: str, user_id: int, target_id: int, reason: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO server_logs (guild_id, action, user_id, target_id, reason) VALUES (?, ?, ?, ?, ?)",
        (guild_id, action, user_id, target_id, reason)
    )
    conn.commit()
    conn.close()

def get_admin_level(user_id: int) -> Optional[int]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT level FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_admin_level(user_id: int, level: int, moderator_id: int, reason: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id, level, appointed_by) VALUES (?, ?, ?)", (user_id, level, moderator_id))
    cursor.execute("SELECT level, position, access FROM admins WHERE user_id = ?", (user_id,))
    old = cursor.fetchone()
    old_level, old_pos, old_access = old if old else (None, None, "{}")
    cursor.execute("UPDATE admins SET level = ?, last_promoted = ? WHERE user_id = ?", (level, datetime.now().isoformat(), user_id))
    cursor.execute(
        "INSERT INTO admin_history (user_id, action, old_level, new_level, old_position, new_position, old_access, new_access, reason, moderator_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, "level_change", old_level, level, old_pos, old_pos, old_access, old_access, reason, moderator_id)
    )
    conn.commit()
    conn.close()

def set_admin_position(user_id: int, position: str, moderator_id: int, reason: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id, appointed_by) VALUES (?, ?)", (user_id, moderator_id))
    cursor.execute("SELECT level, position, access FROM admins WHERE user_id = ?", (user_id,))
    old = cursor.fetchone()
    old_level, old_pos, old_access = old if old else (None, None, "{}")
    cursor.execute("UPDATE admins SET position = ? WHERE user_id = ?", (position, user_id))
    cursor.execute(
        "INSERT INTO admin_history (user_id, action, old_level, new_level, old_position, new_position, old_access, new_access, reason, moderator_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, "position_change", old_level, old_level, old_pos, position, old_access, old_access, reason, moderator_id)
    )
    conn.commit()
    conn.close()

def set_admin_access(user_id: int, access_dict: Dict, moderator_id: int, reason: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id, appointed_by) VALUES (?, ?)", (user_id, moderator_id))
    cursor.execute("SELECT level, position, access FROM admins WHERE user_id = ?", (user_id,))
    old = cursor.fetchone()
    old_level, old_pos, old_access = old if old else (None, None, "{}")
    new_access = json.dumps(access_dict)
    cursor.execute("UPDATE admins SET access = ? WHERE user_id = ?", (new_access, user_id))
    cursor.execute(
        "INSERT INTO admin_history (user_id, action, old_level, new_level, old_position, new_position, old_access, new_access, reason, moderator_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, "access_change", old_level, old_level, old_pos, old_pos, old_access, new_access, reason, moderator_id)
    )
    conn.commit()
    conn.close()

def fire_admin(user_id: int, moderator_id: int, reason: str = ""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, level, position, access FROM admins WHERE user_id = ?", (user_id,))
    admin = cursor.fetchone()
    if admin:
        # Сохраняем в архив
        cursor.execute(
            "INSERT INTO admin_archive (user_id, user_name, level, position, access, fired_by, reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, str(user_id), admin[1], admin[2], admin[3], moderator_id, reason)
        )
        # Удаляем из активных
        cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        cursor.execute(
            "INSERT INTO admin_history (user_id, action, reason, moderator_id) VALUES (?, ?, ?, ?)",
            (user_id, "fire", reason, moderator_id)
        )
    conn.commit()
    conn.close()

def get_admin_history(user_id: int) -> List[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_weekly_history() -> List[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cursor.execute("SELECT * FROM admin_history WHERE timestamp > ? ORDER BY timestamp DESC", (week_ago,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_all_admins() -> List[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, level, position, access FROM admins WHERE is_active = 1")
    result = cursor.fetchall()
    conn.close()
    return result

def log_nickname_change(user_id: int, old_nick: Optional[str], new_nick: Optional[str]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO nickname_history (user_id, old_nick, new_nick) VALUES (?, ?, ?)",
        (user_id, old_nick, new_nick)
    )
    conn.commit()
    conn.close()

def get_nickname_history(user_id: int) -> List[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nickname_history WHERE user_id = ? ORDER BY changed_at DESC", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

# ==================== КЛАССЫ ДЛЯ КНОПОК (ЖАЛОБЫ) ====================

class TicketView(View):
    def __init__(self, bot, guild_id, category_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.category_id = category_id

    @discord.ui.button(label="📝 Создать жалобу", style=discord.ButtonStyle.danger, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(TicketModal(self.bot, self.guild_id, self.category_id))

class TicketModal(Modal, title="📝 Подача жалобы на администратора"):
    def __init__(self, bot, guild_id, category_id):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id
        self.category_id = category_id

    admin_name = TextInput(label="Ник администратора", placeholder="Укажите ник администратора", max_length=100)
    reason = TextInput(label="Причина жалобы", placeholder="Опишите ситуацию", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        guild = self.bot.get_guild(self.guild_id)
        category = guild.get_channel(self.category_id)
        if not category:
            await interaction.response.send_message("Ошибка: категория не найдена", ephemeral=True)
            return

        # Создаём канал
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_member(OWNER_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for dep_id in DEPUTY_OWNER_IDS:
            dep = guild.get_member(dep_id)
            if dep:
                overwrites[dep] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        for role_id in ADMIN_TICKET_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_number = random.randint(1000, 9999)
        channel = await category.create_text_channel(f"жалоба-{ticket_number}", overwrites=overwrites)

        embed = discord.Embed(title=f"🎫 Жалоба #{ticket_number}", color=COLOR_ERROR)
        embed.add_field(name="Отправитель", value=interaction.user.mention)
        embed.add_field(name="Нарушитель", value=self.admin_name.value)
        embed.add_field(name="Причина", value=self.reason.value, inline=False)
        embed.set_thumbnail(url=ANIME_ICONS["ticket"])
        await channel.send(embed=embed)

        await interaction.response.send_message(f"✅ Жалоба создана: {channel.mention}", ephemeral=True)

class EvidenceView(View):
    def __init__(self, bot, guild_id, category_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.category_id = category_id

    @discord.ui.button(label="📎 Подать доказательство", style=discord.ButtonStyle.blurple, custom_id="create_evidence")
    async def create_evidence(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(EvidenceModal(self.bot, self.guild_id, self.category_id))

class EvidenceModal(Modal, title="📎 Подача доказательства нарушения"):
    def __init__(self, bot, guild_id, category_id):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id
        self.category_id = category_id

    player_name = TextInput(label="Ник нарушителя", placeholder="Кто нарушил?", max_length=100)
    violation = TextInput(label="Тип нарушения", placeholder="Например: оскорбления", max_length=100)
    description = TextInput(label="Описание", placeholder="Подробности", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        guild = self.bot.get_guild(self.guild_id)
        category = guild.get_channel(self.category_id)
        if not category:
            await interaction.response.send_message("Ошибка", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_member(OWNER_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        for dep_id in DEPUTY_OWNER_IDS:
            dep = guild.get_member(dep_id)
            if dep:
                overwrites[dep] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        evidence_number = random.randint(1000, 9999)
        channel = await category.create_text_channel(f"доказательство-{evidence_number}", overwrites=overwrites)

        embed = discord.Embed(title=f"📎 Доказательство #{evidence_number}", color=COLOR_INFO)
        embed.add_field(name="Отправитель", value=interaction.user.mention)
        embed.add_field(name="Нарушитель", value=self.player_name.value)
        embed.add_field(name="Тип", value=self.violation.value)
        embed.add_field(name="Описание", value=self.description.value, inline=False)
        embed.set_thumbnail(url=ANIME_ICONS["ticket"])
        await channel.send(embed=embed)

        await interaction.response.send_message(f"✅ Доказательство создано: {channel.mention}", ephemeral=True)

# ==================== СОЗДАНИЕ БОТА ====================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ==================== АНИМАЦИЯ СТАТУСА ====================

@tasks.loop(seconds=12)
async def change_status():
    status_text = STATUSES[change_status.current % len(STATUSES)]
    activity = discord.Activity(type=discord.ActivityType.watching, name=status_text)
    await bot.change_presence(status=discord.Status.online, activity=activity)
    change_status.current += 1
change_status.current = 0

# ==================== СОБЫТИЯ ====================

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен!")
    print(f"Серверов: {len(bot.guilds)}")
    print(f"Пользователей: {sum(g.member_count for g in bot.guilds)}")
    if not change_status.is_running():
        change_status.start()

@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        log_nickname_change(after.id, before.nick, after.nick)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="❌ Недостаточно прав", color=COLOR_ERROR)
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="❌ Не хватает аргументов", description=f"Использование: `{PREFIX}{ctx.command.name} {ctx.command.signature}`", color=COLOR_ERROR)
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CheckFailure):
        embed = discord.Embed(title="❌ У вас нет доступа к этой команде", color=COLOR_ERROR)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Ошибка", description=str(error), color=COLOR_ERROR)
        await ctx.send(embed=embed)
        raise error

# ==================== КОМАНДЫ ====================

# ----- Общие команды -----

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="📚 Справка по командам", description=f"Префикс: `{PREFIX}`", color=COLOR_INFO)
    embed.add_field(name="💰 Экономика", value="`balance`, `daily`, `work`, `crime`, `casino`, `give`, `leaderboard`", inline=False)
    embed.add_field(name="⚔️ Модерация", value="`kick`, `ban`, `unban`, `mute`, `unmute`, `clear`, `slowmode`, `lock`, `unlock`, `announce`", inline=False)
    embed.add_field(name="🎫 Жалобы", value="`admticketsetup`, `evidencesetup` (требуют прав)", inline=False)
    embed.add_field(name="🛠️ Администрирование", value="`admlist`, `cfginfo`, `cnick`, `me`, `ahistory`, `hadm`, `setpost`, `uplvl`, `archives`, `ratingall`, `setdostup`, `fire`", inline=False)
    embed.add_field(name="🎉 Развлечения", value="`joke`, `compliment`, `8ball`, `roll`, `choose`, `avatar`, `love`", inline=False)
    embed.add_field(name="📞 Техподдержка", value="`tech <текст>` - отправить сообщение в ВК", inline=False)
    embed.add_field(name="ℹ️ Другое", value="`ping`, `serverinfo`, `userinfo`, `stats`", inline=False)
    embed.set_thumbnail(url=ANIME_ICONS["welcome"])
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    embed = discord.Embed(title="🏓 Понг!", description=f"{round(bot.latency*1000)}ms", color=COLOR_SUCCESS)
    embed.set_thumbnail(url=ANIME_ICONS["fun"])
    await ctx.send(embed=embed)

@bot.command(name="serverinfo")
async def serverinfo(ctx):
    embed = discord.Embed(title=f"📊 Информация о сервере {ctx.guild.name}", color=COLOR_INFO)
    embed.add_field(name="👑 Владелец", value=ctx.guild.owner.mention)
    embed.add_field(name="👥 Участников", value=ctx.guild.member_count)
    embed.add_field(name="📅 Создан", value=f"<t:{int(ctx.guild.created_at.timestamp())}:D>")
    embed.add_field(name="💬 Каналов", value=len(ctx.guild.channels))
    embed.add_field(name="🎭 Ролей", value=len(ctx.guild.roles))
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    await ctx.send(embed=embed)

@bot.command(name="userinfo")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 Информация о {member.display_name}", color=member.color)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id)
    embed.add_field(name="📅 Присоединился", value=f"<t:{int(member.joined_at.timestamp())}:R>")
    embed.add_field(name="📝 Зарегистрирован", value=f"<t:{int(member.created_at.timestamp())}:R>")
    roles = [r.mention for r in member.roles[1:6]]
    embed.add_field(name="🎭 Роли", value=" ".join(roles) if roles else "Нет")
    await ctx.send(embed=embed)

@bot.command(name="stats")
async def stats(ctx):
    embed = discord.Embed(title="📊 Статистика бота", color=COLOR_INFO)
    embed.add_field(name="🖥️ Серверов", value=len(bot.guilds))
    embed.add_field(name="👥 Пользователей", value=sum(g.member_count for g in bot.guilds))
    embed.add_field(name="🔌 Пинг", value=f"{round(bot.latency*1000)}ms")
    embed.add_field(name="⏰ Запущен", value=f"<t:{int(datetime.now().timestamp())}:R>")
    embed.set_thumbnail(url=ANIME_ICONS["profile"])
    await ctx.send(embed=embed)

# ----- Экономика -----

@bot.command(name="balance", aliases=["bal"])
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    bal = get_user_balance(member.id)
    embed = discord.Embed(title=f"💰 Баланс {member.display_name}", description=f"**{bal}** 💵", color=COLOR_GOLD)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text="Используйте !daily для ежедневного бонуса")
    await ctx.send(embed=embed)

@bot.command(name="daily")
async def daily(ctx):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (ctx.author.id,))
    cursor.execute("SELECT last_daily FROM users WHERE user_id = ?", (ctx.author.id,))
    last = cursor.fetchone()[0]
    if last:
        last_time = datetime.fromisoformat(last)
        if datetime.now() - last_time < timedelta(days=1):
            remaining = timedelta(days=1) - (datetime.now() - last_time)
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes = remainder // 60
            embed = discord.Embed(title="⏰ Ежедневная награда уже получена", description=f"Приходи через {hours}ч {minutes}м", color=COLOR_WARN)
            conn.close()
            return await ctx.send(embed=embed)
    cursor.execute("UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?", (DAILY_REWARD, datetime.now().isoformat(), ctx.author.id))
    conn.commit()
    conn.close()
    embed = discord.Embed(title="✅ Ежедневная награда", description=f"Вы получили **{DAILY_REWARD}** 💵", color=COLOR_SUCCESS)
    embed.set_thumbnail(url=ANIME_ICONS["economy"])
    await ctx.send(embed=embed)

@bot.command(name="work")
async def work(ctx):
    reward = random.randint(*WORK_REWARD)
    add_money(ctx.author.id, reward)
    embed = discord.Embed(title="💼 Работа", description=f"Вы заработали **{reward}** 💵", color=COLOR_SUCCESS)
    embed.set_thumbnail(url=ANIME_ICONS["economy"])
    await ctx.send(embed=embed)

@bot.command(name="crime")
async def crime(ctx):
    if random.random() > 0.5:
        reward = random.randint(*CRIME_REWARD)
        add_money(ctx.author.id, reward)
        embed = discord.Embed(title="🦹 Успешное преступление", description=f"Вы украли **{reward}** 💵", color=COLOR_GOLD)
    else:
        fine = random.randint(100, 300)
        remove_money(ctx.author.id, fine)
        embed = discord.Embed(title="👮 Вас поймали", description=f"Штраф **{fine}** 💵", color=COLOR_ERROR)
    embed.set_thumbnail(url=ANIME_ICONS["fun"])
    await ctx.send(embed=embed)

@bot.command(name="casino")
async def casino(ctx, bet: int):
    bal = get_user_balance(ctx.author.id)
    if bet < BET_MIN or bet > BET_MAX:
        return await ctx.send(embed=discord.Embed(title="❌ Неверная ставка", description=f"От {BET_MIN} до {BET_MAX}", color=COLOR_ERROR))
    if bal < bet:
        return await ctx.send(embed=discord.Embed(title="❌ Недостаточно средств", color=COLOR_ERROR))
    if random.random() > 0.45:
        win = int(bet * 1.5)
        add_money(ctx.author.id, win)
        embed = discord.Embed(title="🎰 Вы выиграли!", description=f"+{win} 💵", color=COLOR_SUCCESS)
    else:
        remove_money(ctx.author.id, bet)
        embed = discord.Embed(title="🎰 Вы проиграли", description=f"-{bet} 💵", color=COLOR_ERROR)
    embed.set_thumbnail(url=ANIME_ICONS["economy"])
    await ctx.send(embed=embed)

@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send(embed=discord.Embed(title="❌ Сумма должна быть положительной", color=COLOR_ERROR))
    bal = get_user_balance(ctx.author.id)
    if bal < amount:
        return await ctx.send(embed=discord.Embed(title="❌ Недостаточно средств", color=COLOR_ERROR))
    remove_money(ctx.author.id, amount)
    add_money(member.id, amount)
    embed = discord.Embed(title="✅ Перевод выполнен", description=f"Вы отправили {member.mention} **{amount}** 💵", color=COLOR_SUCCESS)
    embed.set_thumbnail(url=ANIME_ICONS["economy"])
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["top"])
async def leaderboard(ctx):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
    top = cursor.fetchall()
    conn.close()
    embed = discord.Embed(title="🏆 Топ богачей", color=COLOR_GOLD)
    for i, (uid, bal) in enumerate(top, 1):
        user = bot.get_user(uid)
        name = user.display_name if user else f"Unknown ({uid})"
        embed.add_field(name=f"{i}. {name}", value=f"{bal} 💵", inline=False)
    embed.set_thumbnail(url=ANIME_ICONS["leaderboard"])
    await ctx.send(embed=embed)

# ----- Модерация -----

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Не указана"):
    if member.top_role >= ctx.author.top_role:
        return await ctx.send(embed=discord.Embed(title="❌ Нельзя кикнуть этого пользователя", color=COLOR_ERROR))
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Кик", description=f"{member.mention} кикнут", color=COLOR_WARN)
    embed.add_field(name="Причина", value=reason)
    embed.set_thumbnail(url=ANIME_ICONS["mod"])
    await ctx.send(embed=embed)

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    if member.top_role >= ctx.author.top_role:
        return await ctx.send(embed=discord.Embed(title="❌ Нельзя забанить этого пользователя", color=COLOR_ERROR))
    await member.ban(reason=reason)
    embed = discord.Embed(title="🚫 Бан", description=f"{member.mention} забанен", color=COLOR_ERROR)
    embed.add_field(name="Причина", value=reason)
    embed.set_thumbnail(url=ANIME_ICONS["mod"])
    await ctx.send(embed=embed)

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    embed = discord.Embed(title="✅ Разбанен", description=f"{user.mention} разбанен", color=COLOR_SUCCESS)
    embed.set_thumbnail(url=ANIME_ICONS["mod"])
    await ctx.send(embed=embed)

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount+1)
    embed = discord.Embed(title="🗑️ Очистка", description=f"Удалено {amount} сообщений", color=COLOR_SUCCESS)
    await ctx.send(embed=embed, delete_after=5)

@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int = 0):
    await ctx.channel.edit(slowmode_delay=seconds)
    embed = discord.Embed(title="⏱️ Слоумод", description=f"Установлен {seconds} сек", color=COLOR_INFO)
    await ctx.send(embed=embed)

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 Канал заблокирован", color=COLOR_WARN)
    await ctx.send(embed=embed)

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 Канал разблокирован", color=COLOR_SUCCESS)
    await ctx.send(embed=embed)

@bot.command(name="announce")
@commands.has_permissions(administrator=True)
async def announce(ctx, *, message):
    embed = discord.Embed(title="📢 Объявление", description=message, color=COLOR_INFO)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    embed.set_thumbnail(url=ANIME_ICONS["welcome"])
    await ctx.send(embed=embed)

@bot.command(name="admininfo")
@commands.has_permissions(administrator=True)
async def admininfo(ctx):
    embed = discord.Embed(title="🔐 Админ-панель", color=COLOR_ADMIN)
    embed.add_field(name="Команды", value="`kick`, `ban`, `unban`, `clear`, `slowmode`, `lock`, `unlock`, `announce`", inline=False)
    embed.set_thumbnail(url=ANIME_ICONS["admin"])
    await ctx.send(embed=embed)

# ----- Система жалоб (с кнопками) -----

@bot.command(name="admticketsetup")
@commands.has_permissions(administrator=True)
async def admticketsetup(ctx):
    category = await ctx.guild.create_category("🎫 Жалобы на администраторов")
    channel = await category.create_text_channel("📝-подача-жалоб")
    view = TicketView(bot, ctx.guild.id, category.id)
    embed = discord.Embed(title="🎫 Система жалоб на администраторов", description="Нажмите кнопку, чтобы создать жалобу", color=COLOR_ERROR)
    embed.set_thumbnail(url=ANIME_ICONS["ticket"])
    await channel.send(embed=embed, view=view)
    await ctx.send(embed=discord.Embed(title="✅ Система жалоб создана", description=f"Канал: {channel.mention}", color=COLOR_SUCCESS))

@bot.command(name="evidencesetup")
@commands.has_permissions(administrator=True)
async def evidencesetup(ctx):
    category = await ctx.guild.create_category("📎 Доказательства нарушений")
    channel = await category.create_text_channel("📋-подача-доказательств")
    view = EvidenceView(bot, ctx.guild.id, category.id)
    embed = discord.Embed(title="📎 Система доказательств", description="Нажмите кнопку, чтобы подать доказательство", color=COLOR_INFO)
    embed.set_thumbnail(url=ANIME_ICONS["ticket"])
    await channel.send(embed=embed, view=view)
    await ctx.send(embed=discord.Embed(title="✅ Система доказательств создана", description=f"Канал: {channel.mention}", color=COLOR_SUCCESS))

# ----- Развлечения -----

@bot.command(name="joke")
async def joke(ctx):
    jokes = [
        "Почему программисты любят хэллоуин? Потому что 31 октября = 25 декабря (в восьмеричной)!",
        "Как называют бота, который любит аниме? Waifu-бот!",
        "Встречаются два массива. Один говорит: 'Я тебя индексирую!'",
        "Что сказал 0 числу 8? 'Классный пояс!'",
        "Почему кошки отличные программисты? Они всегда ловят ошибки!"
    ]
    embed = discord.Embed(title="😂 Анекдот", description=random.choice(jokes), color=COLOR_PINK)
    embed.set_thumbnail(url=ANIME_ICONS["fun"])
    await ctx.send(embed=embed)

@bot.command(name="compliment")
async def compliment(ctx, member: discord.Member = None):
    member = member or ctx.author
    compliments = [
        "ты просто космос!",
        "ты лучше всех!",
        "твоя аватарка — огонь!",
        "ты делаешь этот сервер лучше!",
        "у тебя отличное чувство юмора!"
    ]
    embed = discord.Embed(title="💝 Комплимент", description=f"{member.mention}, {random.choice(compliments)}", color=COLOR_PINK)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="8ball")
async def eightball(ctx, *, question):
    answers = ["Да", "Нет", "Возможно", "Спроси позже", "Бесспорно", "Никогда", "Может быть", "Определённо да"]
    embed = discord.Embed(title="🎱 Шар судьбы", description=f"Вопрос: {question}\nОтвет: **{random.choice(answers)}**", color=COLOR_PURPLE)
    embed.set_thumbnail(url=ANIME_ICONS["fun"])
    await ctx.send(embed=embed)

@bot.command(name="roll")
async def roll(ctx, sides: int = 6):
    result = random.randint(1, sides)
    embed = discord.Embed(title="🎲 Бросок кубика", description=f"Выпало: **{result}** (1-{sides})", color=COLOR_INFO)
    await ctx.send(embed=embed)

@bot.command(name="choose")
async def choose(ctx, *, options):
    opts = [o.strip() for o in options.split("|")]
    if len(opts) < 2:
        return await ctx.send(embed=discord.Embed(title="❌ Укажите варианты через |", color=COLOR_ERROR))
    chosen = random.choice(opts)
    embed = discord.Embed(title="🎯 Я выбираю", description=f"**{chosen}**", color=COLOR_SUCCESS)
    embed.add_field(name="Варианты", value=" | ".join(opts))
    await ctx.send(embed=embed)

@bot.command(name="avatar")
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Аватар {member.display_name}", url=member.avatar.url)
    embed.set_image(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="love")
async def love(ctx, member: discord.Member):
    percent = random.randint(0, 100)
    bar = "❤️" * (percent//10) + "🖤" * (10 - percent//10)
    embed = discord.Embed(title="💕 Калькулятор любви", description=f"{ctx.author.mention} + {member.mention}", color=COLOR_PINK)
    embed.add_field(name="Результат", value=f"{bar} **{percent}%**")
    await ctx.send(embed=embed)

# ----- Команды владельца (скрытые) -----

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

@bot.command(name="copium")
@is_owner()
async def copium(ctx):
    await ctx.send("Я не удалял твои сообщения... 👀")

@bot.command(name="ownermode")
@is_owner()
async def ownermode(ctx):
    embed = discord.Embed(title="👑 Режим владельца активирован", color=COLOR_GOLD)
    await ctx.send(embed=embed)

@bot.command(name="whoami")
@is_owner()
async def whoami(ctx):
    await ctx.send("Ты — бог этого сервера!")

@bot.command(name="epicness")
@is_owner()
async def epicness(ctx):
    await ctx.send(f"✨ Уровень эпичности: **9001**")

@bot.command(name="mindblow")
@is_owner()
async def mindblow(ctx):
    await ctx.send("🤯 Бот — это нейросеть, работающая на аниме-энергии!")

@bot.command(name="serverinfo_secret")
@is_owner()
async def serverinfo_secret(ctx):
    embed = discord.Embed(title="🔐 Секретная информация", color=0x000000)
    embed.add_field(name="Спящих", value=len([m for m in ctx.guild.members if m.status == discord.Status.idle]))
    embed.add_field(name="Ботов", value=sum(1 for m in ctx.guild.members if m.bot))
    await ctx.send(embed=embed)

@bot.command(name="ultimate_power")
@is_owner()
async def ultimate_power(ctx):
    await ctx.send("✨ Ты получил абсолютную силу! Теперь ты можешь всё!")

# ----- НОВЫЕ КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАЦИЕЙ -----

def has_level(required: int):
    async def predicate(ctx):
        if ctx.author.id == OWNER_ID:
            return True
        level = get_admin_level(ctx.author.id)
        return level is not None and level >= required
    return commands.check(predicate)

@bot.command(name="admlist")
@has_level(1)
async def admlist(ctx):
    admins = get_all_admins()
    embed = discord.Embed(title="📋 Список администрации", color=COLOR_ADMIN)
    for uid, lvl, pos, acc in admins:
        user = bot.get_user(uid)
        if user:
            level_info = LEVELS.get(lvl, {"name": f"Уровень {lvl}", "emoji": "🔹"})
            embed.add_field(name=f"{level_info['emoji']} {user.display_name}", value=f"{level_info['name']} | {pos}", inline=False)
    embed.set_thumbnail(url=ANIME_ICONS["admin"])
    await ctx.send(embed=embed)

@bot.command(name="cfginfo")
@has_level(1)
async def cfginfo(ctx):
    admins = get_all_admins()
    embed = discord.Embed(title="ℹ️ Конфигурация сервера", color=COLOR_INFO)
    embed.add_field(name="Администраторов", value=len(admins))
    embed.add_field(name="Уровней доступа", value=10)
    embed.add_field(name="Каналов", value=len(ctx.guild.channels))
    await ctx.send(embed=embed)

@bot.command(name="cnick")
@has_level(1)
async def cnick(ctx, member: discord.Member):
    history = get_nickname_history(member.id)
    embed = discord.Embed(title=f"📝 История ников {member.display_name}", color=COLOR_INFO)
    for h in history[:10]:
        old = h[2] or "None"
        new = h[3] or "None"
        embed.add_field(name=h[4][:10], value=f"{old} → {new}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="me", aliases=["myinfo", "find"])
async def me(ctx):
    level = get_admin_level(ctx.author.id)
    if level is None:
        return await ctx.send(embed=discord.Embed(title="❌ Вы не администратор", color=COLOR_ERROR))
    level_info = LEVELS.get(level, {"name": f"Уровень {level}", "emoji": "🔹"})
    embed = discord.Embed(title=f"👤 Профиль {ctx.author.display_name}", color=ctx.author.color)
    embed.add_field(name="Уровень", value=f"{level_info['emoji']} {level_info['name']}")
    embed.add_field(name="Должность", value="...")  # Можно добавить из БД
    embed.set_thumbnail(url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="ahistory")
@has_level(3)
async def ahistory(ctx):
    history = get_weekly_history()
    embed = discord.Embed(title="📆 История за неделю", color=COLOR_INFO)
    for h in history[:10]:
        embed.add_field(name=h[11][:10], value=f"{h[2]} {h[1]}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="hadm")
@has_level(3)
async def hadm(ctx, member: discord.Member):
    history = get_admin_history(member.id)
    embed = discord.Embed(title=f"📜 История {member.display_name}", color=COLOR_INFO)
    for h in history[:10]:
        embed.add_field(name=h[11][:10], value=f"{h[2]}: {h[5]} → {h[6]}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="setpost")
@has_level(7)
async def setpost(ctx, member: discord.Member, *, position):
    set_admin_position(member.id, position, ctx.author.id, "Назначение должности")
    embed = discord.Embed(title="✅ Должность установлена", description=f"{member.mention} теперь **{position}**", color=COLOR_SUCCESS)
    await ctx.send(embed=embed)

@bot.command(name="uplvl")
@has_level(7)
async def uplvl(ctx, member: discord.Member, level: int):
    if level not in range(1, 11) and ctx.author.id != OWNER_ID:
        return await ctx.send(embed=discord.Embed(title="❌ Недопустимый уровень (1-10)", color=COLOR_ERROR))
    set_admin_level(member.id, level, ctx.author.id, "Изменение уровня")
    level_info = LEVELS.get(level, {"name": f"Уровень {level}", "emoji": "🔹"})
    embed = discord.Embed(title="✅ Уровень изменён", description=f"{member.mention} теперь {level_info['emoji']} {level_info['name']}", color=COLOR_SUCCESS)
    await ctx.send(embed=embed)

@bot.command(name="archives")
@has_level(5)
async def archives(ctx):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin_archive ORDER BY fired_at DESC LIMIT 10")
    arch = cursor.fetchall()
    conn.close()
    embed = discord.Embed(title="🗂️ Архив снятых администраторов", color=COLOR_WARN)
    for a in arch:
        user = bot.get_user(a[1]) or a[2]
        embed.add_field(name=f"{user}", value=f"Причина: {a[7][:50]}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ratingall")
@has_level(5)
async def ratingall(ctx):
    admins = get_all_admins()
    sorted_admins = sorted(admins, key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="🏆 Рейтинг администрации", color=COLOR_GOLD)
    for uid, lvl, pos, acc in sorted_admins:
        user = bot.get_user(uid)
        if user:
            level_info = LEVELS.get(lvl, {"name": f"Ур.{lvl}", "emoji": "🔹"})
            embed.add_field(name=f"{level_info['emoji']} {user.display_name}", value=f"{level_info['name']} - {pos}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="setdostup")
@has_level(7)
async def setdostup(ctx, member: discord.Member, *, access_json: str):
    try:
        acc_dict = json.loads(access_json)
    except json.JSONDecodeError:
        return await ctx.send(embed=discord.Embed(title="❌ Неверный JSON", color=COLOR_ERROR))
    set_admin_access(member.id, acc_dict, ctx.author.id, "Установка доступа")
    embed = discord.Embed(title="✅ Доступ обновлён", description=f"Для {member.mention}", color=COLOR_SUCCESS)
    await ctx.send(embed=embed)

@bot.command(name="fire")
@has_level(8)
async def fire(ctx, member: discord.Member, *, reason="Не указана"):
    fire_admin(member.id, ctx.author.id, reason)
    embed = discord.Embed(title="🔥 Администратор снят", description=f"{member.mention} снят. Причина: {reason}", color=COLOR_ERROR)
    await ctx.send(embed=embed)

# ----- КОМАНДА !tech (отправка в ВК) -----

@bot.command(name="tech")
async def tech(ctx, *, text):
    """Отправить сообщение в техподдержку ВК"""
    if not text:
        return await ctx.send(embed=discord.Embed(title="❌ Введите текст", color=COLOR_ERROR))

    vk_message = f"/tech {text} by {ctx.author} (ID {ctx.author.id})"
    params = {
        "peer_id": VK_PEER_ID,
        "message": vk_message,
        "access_token": VK_TOKEN,
        "v": "5.131",
        "random_id": random.getrandbits(64)
    }

    try:
        response = requests.get("https://api.vk.com/method/messages.send", params=params)
        data = response.json()
        if "error" in data:
            error_msg = data["error"]["error_msg"]
            embed = discord.Embed(title="❌ Ошибка ВК", description=error_msg, color=COLOR_ERROR)
        else:
            embed = discord.Embed(title="✅ Сообщение отправлено в техподдержку", description=f"Текст: {text}", color=COLOR_SUCCESS)
            embed.set_thumbnail(url=ANIME_ICONS["tech"])
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=discord.Embed(title="❌ Ошибка при отправке", description=str(e), color=COLOR_ERROR))

# ==================== ЗАПУСК БОТА ====================

if __name__ == "__main__":
    init_db()
    bot.run(DISCORD_TOKEN)
