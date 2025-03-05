import socket
import threading
import random
import time
import tkinter as tk
from tkinter import messagebox

# Configuración del servidor
class Server:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.clients = {}
        self.monster_position = None
        self.winner = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[SERVIDOR] Esperando conexiones en {self.host}:{self.port}...")

    def handle_client(self, conn, addr):
        player_name = conn.recv(1024).decode()
        self.clients[player_name] = conn
        print(f"[NUEVO JUGADOR] {player_name} se ha unido.")
        while True:
            try:
                msg = conn.recv(1024).decode()
                if msg.startswith("HIT"):  # Ejemplo: "HIT 3"
                    pos = int(msg.split()[1])
                    if pos == self.monster_position:
                        print(f"{player_name} golpeó al monstruo!")
                        self.check_winner(player_name)
            except:
                print(f"[DESCONECTADO] {player_name} salió del juego.")
                del self.clients[player_name]
                conn.close()
                break
    
    def send_monsters(self):
        while not self.winner:
            self.monster_position = random.randint(0, 8)  # Posición del monstruo en una grilla 3x3
            print(f"[SERVIDOR] Monstruo en posición {self.monster_position}")
            time.sleep(3)  # Enviar nuevo monstruo cada 3 segundos
    
    def check_winner(self, player_name):
        if player_name not in self.clients:
            return
        conn = self.clients[player_name]
        conn.send("WINNER".encode())
        self.winner = player_name
        print(f"[GANADOR] {player_name} ha ganado el juego!")
        self.reset_game()
    
    def reset_game(self):
        self.winner = None
        for conn in self.clients.values():
            conn.send("RESET".encode())
        print("[SERVIDOR] Juego reiniciado.")
    
    def start(self):
        threading.Thread(target=self.send_monsters, daemon=True).start()
        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

# Cliente
class Client:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.name = input("Ingrese su nombre: ")
        self.client_socket.send(self.name.encode())
        threading.Thread(target=self.listen_server, daemon=True).start()
    
    def listen_server(self):
        while True:
            try:
                msg = self.client_socket.recv(1024).decode()
                if msg == "WINNER":
                    print("¡Ganaste!")
                elif msg == "RESET":
                    print("El juego se ha reiniciado.")
            except:
                print("[ERROR] Conexión con el servidor perdida.")
                self.client_socket.close()
                break
    
    def hit_monster(self, pos):
        self.client_socket.send(f"HIT {pos}".encode())

# Interfaz Gráfica del Cliente
class GameGUI:
    def __init__(self, client):
        self.client = client
        self.root = tk.Tk()
        self.root.title("¡Pégale al monstruo!")
        self.buttons = []
        self.create_grid()
        self.root.mainloop()
    
    def create_grid(self):
        for i in range(9):  # 3x3 grid
            btn = tk.Button(self.root, text=str(i), width=10, height=3, command=lambda i=i: self.client.hit_monster(i))
            btn.grid(row=i//3, column=i%3)
            self.buttons.append(btn)

if __name__ == "__main__":
    option = input("¿Quieres iniciar el servidor o cliente? (s/c): ")
    if option.lower() == 's':
        server = Server()
        server.start()
    elif option.lower() == 'c':
        client = Client()
        GameGUI(client)
