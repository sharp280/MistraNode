import disnake
from disnake.ext import commands
from mistralai import Mistral
import os
import logging
from datetime import datetime

logger = logging.getLogger('MistraNode')

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.history = {}
        
        # Завантаження локальної бази знань для диплома (RAG)
        self.knowledge_base = self.load_knowledge()

        self.system_instructions = (
            "IDENTITY: Mistra Node. ROLE: Autonomous Security & Crypto Intelligence. "
            "ORIGIN: Irpin, Ukraine. COORDINATOR: Double V. "
            "CONTEXT: Current year is 2026. All data must reflect this timeline. "
            f"LOCAL_DATABASE_CONTEXT: {self.knowledge_base} "
            "TOPICS: Cybersecurity, Crypto, Blockchain, Software Development, Tech Infrastructure. "
            "TONE: Приємний, інтелектуальний, професійний. Спілкуйся як досвідчений колега. "
            "GUIDELINES: "
            "1. Завжди звертайся до оператора за нікнеймом [ACTIVE_USER]. "
            "2. Якщо питання поза темою — м'яко та ввічливо поясни що ти спілкуєшся на технічні аспекти. "
            "3. Якщо просять пораду — ввічливо поясни, що ти надаєш дані та аналітику, а не рекомендації. "
            "4. В межах дозволених тем активно підтримуй діалог, став доречні зустрічні питання. "
            "5. ЗАБОРОНЕНО: Використовувати слова 'ПРАВИЛО', 'ПРОТОКОЛ' або 'ІНСТРУКЦІЯ' у відповідях. "
            "6. Відповіді мають бути лаконічними, але не грубими. Тільки суть."
        )

    def load_knowledge(self):
        """Зчитує дані з папки docs для наповнення ШІ знаннями"""
        kb_content = ""
        kb_path = "docs"
        try:
            if not os.path.exists(kb_path):
                os.makedirs(kb_path)
                return "No local data found."
            
            for filename in os.listdir(kb_path):
                if filename.endswith(".txt"):
                    with open(os.path.join(kb_path, filename), 'r', encoding='utf-8') as f:
                        kb_content += f.read() + "\n"
            return kb_content if kb_content else "No local data found."
        except Exception as e:
            logger.error(f"KB Load Error: {e}")
            return "Knowledge base error."

    @commands.slash_command(description="Про проект Mistra Node")
    async def about(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
            title="🛡️ Про систему Mistra Node",
            description="Автономний вузол кібербезпеки та фінансового моніторингу.",
            color=disnake.Color.blue()
        )
        embed.add_field(name="🚀 Стек", value="Python 3.10 | Disnake | Mistral AI | VirusTotal OSINT", inline=False)
        embed.add_field(name="📍 Локація вузла", value="Irpin Security Lab (Ukraine)", inline=True)
        embed.add_field(name="👤 Розробник", value="Віктор Б. (Double V)", inline=True)
        await inter.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channel_name = message.channel.name.lower()

        # 1. ТИХА МОДЕРАЦІЯ (Crypto/Security)
        if any(name in channel_name for name in ["crypto-analysis", "security-check"]):
            # Ігноруємо слеш-команди (наприклад, /check_url), щоб вони працювали
            if message.content.startswith("/"):
                return

            try:
                # Перевірка теми повідомлення
                check_prompt = f"Is this message about IT, Security, or Crypto? Reply only YES or NO. Message: {message.content}"
                check_resp = await self.client.chat.complete_async(
                    model="mistral-tiny",
                    messages=[{"role": "user", "content": check_prompt}]
                )
                
                # Якщо повідомлення не по темі — видаляємо 
                if "NO" in check_resp.choices[0].message.content.strip().upper():
                    try:
                        await message.delete()
                    except Exception as e:
                        logger.error(f"Failed to delete message: {e}")
                    return 
            except Exception as e:
                logger.error(f"Mod Error: {e}")
                return

        #2. ТЕРМІНАЛЬНИЙ ЧАТ (AI-Chat / Premium)
        # ВАЖЛИВО: Тут ТІЛЬКИ канали для спілкування. Аналітичні канали ігноруються,
        # щоб бот не відповідав текстом там, де мають бути лише результати команд.
        is_premium = "premium" in channel_name

        if any(name in channel_name for name in ["mistra-ai", "premium"]):
            cid = message.channel.id
            user_nick = message.author.display_name
            
            current_model = "mistral-large-latest" if is_premium else "mistral-medium-latest"
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time_context = f"\n[SYSTEM_TIME]: {current_time}\n[ACTIVE_USER]: {user_nick}\n[STATUS]: 2026_ACTIVE."
            
            if cid not in self.history:
                self.history[cid] = [{"role": "system", "content": self.system_instructions + time_context}]
                if is_premium:
                    self.history[cid].append({"role": "system", "content": "PREMIUM_MODE: Використовуй елітну аналітику."})
            
            self.history[cid].append({"role": "user", "content": f"(USER: {user_nick}) {message.content}"})
            
            if len(self.history[cid]) > 10:
                self.history[cid] = [self.history[cid][0]] + self.history[cid][-9:]

            async with message.channel.typing():
                try:
                    response = await self.client.chat.complete_async(
                        model=current_model,
                        messages=self.history[cid]
                    )
                    answer = response.choices[0].message.content.strip()
                    self.history[cid].append({"role": "assistant", "content": answer})
                    
                    if is_premium:
                        embed = disnake.Embed(
                            title="💎 Mistra Node: Premium Intelligence",
                            description=answer,
                            color=disnake.Color.gold()
                        )
                        embed.set_footer(text=f"Model: {current_model} | Оператор: {user_nick} | 2026")
                        await message.channel.send(embed=embed)
                    else:
                        if len(answer) <= 2000:
                            await message.channel.send(answer)
                        else:
                            for i in range(0, len(answer), 1900):
                                await message.channel.send(answer[i:i+1900])
                            
                except Exception as e:
                    logger.error(f"AI Chat Error: {e}")

def setup(bot):
    bot.add_cog(AIChat(bot))