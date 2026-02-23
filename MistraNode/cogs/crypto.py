import disnake
from disnake.ext import commands, tasks
import aiohttp
import logging
from utils.formatting import format_crypto_response

logger = logging.getLogger('MistraNode')

class Crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alerts = []  # Твій список активних алертів
        self.crypto_monitor.start()

    def cog_unload(self):
        self.crypto_monitor.cancel()

    # --- 1. КОМАНДА ЦІНИ (З PREMIUM-АНАЛІТИКОЮ) ---
    @commands.slash_command(description="Дізнатися поточну ціну криптовалюти")
    async def price(self, inter: disnake.ApplicationCommandInteraction, symbol: str = "BTC"):
        # Перевірка дозволених каналів
        if not any(name in inter.channel.name.lower() for name in ["crypto", "analysis", "premium"]):
            await inter.response.send_message("❌ Використовуйте канал #crypto-analysis або Premium-зону", ephemeral=True)
            return

        try:
            await inter.response.defer()
        except disnake.errors.NotFound:
            logger.error("Interaction timed out during reconnect.")
            return

        symbol = symbol.upper()
        is_premium = "premium" in inter.channel.name.lower()
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    crypto_data = {
                        'price': float(data['lastPrice']),
                        'change_24h': float(data['priceChangePercent'])
                    }
                    
                    response_text = format_crypto_response(symbol, crypto_data)
                    embed_color = disnake.Color.gold() if is_premium else disnake.Color.blue()
                    title_prefix = "💎 PREMIUM " if is_premium else "📊 "
                    
                    embed = disnake.Embed(
                        title=f"{title_prefix}Аналітика ринку: {symbol}",
                        description=response_text,
                        color=embed_color
                    )

                    # Прогноз від моделі Large для преміум-каналів
                    if is_premium:
                        ai_cog = self.bot.get_cog("AIChat")
                        if ai_cog:
                            prompt = f"Act as a professional crypto trader. Price for {symbol} is ${crypto_data['price']}. Give a concise 4-hour trend prediction in Ukrainian."
                            try:
                                ai_resp = await ai_cog.client.chat.complete_async(
                                    model="mistral-large-latest",
                                    messages=[{"role": "user", "content": prompt}]
                                )
                                prediction = ai_resp.choices[0].message.content.strip()
                                embed.add_field(name="🎯 Елітний Прогноз (4h)", value=f"*{prediction}*", inline=False)
                            except Exception as e:
                                logger.error(f"Premium AI Error: {e}")

                    embed.set_footer(text=f"Джерело: Binance API | Mistra Node 2026")
                    await inter.edit_original_message(embed=embed)
                else:
                    await inter.edit_original_message(content=f"ERROR: InvalidTicker {symbol}.")

    # --- 2. КОМАНДА ІНДЕКСУ СТРАХУ (ТЕПЕР З ОБМЕЖЕННЯМ КАНАЛУ) ---
    @commands.slash_command(description="Глибокий аналіз настроїв ринку")
    async def market_analysis(self, inter: disnake.ApplicationCommandInteraction):
        # ДОДАЄМО ОБМЕЖЕННЯ ТУТ, ЩОБ ПРИБРАТИ "КАШУ"
        if not any(name in inter.channel.name.lower() for name in ["crypto", "analysis", "premium"]):
            await inter.response.send_message("❌ Використовуйте канал #crypto-analysis або Premium-зону", ephemeral=True)
            return

        try:
            await inter.response.defer()
        except disnake.errors.NotFound: return

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.alternative.me/fng/") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    val = int(data['data'][0]['value'])
                    status = data['data'][0]['value_classification']
                    
                    ai_cog = self.bot.get_cog("AIChat")
                    analysis = "Аналіз недоступний."
                    if ai_cog:
                        prompt = f"Market Fear&Greed Index is {val} ({status}). Give a 1-sentence technical perspective in Ukrainian."
                        ai_resp = await ai_cog.client.chat.complete_async(
                            model="mistral-tiny",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        analysis = ai_resp.choices[0].message.content.strip()

                    # Динамічний колір для преміуму
                    is_premium = "premium" in inter.channel.name.lower()
                    color = disnake.Color.gold() if is_premium else disnake.Color.dark_magenta()

                    embed = disnake.Embed(
                        title=f"🧠 {'PREMIUM ' if is_premium else ''}Смарт-аналіз настроїв", 
                        color=color
                    )
                    embed.add_field(name="Індекс", value=f"**{val}/100** ({status})", inline=True)
                    embed.add_field(name="Висновок Mistra Node", value=f"*{analysis}*", inline=False)
                    embed.set_footer(text="Mistra Intelligence | 2026")
                    await inter.edit_original_message(embed=embed)

    # --- 3. КОМАНДА АЛЕРТУ ---
    @commands.slash_command(description="Встановити сповіщення про ціну")
    async def set_alert(self, inter: disnake.ApplicationCommandInteraction, symbol: str, condition: str, price: float):
        # Додаємо таку ж перевірку, як у price та market_analysis
        if not any(name in inter.channel.name.lower() for name in ["crypto", "analysis", "premium"]):
            await inter.response.send_message(
                "❌ Встановлення алертів доступне лише в #crypto-analysis або Premium-зоні", 
                ephemeral=True
            )
            return

        symbol = symbol.upper()
        self.alerts.append({
            "user_id": inter.author.id,
            "channel_id": inter.channel.id,
            "symbol": symbol,
            "condition": condition,
            "price": price
        })
        
        # Робимо підтвердження гарним Embed
        embed = disnake.Embed(
            title="🔔 Сповіщення встановлено",
            description=f"Вузол **Mistra Node** відстежуватиме ціну {symbol}",
            color=disnake.Color.green()
        )
        embed.add_field(name="Умова", value=f"`{symbol} {condition} {price}$`", inline=True)
        embed.set_footer(text="Система моніторингу активна")
        
        await inter.response.send_message(embed=embed, ephemeral=True)

    # --- 4. МОНІТОРИНГ АЛЕРТІВ ---
    @tasks.loop(minutes=1.0)
    async def crypto_monitor(self):
        if not self.alerts: return
        async with aiohttp.ClientSession() as session:
            for alert in self.alerts[:]:
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={alert['symbol']}USDT"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        cur_price = float(data['price'])
                        triggered = (alert['condition'] == "<" and cur_price <= alert['price']) or \
                                    (alert['condition'] == ">" and cur_price >= alert['price'])
                        
                        if triggered:
                            channel = self.bot.get_channel(alert['channel_id'])
                            if channel:
                                await channel.send(f"🚨 **[ALERT]** <@{alert['user_id']}>: {alert['symbol']} досяг цілі {cur_price}$!")
                            self.alerts.remove(alert)

def setup(bot):
    bot.add_cog(Crypto(bot))