import os
import random
import sqlite3
import logging
import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = os.getenv("DATABASE_PATH", "quiz.db")
QUESTION_FILE = Path("questions.json")

if not TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your hosting provider's environment variables.")

DEFAULT_QUESTIONS = [
    {"category": "ثقافة عامة", "question": "ما عاصمة سلطنة عُمان؟", "choices": ["مسقط", "صلالة", "نزوى", "صحار"], "answer": 0},
    {"category": "علوم", "question": "ما الكوكب المعروف بالكوكب الأحمر؟", "choices": ["الزهرة", "المريخ", "زحل", "عطارد"], "answer": 1},
    {"category": "رياضة", "question": "كم عدد لاعبي فريق كرة القدم داخل الملعب؟", "choices": ["9", "10", "11", "12"], "answer": 2},
    {"category": "جغرافيا", "question": "ما أكبر محيط في العالم؟", "choices": ["الأطلسي", "الهندي", "المتجمد الشمالي", "الهادئ"], "answer": 3},
    {"category": "ألعاب", "question": "ما الشركة المطورة للعبة Minecraft؟", "choices": ["Mojang", "Nintendo", "Valve", "Ubisoft"], "answer": 0},
    {"category": "تاريخ", "question": "في أي قارة تقع مصر؟", "choices": ["آسيا فقط", "أفريقيا", "أوروبا", "أمريكا الجنوبية"], "answer": 1},
]

def load_questions():
    if QUESTION_FILE.exists():
        try:
            data = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except (ValueError, OSError):
            logging.exception("Could not read questions.json; using built-in questions.")
    return DEFAULT_QUESTIONS

def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS scores (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            correct INTEGER NOT NULL DEFAULT 0,
            answered INTEGER NOT NULL DEFAULT 0
        )""")

def record_answer(user, correct):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""INSERT INTO scores(user_id, username, points, correct, answered)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            points=points + excluded.points,
            correct=correct + excluded.correct,
            answered=answered + 1""",
            (user.id, user.display_name, 10 if correct else 0, 1 if correct else 0))

def leaderboard_rows():
    with sqlite3.connect(DB_PATH) as db:
        return db.execute(
            "SELECT username, points, correct, answered FROM scores ORDER BY points DESC, correct DESC LIMIT 10"
        ).fetchall()

class QuizView(discord.ui.View):
    def __init__(self, question, timeout=20):
        super().__init__(timeout=timeout)
        self.question = question
        self.message = None
        self.answered_users = set()
        for index, choice in enumerate(question["choices"]):
            button = discord.ui.Button(label=choice[:80], style=discord.ButtonStyle.primary, custom_id=f"quiz_choice_{index}")
            button.callback = self.make_callback(index)
            self.add_item(button)

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id in self.answered_users:
                await interaction.response.send_message("لقد أجبت عن هذا السؤال بالفعل.", ephemeral=True)
                return
            self.answered_users.add(interaction.user.id)
            correct = index == int(self.question["answer"])
            record_answer(interaction.user, correct)
            if correct:
                result = "إجابة صحيحة! حصلت على 10 نقاط."
            else:
                right = self.question["choices"][int(self.question["answer"])]
                result = f"إجابة غير صحيحة. الإجابة الصحيحة: {right}"
            await interaction.response.send_message(result, ephemeral=True)
        return callback

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

class QuizBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()
        logging.info("Slash commands synced.")

intents = discord.Intents.default()
bot = QuizBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info("Logged in as %s (%s)", bot.user, bot.user.id)

@bot.tree.command(name="quiz", description="ابدأ سؤالاً عشوائياً")
@app_commands.describe(category="اختر تصنيفاً أو اتركه عشوائياً")
@app_commands.choices(category=[
    app_commands.Choice(name="ثقافة عامة", value="ثقافة عامة"),
    app_commands.Choice(name="علوم", value="علوم"),
    app_commands.Choice(name="تاريخ", value="تاريخ"),
    app_commands.Choice(name="رياضة", value="رياضة"),
    app_commands.Choice(name="ألعاب", value="ألعاب"),
    app_commands.Choice(name="جغرافيا", value="جغرافيا"),
])
async def quiz(interaction: discord.Interaction, category: app_commands.Choice[str] | None = None):
    questions = load_questions()
    pool = [q for q in questions if category is None or q["category"] == category.value]
    if not pool:
        await interaction.response.send_message("لا توجد أسئلة لهذا التصنيف حالياً.", ephemeral=True)
        return
    question = random.choice(pool)
    embed = discord.Embed(
        title=f"سؤال {question['category']}",
        description=f"**{question['question']}**\n\n" + "\n".join(
            f"**{i + 1}.** {choice}" for i, choice in enumerate(question["choices"])
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="لديك 20 ثانية للإجابة • كل إجابة صحيحة = 10 نقاط")
    view = QuizView(question)
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

@bot.tree.command(name="leaderboard", description="عرض أفضل 10 لاعبين")
async def leaderboard(interaction: discord.Interaction):
    rows = leaderboard_rows()
    if not rows:
        await interaction.response.send_message("لا توجد نتائج بعد. ابدأ باستخدام /quiz!")
        return
    lines = [
        f"**{i}. {name}** — {points} نقطة | {correct}/{answered} إجابة صحيحة"
        for i, (name, points, correct, answered) in enumerate(rows, 1)
    ]
    embed = discord.Embed(title="ترتيب اللاعبين", description="\n".join(lines), color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="score", description="عرض نقاطك")
async def score(interaction: discord.Interaction):
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT points, correct, answered FROM scores WHERE user_id=?", (interaction.user.id,)).fetchone()
    if not row:
        await interaction.response.send_message("لم تسجل أي نقاط بعد. استخدم /quiz للبدء!", ephemeral=True)
        return
    await interaction.response.send_message(
        f"نقاطك: {row[0]}\nالإجابات الصحيحة: {row[1]} من {row[2]}", ephemeral=True
    )

@bot.tree.command(name="help_quiz", description="عرض أوامر البوت")
async def help_quiz(interaction: discord.Interaction):
    await interaction.response.send_message(
        "أوامر Quiz Bot\n/quiz — سؤال عشوائي\n/leaderboard — أفضل 10 لاعبين\n/score — نقاطك الحالية",
        ephemeral=True,
    )

if __name__ == "__main__":
    init_db()
    bot.run(TOKEN, log_handler=None)
