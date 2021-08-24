import json
import random
import configparser

from discord.ext import commands


config = configparser.ConfigParser()
config.read('env.ini')
BOT_TOKEN = config['DISCORD']['BOT_TOKEN']

bot = commands.Bot(command_prefix='!')


@bot.command(name='team', help='Responds with two random teams')
async def on_message(ctx):
    response = ''
    with open('champs.json') as f:
        champs = json.load(f)
    positions = ['Baron', 'Dragon', 'Mid', 'Jungle', 'Support']
    role_opts = ['AD', 'AP', 'Utility']
    for side in 'AB':
        team = random.sample(champs, 5)
        roles = [random.choice(role_opts) for _ in positions]
        squad = '\n'.join([f'> {roles[i]} {positions[i]} {champ}' for i, champ in enumerate(team)])
        response += f'Side {side}\n{squad}\n'

    await ctx.send(response)

bot.run(BOT_TOKEN)
