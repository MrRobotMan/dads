import random


def main():
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
    for side in ['A', 'B']:
        team = random.sample(champs, 5)
        random.shuffle(positions)
        roles = [random.choice(role_opts) for _ in positions]
        print(f'Side {side}')
        [print(f'{roles[i]} {positions[i]} {champ}') for i, champ in enumerate(team)]
        print()


if __name__ == '__main__':
    main()
