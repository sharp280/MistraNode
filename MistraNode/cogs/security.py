import disnake
from disnake.ext import commands
import aiohttp
import base64
import os
import re
import whois
import logging
from datetime import datetime

logger = logging.getLogger('MistraNode')

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vt_key = os.getenv("VT_API_KEY")

    @commands.slash_command(description="Комплексний аналіз безпеки посилання")
    async def check_url(self, inter: disnake.ApplicationCommandInteraction, url: str):
        # 1. Перевірка каналу (підтримує назви з емодзі)
        if "security" not in inter.channel.name.lower():
            await inter.response.send_message("🛡️ Використовуйте канал #security-check", ephemeral=True)
            return

        await inter.response.defer()
        local_details = []
        risk_score = 0 # Початковий бал ризику для диплома
        
        # 2. Локальна евристика
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url): 
            local_details.append("⚠️ Пряма IP-адреса (підозра на фішинг).")
            risk_score += 30
        if url.startswith("http://") and not url.startswith("https://"): 
            local_details.append("⚠️ Незахищене HTTP з'єднання.")
            risk_score += 15

        # 3. Аналіз Whois
        try:
            domain = url.replace("https://","").replace("http://","").split("/")[0]
            w = whois.whois(domain)
            days_val = "Невідомо"
            
            raw_date = w.get('creation_date')
            if raw_date:
                c_date = raw_date[0] if isinstance(raw_date, list) else raw_date
                if isinstance(c_date, str):
                    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', c_date)
                    if date_match:
                        c_date = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
                
                if isinstance(c_date, datetime):
                    days_count = (datetime.now() - c_date).days
                    days_val = f"{days_count} днів"
                    if days_count < 30:
                        local_details.append(f"🔴 ДОМЕНУ ВСЬОГО {days_count} ДНІВ!")
                        risk_score += 45 # Високий ризик для нових доменів
            
            local_details.append(f"📅 Вік домену: {days_val}.")
        except Exception as e:
            logger.warning(f"Whois failed: {e}")
            local_details.append("📅 Вік домену: не вдалося отримати дані.")

        # 4. Асинхронний запит до VirusTotal
        vt_res = "Дані відсутні"
        try:
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://www.virustotal.com/api/v3/urls/{url_id}", 
                    headers={"x-apikey": self.vt_key}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        stats = data['data']['attributes']['last_analysis_stats']
                        vt_res = f"🔴 {stats['malicious']} | 🟡 {stats['suspicious']} | 🟢 {stats['harmless']}"
                        risk_score += (stats['malicious'] * 25) # Кожна загроза значно підвищує бал
        except Exception as e:
            logger.error(f"VT Error: {e}")

        # 5. Формування фінального Embed
        risk_score = min(risk_score, 100) 
        is_premium = "premium" in inter.channel.name.lower()
        
        # Колірна індикація
        if risk_score > 60: color = disnake.Color.red()
        elif risk_score > 25: color = disnake.Color.orange()
        else: color = disnake.Color.green()

        embed = disnake.Embed(title=f"🛡️ Аналіз безпеки: {url}", color=color)
        embed.add_field(name="🛡️ MISTRA RISK SCORE", value=f"**{risk_score}/100**", inline=False)
        embed.add_field(name="🌐 Рейтинг VirusTotal", value=f"`{vt_res}`", inline=True)
        embed.add_field(name="🛠️ Технічні деталі", value="\n".join(local_details) if local_details else "✅ Аномалій не виявлено", inline=False)

        # ІЗЮМІНКА: AI порада для Premium
        if is_premium:
            ai_cog = self.bot.get_cog("AIChat")
            if ai_cog:
                prompt = f"URL {url} has Risk Score {risk_score}/100. Give a 1-sentence pro security tip in Ukrainian."
                ai_resp = await ai_cog.client.chat.complete_async(
                    model="mistral-large-latest",
                    messages=[{"role": "user", "content": prompt}]
                )
                embed.add_field(name="💎 Елітна порада (Mistral Large)", value=f"*{ai_resp.choices[0].message.content.strip()}*", inline=False)
                embed.color = disnake.Color.gold()

        embed.set_footer(text="Mistra Security Lab | Irpin 2026")
        await inter.edit_original_message(embed=embed)

def setup(bot):
    bot.add_cog(Security(bot))