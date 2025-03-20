import socket
import threading
import random
import time
import statistics
import tkinter as tk

#############################################################################################################
# 1) Correr el archivo y seleccionar entre s (Servidor), c (Cliente), e (Estresador)
# *) Es necesario correr el servidor para correr el cliente o estresador
# *) En el cliente se debe seleccionar el lugar en el que se piensa que esta en el mounstro y el resultado 
#    del tiro aparecerá en la terminal 
# *) En el estresador se pide el número de clientes que se registraran y el tiempo que durará la 
#    prueba
#############################################################################################################

#############################################################################################################
#                                     Configuración del servidor
#############################################################################################################
class Server:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.clients = {}
        self.monster_position = None
        self.scores = {}  # Diccionario para contar aciertos
        self.winner = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[SERVIDOR] Esperando conexiones en {self.host}:{self.port}...")


    def handle_client(self, conn, addr):
        player_name = conn.recv(1024).decode()
        self.clients[player_name] = conn
        self.scores[player_name] = 0  # Inicializar puntuación
        print(f"[NUEVO JUGADOR] {player_name} se ha unido.")
        conn.send("NAME".encode())
        while True:
            try:
                msg = conn.recv(1024).decode()
                if msg.startswith("HIT"):  # Ejemplo: "HIT 3"
                    pos = int(msg.split()[1])
                    if pos == self.monster_position:
                        print(f"{player_name} golpeó al monstruo!")
                        self.scores[player_name] += 1
                        print(f"{player_name} tiene {self.scores[player_name]} aciertos")
                        conn.send("ACIERTO".encode())  # Responder que acertó
                        if self.scores[player_name] >= 5:
                            self.check_winner(player_name)
                    else:
                        print(f"{player_name} falló el golpe.")
                        conn.send("FALLO".encode())  # Responder que falló
            except:
                print(f"[DESCONECTADO] {player_name} salió del juego.")
                del self.clients[player_name]
                del self.scores[player_name]
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
        self.scores = {player: 0 for player in self.scores}  # Reiniciar puntuaciones
        for conn in self.clients.values():
            conn.send("RESET".encode())
        print("[SERVIDOR] Juego reiniciado.")
    
    def start(self):
        threading.Thread(target=self.send_monsters, daemon=True).start()
        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
#############################################################################################################
#                                               Cliente
#############################################################################################################
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
                elif msg == "ACIERTO":
                    print("¡Acertaste! ¡Bien hecho!")
                elif msg == "FALLO":
                    print("Fallaste. Intenta de nuevo.")
                elif msg == "NAME":
                    print("Registro correctamente")
            except:
                print("[ERROR] Conexión con el servidor perdida.")
                self.client_socket.close()
                break
    
    def hit_monster(self, pos):
        self.client_socket.send(f"HIT {pos}".encode())
#############################################################################################################
#                                          Cliente de estrés
#############################################################################################################
class StressClient:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.name = f"StressClient-{random.randint(1000, 9999)}"
        self.client_socket.send(self.name.encode())
        self.response_times = []  # Almacena los tiempos de respuesta
        self.running = True
        threading.Thread(target=self.listen_server, daemon=True).start()

    def listen_server(self):
        while self.running:
            try:
                msg = self.client_socket.recv(1024).decode()
                if msg == "WINNER" or msg == "RESET" or msg == "NAME":
                    break  # Termina la escucha
            except:
                break

    def send_random_hits(self, duration):
        start_time = time.time()
        self.client_socket.settimeout(2)  

        while time.time() - start_time < duration:
            pos = random.randint(0, 8)
            hit_time = time.time()  
            print(f"[{self.name}] Enviando HIT {pos}")
            self.client_socket.send(f"HIT {pos}".encode())

            try:
                response = self.client_socket.recv(1024).decode()
                if response in ["ACIERTO", "FALLO", "NAME"]:
                    response_time = time.time() - hit_time
                    self.response_times.append(response_time)
                    print(f"[{self.name}] Respuesta en {response_time:.4f} segundos: {response}")
                else:
                    print(f"[{self.name}] Respuesta inesperada: {response}")
            except socket.timeout:
                print(f"[{self.name}] [TIMEOUT] No hubo respuesta del servidor a tiempo.")
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                break  

            time.sleep(random.uniform(0.5, 2))  

        self.running = False
        self.client_socket.close()

#############################################################################################################
#                                     Interfaz Gráfica del Cliente
#############################################################################################################
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

#############################################################################################################
#                                  Cliente de estrés principal
#############################################################################################################
if __name__ == "__main__":
    option = input("¿Quieres iniciar el servidor, cliente o cliente de estrés? (s/c/e): ")
    if option.lower() == 's':
        server = Server()
        server.start()
    elif option.lower() == 'c':
        client = Client()
        GameGUI(client)
    elif option.lower() == 'e':
        n = int(input("Número de clientes de estrés: "))
        t = int(input("Duración del juego en segundos: "))
        clients = []
        
        for _ in range(n):
            client = StressClient()
            clients.append(client)
        
        threads = []
        for client in clients:
            thread = threading.Thread(target=client.send_random_hits, args=(t,))
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
        
        all_times = [time*1000 for client in clients for time in client.response_times]
        if all_times:
            avg_response = sum(all_times) / len(all_times)
            stddev_response = statistics.stdev(all_times) if len(all_times) > 1 else 0
            print(f"\nResultados de estrés:")
            print(f"Tiempo promedio de respuesta: {avg_response:.4f} milisegundos")
            print(f"Desviación estándar: {stddev_response:.4f} milisegundos")
        else:
            print("No se recopilaron datos de respuesta.")
