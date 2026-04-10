import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

AGENTS = {
    "quant": {
        "name": "📊 Analista Cuantitativo",
        "system": "Eres un analista cuantitativo de mercados financieros de élite. Analizas datos con modelos DCF, valuaciones relativas, series de tiempo y métricas financieras (P/E, EV/EBITDA, ROE, CAGR). Eres preciso, usas números concretos y referencias comparables de industria. Respondes en español, de forma estructurada y directa. Cuando no tienes datos exactos, das rangos razonables basados en promedios del sector. Sé conciso, máximo 3 párrafos."
    },
    "fundamental": {
        "name": "🔍 Analista Fundamental",
        "system": "Eres un analista fundamental especializado en equity research. Evalúas modelos de negocio, ventajas competitivas (moats), estados financieros, posición competitiva y potencial de crecimiento de empresas. Usas frameworks como Porter's 5 fuerzas, análisis FODA y due diligence cualitativo. Respondes en español con análisis profundo y ejemplos de empresas reales cuando es relevante. Sé conciso, máximo 3 párrafos."
    },
    "riesgo": {
        "name": "⚠️ Gestor de Riesgos",
        "system": "Eres un gestor de riesgos de inversión senior. Identificas y cuantificas riesgos sistémicos, de crédito, liquidez, concentración y tail risks. Usas VaR, stress testing y escenarios adversos. Siempre señalas los principales riesgos antes de cualquier oportunidad. Respondes en español con un enfoque conservador y riguroso, priorizando la preservación de capital. Sé conciso, máximo 3 párrafos."
    },
    "macro": {
        "name": "🌍 Analista Macro",
        "system": "Eres un estratega macroeconómico global. Analizas ciclos económicos, política monetaria de bancos centrales, inflación, tasas de interés, flujos de capital, divisas y geopolítica. Contextualizas cualquier inversión dentro del entorno macro global y latinoamericano. Respondes en español con perspectiva amplia. Sé conciso, máximo 3 párrafos."
    },
    "tecnico": {
        "name": "📈 Analista Técnico",
        "system": "Eres un analista técnico de mercados con 15 años de experiencia. Interpretas patrones de precio y volumen, tendencias, soportes/resistencias, y usas indicadores como RSI, MACD, medias móviles y Bollinger. Identificas puntos de entrada y salida óptimos. Respondes en español describiendo claramente lo que sugieren los gráficos. Sé conciso, máximo 3 párrafos."
    },
    "cio": {
        "name": "🧭 Director de Inversiones",
        "system": "Eres el Director de Inversiones (CIO) de un family office latinoamericano. Integras análisis cuantitativo, fundamental, de riesgos, macro y técnico para tomar decisiones finales de asignación de capital. Das recomendaciones concretas con tesis de inversión claras, horizonte temporal y criterios de salida. Respondes en español con autoridad y visión estratégica. Sé conciso, máximo 4 párrafos."
    },
}

TEAM_SEQUENCE = ["macro", "fundamental", "quant", "riesgo", "cio"]

user_state = {}

def get_user_state(user_id):
    if user_id not in user_state:
        user_state[user_id] = {"agent": "cio", "history": []}
    return user_state[user_id]

def call_claude(system_prompt, messages):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Equipo de Análisis de Mercados* activado.\n\n"
        "Elige tu agente con un comando:\n"
        "• /macro — Analista Macroeconómico 🌍\n"
        "• /fundamental — Analista Fundamental 🔍\n"
        "• /quant — Analista Cuantitativo 📊\n"
        "• /riesgo — Gestor de Riesgos ⚠️\n"
        "• /tecnico — Analista Técnico 📈\n"
        "• /cio — Director de Inversiones 🧭\n\n"
        "• /equipo — Análisis completo con todo el equipo 🤝\n\n"
        "• /nuevo — Reinicia la conversación\n\n"
        "Escríbeme tu consulta después de elegir un agente."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def set_agent(update: Update, context: ContextTypes.DEFAULT_TYPE, agent_key: str):
    state = get_user_state(update.effective_user.id)
    state["agent"] = agent_key
    state["history"] = []
    agent = AGENTS[agent_key]
    await update.message.reply_text(
        f"{agent['name']} activado ✅\n\n¿Qué quieres analizar?",
        parse_mode="Markdown"
    )

async def cmd_macro(update, context): await set_agent(update, context, "macro")
async def cmd_fundamental(update, context): await set_agent(update, context, "fundamental")
async def cmd_quant(update, context): await set_agent(update, context, "quant")
async def cmd_riesgo(update, context): await set_agent(update, context, "riesgo")
async def cmd_tecnico(update, context): await set_agent(update, context, "tecnico")
async def cmd_cio(update, context): await set_agent(update, context, "cio")

async def cmd_equipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_user_state(update.effective_user.id)
    state["agent"] = "equipo"
    state["history"] = []
    await update.message.reply_text(
        "🤝 *Modo Equipo Completo* activado.\n\n"
        "Tu consulta será analizada por todos los especialistas en secuencia:\n"
        "🌍 Macro → 🔍 Fundamental → 📊 Quant → ⚠️ Riesgos → 🧭 Director\n\n"
        "¿Qué quieres analizar?",
        parse_mode="Markdown"
    )

async def cmd_nuevo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = get_user_state(update.effective_user.id)
    state["history"] = []
    await update.message.reply_text("🔄 Conversación reiniciada. ¿Qué analizamos?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_user_state(user_id)
    question = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    if state["agent"] == "equipo":
        await run_team_mode(update, context, question)
        return

    agent = AGENTS[state["agent"]]
    state["history"].append({"role": "user", "content": question})

    if len(state["history"]) > 10:
        state["history"] = state["history"][-10:]

    try:
        reply = call_claude(agent["system"], state["history"])
        state["history"].append({"role": "assistant", "content": reply})
        await update.message.reply_text(
            f"{agent['name']}\n\n{reply}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error al procesar. Intenta de nuevo en un momento.")

async def run_team_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    full_context = ""

    for agent_key in TEAM_SEQUENCE:
        agent = AGENTS[agent_key]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        system = agent["system"]
        if full_context:
            system += f"\n\nContexto del equipo hasta ahora:\n{full_context}"

        try:
            reply = call_claude(system, [{"role": "user", "content": question}])
            full_context += f"\n[{agent['name']}]: {reply}"
            await update.message.reply_text(
                f"{agent['name']}\n\n{reply}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error con agente {agent_key}: {e}")
            await update.message.reply_text(f"❌ Error con {agent['name']}.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("macro", cmd_macro))
    app.add_handler(CommandHandler("fundamental", cmd_fundamental))
    app.add_handler(CommandHandler("quant", cmd_quant))
    app.add_handler(CommandHandler("riesgo", cmd_riesgo))
    app.add_handler(CommandHandler("tecnico", cmd_tecnico))
    app.add_handler(CommandHandler("cio", cmd_cio))
    app.add_handler(CommandHandler("equipo", cmd_equipo))
    app.add_handler(CommandHandler("nuevo", cmd_nuevo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
