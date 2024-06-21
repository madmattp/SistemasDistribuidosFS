import socket
from multiprocessing import Process, Manager, Value
import pickle
from time import sleep
from random import choice

# PORTS:
#   20001 -> guest-to-border
#   20003 -> guest-to-border (commands)

def view_files(file_list):
    while(True):
        sleep(1)
        print("=========\nFILES:")
        for entry in file_list:
            print(entry)

def handle_connection(connection, node_address, file_list, guest_nodes):
    def cleanup():  # Função que limpa todos os arquivos com o endereço do nó.
        # Por motivos que vão além do meu entendimento, eu tenho que fazer a limpeza
        # 3 vezes, porque sempre sobra algum arquivo com o endereço de um nó perdido.
        # Palavras não são suficientes para explicar minha confusão. Mas esse objeto
        # "ListProxy" não é tão confiável.
        try:
            i = 0
            while i < 3:
                for item in file_list:
                    if item[1] == node_address:
                        file_list.remove(item)
                i += 1
        except ValueError:
            pass
    try:
        temp = []
        while(True):
            message = connection.recv(1024)
            files = pickle.loads(message)
            if((len(files) < 1) or (files == temp)):
                continue
            else:
                # Remover apenas os arquivos que sumiram e adicionar apenas os novos é muito trabalho,
                # como eu valorizo muito o meu tempo, irei limpar apenas os arquivos que possuem o mesmo
                # endereçamento da conexão com esse cleanup(). Não é rápido, mas é consistente.
                cleanup() 
                x = [file for file in files]
                for file in x:
                    file_list.append([file, node_address])
                temp = files

    except EOFError:   # Caso a conexão seja perdida, remover arquivos linkados a conexão
        print(f"=========\nConexão com Node {node_address} perdida.\n=========")
        cleanup()
        # Esses try except já não fazem sentido pra mim, esse "ListProxy" é terrível!
        try:
            i = 0
            while(i < 3):  # Deus, me perdoe por usar mais um "while" por causa desse ListProxy...
                if len(guest_nodes) == 0:
                    i += 1
                    continue
                for node in guest_nodes:
                    if node[1] == node_address:
                        # acontece dele achar o nó na lista, printar ele, e depois
                        #dizer que ele não existe... gaslight?
                        guest_nodes.remove(node)
                i += 1
        except:
            pass
                    

def get_guests():
    BORDER_ADDRESS = "0.0.0.0"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (BORDER_ADDRESS, 20001)
    server_socket.bind(server_address)

    server_socket.listen()

    while(True):
        connection, client_address = server_socket.accept()
        guest_nodes.append([connection, client_address])
        Process(target=handle_connection, args=(connection, client_address, file_list, guest_nodes)).start()

def handle_front(connection, client_address, file_list, guest_nodes):
    while(True):
        message = connection.recv(1024)
        message = message.decode("utf-8")
        print("=========")
        print(f"[{client_address}] MESSAGE: {message}")
        
        if message.startswith("REQUEST"):
            
            message = message[8:]
            
            opts = [] # Guarda arquivos identicos, caso existam (opção para balanceamento)
            for file in file_list:
                if file[0] == message:
                    opts.append(file)

            if len(opts) == 0:
                connection.send(pickle.dumps("Arquivo Inexistente!"))
            else:
                
                file = choice(opts) # Escolhe aleatoriamente um endereço. BaLaNcAmENtO 
                connection.send(pickle.dumps(file))

        elif message == "NODES":
            temp = []
            i = 0
            while(i != 3):
                for address in guest_nodes:
                    temp.append(address[1])
                i += 1
            connection.send(pickle.dumps(temp))

        elif message == "FILES":
            temp = []
            i = 0
            while(i != 3):
                for file in file_list:
                    temp.append(file[0])
                i += 1
            temp = list(set(temp)) # Remove duplicatas
            connection.send(pickle.dumps(temp))

        elif message == "HELP":
            msg = """
                HELP - MOSTRA ESSA LISTA DE COMANDOS :D
                NODES - EXIBE OS NÓS LIGADOS AO SISTEMA.
                FILES - EXIBE TODOS OS ARQUIVOS NO SISTEMA.
                REQUEST <file> - FAZ REQUEST DE DOWNLOAD DE ARQUIVO.
            """
            connection.send(pickle.dumps(msg))
        else:
            msg = """
                HELP - MOSTRA ESSA LISTA DE COMANDOS :D
                NODES - EXIBE OS NÓS LIGADOS AO SISTEMA.
                FILES - EXIBE TODOS OS ARQUIVOS NO SISTEMA.
                REQUEST <file> - FAZ REQUEST DE DOWNLOAD DE ARQUIVO.
            """
            connection.send(pickle.dumps(msg))

def get_front(file_list, guest_nodes):
    BORDER_ADDRESS = "0.0.0.0"
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (BORDER_ADDRESS, 20003)
    server_socket.bind(server_address)

    server_socket.listen()

    while(True):
        connection, client_address = server_socket.accept()
        Process(target=handle_front, args=(connection, client_address, file_list, guest_nodes)).start()


if __name__ == "__main__":
    manager = Manager()
    file_list = manager.list()
    manager1 = Manager()
    guest_nodes = manager1.list()

    Process(target=view_files, args=(file_list,)).start()
    Process(target=get_front, args=(file_list, guest_nodes)).start()
    get_guests()