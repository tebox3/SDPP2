import requests
from flask import Flask,request,jsonify
import logging
import random
import argparse
import json
app = Flask(__name__)
configuracion = {}
board = 0
""" logging.basicConfig(filename='Log.log', 
                    filemode='w', 
                    level=logging.INFO,
                    format='%(asctime)s, %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p') """


# Configurar el logger principal para tu aplicación
app_logger = logging.getLogger('app_logger')
app_logger.setLevel(logging.INFO)

# Configurar el formato del log
formatter = logging.Formatter('%(asctime)s, %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Configurar el handler para escribir en el archivo de log
file_handler = logging.FileHandler('Log.log', mode='a')
file_handler.setFormatter(formatter)

# Agregar el handler al logger de la aplicación
app_logger.addHandler(file_handler)


juego='juego1' #Verificar como hacer esto automatico
def cargar_configuracion():
    parser = argparse.ArgumentParser(description='Script para CLIENTE')
    parser.add_argument('ruta_archivo', type=str, help='Ruta del archivo de configuración')
    args = parser.parse_args()
    ruta_configuracion = args.ruta_archivo
    print("LA RUTA: ",ruta_configuracion)
    with open(ruta_configuracion, 'r') as archivo:
        configuracion = json.load(archivo)
    return configuracion

# Definir la URL base del servidor Flask
configuracion = cargar_configuracion()
SERVER_URL = configuracion["server"]
CLIENT_IP = configuracion["ip"]
CLIENT_PORT = configuracion["port"]
PLAYER_NAME = configuracion["nombre"]
TEAM_NAME = configuracion["team"]
teams={}

def register_team(team_name):
    url = f'{SERVER_URL}/register_team'
    data = {'team_name': team_name}
    response = requests.post(url, json=data)
    response2 = response.json()
    if response2['message'] == 'Limit of teams reached':
        print("ERROR, limit of teams reached, just join a team.")
    return response.json()

def join_team(team_name, player_name):
    url = f'{SERVER_URL}/join_team'
    data = {'team_name': team_name, 'player_name': player_name, 'ip' : CLIENT_IP, 'port' : CLIENT_PORT}
    response = requests.post(url, json=data)
    return response.json()

def start_game():   
    url = f'{SERVER_URL}/start_game'
    response = requests.post(url)
    return response.json()

def roll_dice():
    url = f'{SERVER_URL}/roll_dice'
    data = {'team name': TEAM_NAME}
    response = requests.post(url, json=data)
    response2 = response.json()
    if (response2['total team']) >= board:
        print("YOUR TEAM WON!")
    return response.json()

def game_status():
    url = f'{SERVER_URL}/game_status'
    response = requests.get(url)
    return response.json()

def get_teams():
    url = f'{SERVER_URL}/get_teams'
    response = requests.get(url)
    return response.json()


def inicio():
    global configuracion,board
    global TEAM_NAME
    global PLAYER_NAME
    global juego
    app_logger.info('%s, %s, %s, %s', "ini", juego, TEAM_NAME, PLAYER_NAME)
    #logging.info('%s, %s, %s', juego, TEAM_NAME, PLAYER_NAME)
    teams = get_teams()
    print("TEAMS : ",teams)
    #equipo_cliente = random.choice(list(teams.keys()))
    print("SELECTED TEAM: ",TEAM_NAME)
    #print("Equipos desde el servidor: ",equipo_cliente)
    message_join = join_team(TEAM_NAME,PLAYER_NAME)
    #print(message_join.json()['board'])
    print(message_join['message'])
    board = message_join['board']
    print(board)
    message_start = start_game()
    print(message_start)

@app.route('/game_ready', methods=['GET'])
def game_ready_message():
    print('game ready to start, waiting for your turn')
    return jsonify({'message':'Ready'}) 

@app.route('/your_turn', methods=['GET'])
def play_turn():
    print("throwing dice...")
    response = roll_dice()
    print("Number obtained: ", response['value'])
    print("Total of your team: ", response['total team'])
    return jsonify({'message':'correc throw', 'total team': response['total team']})

@app.route('/game_ended', methods=['POST'])
def game_ended():
    ganador = request.json['ganador']
    print("The winner is ", ganador)
    print("Thanks for playing!")
    app_logger.info('%s, %s, %s, %s', "fin", juego, TEAM_NAME, PLAYER_NAME)
    return jsonify({'message':'BYE'}) 

with app.app_context():
    inicio()

# Ejemplo de uso
if __name__ == '__main__':
    app.run(host=CLIENT_IP,port=CLIENT_PORT,debug=True, use_reloader=False)