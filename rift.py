import random
import configparser

import discord
from discord.ext import commands


config = configparser.ConfigParser()
config.read('env.ini')
BOT_TOKEN = config['DISCORD']['BOT_TOKEN']
client = discord.Client()
bot = commands.Bot(command_prefix='!')


@bot.command(name='team', help='Responds with two random teams')
async def on_message(ctx):
    response = ''
    champs = ['Ahri', 'Akali', 'Akshan', 'Alistar', 'Amumu', 'Annie', 'Ashe',
              'Aurelion Sol', 'Blitzcrank', 'Braum', 'Camille', 'Corki',
              'Darius', 'Diana', 'Dr. Mundo', 'Draven', 'Evelynn', 'Ezreal',
              'Fiora', 'Fizz', 'Galio', 'Garen', 'Gragas', 'Graves', 'Irelia',
              'Janna', 'Jarvan IV', 'Jax', 'Jhin', 'Jinx', "Kai'Sa", 'Katarina',
              'Kennen', "Kha'Zix", 'Lee Sin', 'Leona', 'Lucian', 'Lulu', 'Lux',
              'Malphite', 'Master Yi', 'Miss Fortune', 'Nami', 'Nasus', 'Olaf',
              'Orianna', 'Pantheon', 'Rakan', 'Renekton', 'Rammus', 'Rengar',
              'Riven', 'Senna', 'Seraphine', 'Shyvana', 'Singed', 'Sona',
              'Soraka', 'Teemo', 'Thesh', 'Tristana', 'Tryndamere',
              'Twisted Fate', 'Varus', 'Vayne', 'Vi', 'Wukong', 'Xayah',
              'Xin Zhao', 'Yasuo', 'Zed', 'Ziggs']
    positions = ['Baron', 'Dragon', 'Jungle', 'Mid', 'Support']
    role_opts = ['AD', 'AP', 'Utility']
    for side in 'AB':
        team = random.sample(champs, 5)
        random.shuffle(positions)
        roles = [random.choice(role_opts) for _ in positions]
        squad = '\n'.join([f'>{roles[i]} {positions[i]} {champ}' for i, champ in enumerate(team)])
        response += f'Side {side}\n{squad}\n\n'

    await ctx.send(response)

bot.run(BOT_TOKEN)
