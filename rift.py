import json
import random
import configparser

from discord.ext import commands

config = configparser.ConfigParser()
config.read('env.ini')
BOT_TOKEN = config['DISCORD']['BOT_TOKEN']

bot = commands.Bot(command_prefix='!')

with open('champs.json') as f:
    champs_data = json.load(f)
champs = champs_data.keys()


def make_team():
    positions = ['Baron', 'Dragon', 'Mid', 'Jungle', 'Support']
    role_opts = ['AD', 'AP', 'Utility']
    team = random.sample(champs, 5)
    roles = [random.choice(role_opts) for _ in positions]
    return [f'{roles[i]} {positions[i]} {champ}' for i, champ in enumerate(team)]


@bot.command(name='team', help='Responds with a random team')
async def on_message(ctx):
    await ctx.send('\n'.join(make_team()))


@bot.command(name='teams', help='Responds with two random teams')
async def on_message(ctx):
    response = ''
    for side in 'AB':
        squad = '\n> '.join(make_team())
        response += f'Side {side}\n> {squad}\n'

    await ctx.send(response)

bot.run(BOT_TOKEN)
