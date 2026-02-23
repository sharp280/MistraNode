import disnake
from disnake.ext import commands
import logging

logger = logging.getLogger('MistraNode')

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Інформаційна довідка Mistra Node")
    async def help(self, inter: disnake.ApplicationCommandInteraction):
        try:
            # Обов'язково додаємо defer, щоб Discord не видавав "Application not responding"
            await inter.response.defer()
        except disnake.errors.NotFound:
            logger.error("Help command interaction timed out.")
            return

        embed = disnake.Embed(
            title="📖 Документація Вузла Mistra Node",
            description="Автономна система моніторингу кібербезпеки та криптоактивів.",
            color=disnake.Color.blue()
        )
        
        # Структуруємо інформацію для комісії
        embed.add_field(
            name="🧠 AI Intelligence", 
            value="`#mistra-ai` — базовий чат\n`#mistra-premium` — елітна модель Large (💎)", 
            inline=False
        )
        embed.add_field(
            name="📊 Crypto Analysis", 
            value="`/price` — курс та аналітика\n`/market_analysis` — індекс настроїв", 
            inline=True
        )
        embed.add_field(
            name="🛡️ Security Lab", 
            value="`/check_url` — OSINT аналіз та Risk Score", 
            inline=True
        )
        embed.add_field(
            name="🖥️ Node Admin", 
            value="`/node_status` — стан обчислювальних ресурсів", 
            inline=False
        )
        
        embed.set_footer(text="Mistra Node v2.5-stable | Irpin Security Lab | 2026")
        
        # Використовуємо edit_original_message після defer
        await inter.edit_original_message(embed=embed)

def setup(bot):
    bot.add_cog(Info(bot))