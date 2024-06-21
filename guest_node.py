import socket
from multiprocessing import Process, Manager
from threading import Thread
import os
import pickle
from time import sleep

# PORTS:
#   20001 -> guest-to-border
#   20002 -> guest-to-guest
#   20003 -> guest-to-border (commands)


def get_file_listing():
    dir_path = r"C:\Users\mpqfreitas\Desktop\code\FILES"

    files = []
    for path in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, path)):  # Verifica se item é um arquivo
            files.append(path)

    return files

def send_dir_status():
    BORDER_ADDRESS = "10.62.202.20"
    server = (BORDER_ADDRESS, 20001)
    border_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    border_socket.connect(server)
    
    print(f"Connected to border Node ({server[0]}:{server[1]})")

    while(True):   
        files = pickle.dumps(get_file_listing()) # Serializa array de arquivos
        border_socket.send(files)
        sleep(0.5)

def handle_peer_request(connection, client_address):
    try:
        message = connection.recv(1024)
        message = message.decode("utf-8")
        print(f"[{client_address}]: REQUESTING {message}")
        dir_path = r"C:\Users\mpqfreitas\Desktop\code\FILES"
        file_path = os.path.join(dir_path, message)

        if os.path.isfile(file_path):
            with open(file_path, "rb") as f:  # Leitura em modo binário
                while(True):
                    data = f.read(1024)
                    print(len(data))
                    if not data:
                        break
                    connection.send(data)
            print(f"File '{message}' sent to {client_address}")
            
        else:
            # Se o arquivo não existe, envia uma mensagem indicando isso
            connection.send("Arquivo Inexistente!".encode("utf-8"))
            print(f"File '{message}' not found")
            connection.close()

    except Exception as e:
        print(e)
        connection.close() # Fecha conexão em caso de erro
        

def listen_peers():
    MY_ADDR = "10.62.202.20"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (MY_ADDR, 20002)
    server_socket.bind(server_address)

    server_socket.listen()
    print(f"Listening for peers on {server_address}")

    while(True):
        connection, client_address = server_socket.accept()
        p = Process(target=handle_peer_request, args=(connection, client_address))
        p.start()
        p.join()
        connection.close()


def user():
    BORDER_ADDRESS = "10.62.202.20"
    server = (BORDER_ADDRESS, 20003)
    front_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    front_socket.connect(server)
    print(f"Connected to front-end ({server[0]}:{server[1]})")

    while(True):
        command = input(">")
        if command != "":
            if command.startswith("REQUEST "):
                front_socket.send(command.encode("utf-8"))

                message = front_socket.recv(1024)
                message = pickle.loads(message)   # ('a.txt', ('192.168.0.104', 20234))
                print(message)

                if message != "Arquivo Inexistente!":
                    PEER_ADDR = message[1][0]
                    peer = (PEER_ADDR, 20002)
                    print(peer)
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        peer_socket.connect(peer)
                        print(f"Connected to Peer Node ({peer[0]}:{peer[1]})")
                    except Exception as e:  
                        print(f"Failed to connect to peer {peer}: {e}")  
                        continue  

                    print(f"Requesting file '{message[0]}'...")
                    peer_socket.send(message[0].encode("utf-8"))

                    print("Downloading file...")
                    try:
                        with open(f"{message[0]}", "wb") as f:   # Escrita em modo binário
                            while(True):
                                data = peer_socket.recv(1024)
                                if not data:
                                    print("Finished Download, closing connection.")
                                    break
                                f.write(data)
                                print(data.decode("utf-8"))
                                print(f"Received {len(data)} bytes")
                    except Exception as e:
                        print(e)
                    finally:
                        peer_socket.close()
                    
                
                            
                    peer_socket.close()
                    print(f"{message[0]} Downloaded!!!")

            else:
                front_socket.send(command.encode("utf-8"))
                message = front_socket.recv(1024)
                message = pickle.loads(message)
                print(message)


if __name__ == "__main__":
    Process(target=send_dir_status).start()
    Process(target=listen_peers).start()
    sleep(1)
    user()
    