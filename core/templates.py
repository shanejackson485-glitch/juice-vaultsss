from pathlib import Path
from dataclasses import dataclass

@dataclass
class Template:
    key: str
    name: str
    description: str
    language: str
    entry: str
    command: str
    files: dict

PY_PREFIX = """import os, logging, discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('PREFIX', ',')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    logging.info('Ready as %s', bot.user)

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! `{round(bot.latency * 1000)}ms`')

@bot.tree.command(name='ping', description='Check bot latency')
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! `{round(bot.latency * 1000)}ms`')

if not TOKEN:
    raise RuntimeError('DISCORD_TOKEN is missing. Configure .env first.')
bot.run(TOKEN)
"""

COG_BOT = """import os, logging, discord
from pathlib import Path
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True

class Bot(commands.Bot):
    async def setup_hook(self):
        for file in Path('cogs').glob('*.py'):
            if file.name != '__init__.py' and not file.name.startswith('_'):
                await self.load_extension(f'cogs.{file.stem}')
                logging.info('Loaded cog: %s', file.stem)

bot = Bot(command_prefix=os.getenv('PREFIX', ','), intents=intents, help_command=None)

@bot.event
async def on_ready():
    logging.info('Connected as %s', bot.user)

if not TOKEN:
    raise RuntimeError('Set DISCORD_TOKEN in .env')
bot.run(TOKEN)
"""

PING_COG = """from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! `{round(self.bot.latency * 1000)}ms`')

async def setup(bot):
    await bot.add_cog(Ping(bot))
"""

JS_INDEX = """require('dotenv').config();
const fs = require('node:fs');
const path = require('node:path');
const { Client, Collection, GatewayIntentBits, Events } = require('discord.js');

if (!process.env.DISCORD_TOKEN) throw new Error('DISCORD_TOKEN missing from .env');
const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent] });
client.commands = new Collection();
for (const file of fs.readdirSync(path.join(__dirname, 'commands')).filter(x => x.endsWith('.js'))) {
  const command = require(path.join(__dirname, 'commands', file));
  client.commands.set(command.data.name, command);
}
client.once(Events.ClientReady, c => console.log(`Ready as ${c.user.tag}`));
client.on(Events.InteractionCreate, async interaction => {
  if (!interaction.isChatInputCommand()) return;
  const command = client.commands.get(interaction.commandName);
  if (!command) return;
  try { await command.execute(interaction, client); }
  catch (error) {
    console.error(error);
    const payload = { content: 'Command failed.', ephemeral: true };
    if (interaction.replied || interaction.deferred) await interaction.followUp(payload);
    else await interaction.reply(payload);
  }
});
client.login(process.env.DISCORD_TOKEN);
"""

JS_PING = """const { SlashCommandBuilder } = require('discord.js');
module.exports = {
  data: new SlashCommandBuilder().setName('ping').setDescription('Check bot latency'),
  async execute(interaction, client) {
    await interaction.reply(`Pong! `${client.ws.ping}ms``);
  }
};
"""

class TemplateCatalog:
    def __init__(self):
        self.items = [
            Template("py_prefix", "discord.py • Prefix + Slash", "Prefix and application ping commands, logging and dotenv setup.", "Python", "bot.py", "python bot.py", {
                "bot.py": PY_PREFIX, "requirements.txt": "discord.py>=2.4.0\\npython-dotenv>=1.0.1\\n",
                ".env.example": "DISCORD_TOKEN=your_token_here\\nPREFIX=,\\n",
                ".gitignore": ".env\\n.venv/\\n__pycache__/\\n", "README.md": "# Discord bot\\nInstall requirements, copy .env.example to .env and run python bot.py.\\n"
            }),
            Template("py_cogs", "discord.py • Cogs Architecture", "Extension loader, cogs folder, separate ping cog and config.", "Python", "bot.py", "python bot.py", {
                "bot.py": COG_BOT, "cogs/__init__.py": "", "cogs/ping.py": PING_COG,
                "requirements.txt": "discord.py>=2.4.0\\npython-dotenv>=1.0.1\\n",
                ".env.example": "DISCORD_TOKEN=your_token_here\\nPREFIX=,\\n", ".gitignore": ".env\\n.venv/\\n__pycache__/\\n"
            }),
            Template("js_v14", "discord.js • v14", "Node.js client with slash-command collection and error handling.", "Node.js", "src/index.js", "node src/index.js", {
                "src/index.js": JS_INDEX, "src/commands/ping.js": JS_PING,
                "package.json": '{\\n "name":"discord-bot","version":"1.0.0","type":"commonjs","scripts":{"start":"node src/index.js"},"dependencies":{"discord.js":"^14.19.0","dotenv":"^16.4.7"}\\n}\\n',
                ".env.example": "DISCORD_TOKEN=your_token_here\\n", ".gitignore": "node_modules/\\n.env\\n"
            }),
            Template("py_minimal", "Python • Minimal", "Small starter with a ready event and ping command.", "Python", "bot.py", "python bot.py", {
                "bot.py": "import os, discord\\nfrom discord.ext import commands\\nfrom dotenv import load_dotenv\\nload_dotenv()\\nbot=commands.Bot(command_prefix=',', intents=discord.Intents.all())\\n@bot.event\\nasync def on_ready(): print(f'Ready as {bot.user}')\\n@bot.command()\\nasync def ping(ctx): await ctx.send(f'Pong! `{round(bot.latency*1000)}ms`')\\nbot.run(os.environ['DISCORD_TOKEN'])\\n",
                "requirements.txt": "discord.py>=2.4.0\\npython-dotenv>=1.0.1\\n", ".env.example": "DISCORD_TOKEN=your_token_here\\n"
            })
        ]

    def all(self):
        return self.items

    def create(self, key, destination, overwrite=False):
        item = next((x for x in self.items if x.key == key), None)
        if not item:
            raise ValueError("Unknown template.")
        destination = Path(destination).expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        written, skipped = [], []
        for relative, body in item.files.items():
            target = (destination / relative).resolve()
            if destination not in target.parents:
                raise ValueError("Template path escaped destination.")
            if target.exists() and not overwrite:
                skipped.append(relative)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            written.append(relative)
        return item, written, skipped
