from flask import Flask,request,jsonify,render_template
import random  
from time import sleep
import requests
from requests.exceptions import RequestException
from threading import Thread
from itertools import cycle, zip_longest
import os

app = Flask(__name__)

teams = {}
teams['Team A'] = []
teams['Team B'] = []
max_player = 3
max_teams = 3
""" teams['Team A'] = ['pancho', 'seba']
teams['Team B'] = ['pepito', 'carlos'] """
game_finished = False
game_started = False
turn_order = {}
current_team_index = 0
board_size = 100
max_dice_value = 40
min_dice_value = 20
players = {}
teams_roll = {}
teams_roll['Team A'] = []
teams_roll['Team B'] = []
winner = ''

# Función para leer el valor de 'juego' desde un archivo
def read_juego_value(filename='juego_value.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return int(file.read().strip())
    else:
        return 1  # Valor inicial si el archivo no existe

# Función para escribir el valor de 'juego' en un archivo
def write_juego_value(value, filename='juego_value.txt'):
    with open(filename, 'w') as file:
        file.write(str(value))


def intercalate_teams(teams):
    # Obtener una lista con los nombres de los equipos
    team_names = list(teams.keys())
    
    # Iterar de manera intercalada sobre los jugadores de los equipos
    for player in zip_longest(*[cycle(teams[team]) for team in team_names]):
        for p in player:
            if p is not None:
                yield p

def send_message_to_all_players(players, consulta, mensaje):
    print(players)
    for player_name, player_data in players.items():
        ip_address, port = player_data
        url = f'http://{ip_address}:{port}/{consulta}'
        print(url)
        try:
            with requests.get(url) as response:
                response.raise_for_status()  # Verificar si hay errores en la respuesta
                json_data = response.json()
                # Obtener el valor de la clave 'message' y convertirlo a minúsculas
                message = json_data.get('message', '').lower()
                # Imprimir el valor de 'message'
                print(message)
        except RequestException as e:
            print(f"Error sending message to {player_name}: {e}")
        
def send_message_to_all_players_ended(players, consulta, mensaje, ganador):
    data = {'message': mensaje, 'ganador': ganador}  # Datos a enviar en la solicitud POST
    for player_name, player_data in players.items():
        ip_address, port = player_data
        url = f'http://{ip_address}:{port}/{consulta}'
        print(url)
        try:
            with requests.post(url, json=data) as response:  # Enviar solicitud POST con datos JSON
                response.raise_for_status()  # Verificar si hay errores en la respuesta
                json_data = response.json()
                # Obtener el valor de la clave 'message' y convertirlo a minúsculas
                message = json_data.get('message', '').lower()
                # Imprimir el valor de 'message'
                print(message)
        except RequestException as e:
            print(f"Error sending message to {player_name}: {e}")

#verifica si el jugador ya esta en el equipo
def Is_Not_in_team(teams,name):
    for equipo, miembros in teams.items():
        if name in miembros:
            return True
    return False
    

def players_on_team(teams):
    return all(miembros for miembros in teams.values())

def start_rolling(teams):
    #desordena equipos
    for team in teams:
        random.shuffle(teams[team])
    #turnos intercalados
    for player in intercalate_teams(teams):
        if game_finished:
            break
        print("Player ",player," is throwing the dice")   
        ip=players[player][0]
        port=players[player][1]
        url = f'http://{ip}:{port}/your_turn'
        response = requests.get(url)
    print("Game finished!, thanks for playing")
    mensajito = send_message_to_all_players_ended(players,'game_ended', 'Gracias por jugar',winner)

@app.route("/")
def index():
    return render_template("index.html")

#registrar equipo
@app.route('/register_team', methods=['POST'])
def register_team():
    team_name = request.json['team_name']
    if len(teams)<3:
        teams[team_name] = []
        print(team_name," registered.")
        return jsonify({'message': f'Team {team_name} registered successfully.'})
    else: 
        return jsonify({'message': f'Limit of teams reached'})

@app.route('/get_teams', methods=['GET'])
def get_teams():
    return jsonify(teams)

@app.route('/join_team', methods=['POST'])
def join_team():
    # Leer el valor actual de 'juego' desde el archivo
    juego = read_juego_value()

    # Incrementar el valor de 'juego'
    juego += 1

    # Guardar el nuevo valor de 'juego' en el archivo
    write_juego_value(juego)
    print("Numero de JUEGO: ",juego)
    #agregar un jugador al equipo deseado
    team_name = request.json['team_name']
    player_name = request.json['player_name']
    players[player_name]=[]
    #Guarda las direcciones de los jugadores
    player_ip = request.json['ip']
    player_port = request.json['port']
    print("PLAYER IP Y PORT: ",player_ip, " : " ,player_port)
    players[player_name].append(player_ip)
    players[player_name].append(player_port)
    #responde por posibles errores
    if team_name not in teams:
        return jsonify({'error': f'Team {team_name} does not exist.'}), 404
    if len(teams[team_name]) == max_player:
        return jsonify({'error': f'Max number of players in this team already'}), 404
    if Is_Not_in_team(teams,player_name):
        return jsonify({'error': f'Player {player_name} already on a team.'}), 404
    teams[team_name].append(player_name)
    print(player_name," joined ",team_name,".")
    #confirma la inclusion al equipo correctamente
    print("Mensaje enviado...")
    return jsonify({'message': f'Player {player_name} joined team {team_name}.','board':board_size})

@app.route('/start_game', methods=['POST'])
def start_game():
    #jugadores tratan de iniciar el juego
    global game_started, turn_order, teams, players
    if not players_on_team(teams):
        return jsonify({'error': 'every team need at least 1 player, wait.'}), 400
    if game_started:
        return jsonify({'error': 'Game has already started.'}), 400
    game_started = True
    thread = Thread(target=execute_function)
    thread.start()
    return jsonify({'message': 'Game started.'})

def execute_function():
    #ejecuta el inicio del juego
    #avisa a jugadores del inicio
    verdad = send_message_to_all_players(players,'game_ready','')
    print("STARTING THE GAME...")
    #inicia
    start_rolling(teams)

#tirar el dado
@app.route('/roll_dice', methods=['POST'])
def roll_dice():
    global teams_roll, game_finished, winner
    #numero random del dado
    roll_result = random.randint(min_dice_value,max_dice_value)
    print("result: ",roll_result)
    team_name = request.json['team name']
    #agrega valor al equipo correspondiente
    teams_roll[team_name].append(roll_result)
    values = teams_roll.get(team_name)
    print(values)
    #total del equipo
    suma_valores = sum(values)
    print("TOTAL OF TEAM ",team_name,": ",suma_valores)
    #verificacion ganadora
    if suma_valores >= board_size:
        game_finished = True
        winner = team_name
        return jsonify({'message': 'YOUR TEAM WON!!!', 'value': roll_result, 'total team': suma_valores})
    elif suma_valores < board_size:
        return jsonify({'message': 'correct launch', 'value': roll_result, 'total team' : suma_valores})
    else:
        return jsonify({'message': 'hubo un error'})


if __name__ == '__main__':
    app.run(host="127.0.0.1",port=4000,debug=True)

