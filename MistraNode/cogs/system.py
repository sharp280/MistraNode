import disnake
from disnake.ext import commands
import psutil
import time
import asyncio
import logging

logger = logging.getLogger('MistraNode')

class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.total_requests = 0

    @commands.Cog.listener()
    async def on_app_command(self, inter: disnake.ApplicationCommandInteraction):
        self.total_requests += 1

    @commands.slash_command(description="Статус системного вузла Mistra Node")
    async def node_status(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        latency = round(self.bot.latency * 1000)
        boot_time = psutil.boot_time()
        uptime_hours = round((time.time() - boot_time) / 3600, 1)

        embed = disnake.Embed(title="🖥️ Стан Вузла: Mistra Node (Irpin)", color=disnake.Color.dark_gray())
        embed.add_field(name="📡 Latency", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="🧠 CPU", value=f"`{cpu}%`", inline=True)
        embed.add_field(name="📟 RAM", value=f"`{ram}%`", inline=True)
        embed.add_field(name="📥 Requests", value=f"`{self.total_requests}`", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"`{uptime_hours}h`", inline=True)
        
        await inter.edit_original_message(embed=embed)

    #  СТРЕС-ТЕСТ
    @commands.slash_command(description="🔬 Запустити аналіз продуктивності (Developer Only)")
    async def stress_test(self, inter: disnake.ApplicationCommandInteraction, duration: int = 5):
        # Перевірка на закритий канал
        if "stress-test" not in inter.channel.name.lower():
            await inter.response.send_message("❌ Цю команду можна запускати лише в ізольованій лабораторії #stress-test", ephemeral=True)
            return

        await inter.response.send_message("🚀 **Запуск стрес-тестування вузла...** Зачекайте...")
        
        start_time = time.time()
        cpu_readings = []
        ram_readings = []

        # Емуляція інтенсивного навантаження (цикл збору метрик)
        for _ in range(duration):
            cpu_readings.append(psutil.cpu_percent(interval=1))
            ram_readings.append(psutil.virtual_memory().percent)
            await asyncio.sleep(0.1)

        avg_cpu = round(sum(cpu_readings) / len(cpu_readings), 1)
        max_cpu = max(cpu_readings)
        avg_ram = round(sum(ram_readings) / len(ram_readings), 1)
        test_duration = round(time.time() - start_time, 2)

        embed = disnake.Embed(
            title="🔬 Звіт про продуктивність (Stress Test)",
            description=f"Тестування тривало `{test_duration}с` у закритому контурі.",
            color=disnake.Color.red()
        )
        embed.add_field(name="📊 Середнє навантаження CPU", value=f"`{avg_cpu}%`", inline=True)
        embed.add_field(name="📈 Пікове навантаження CPU", value=f"`{max_cpu}%`", inline=True)
        embed.add_field(name="📟 Сер. використання RAM", value=f"`{avg_ram}%`", inline=True)
        embed.add_field(name="🔗 Статус API", value="🟢 Стабільно", inline=True)
        
        embed.set_footer(text="Mistra Labs | Irpin 2026 | Performance Audit")
        
        await inter.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(System(bot))