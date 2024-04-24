import socket, threading
from datetime import datetime
from pylogging import Logger

HOSTNAME = "127.0.0.1"
MESSAGE_PORT = 8080
INFO_PORT = 8081

MESSAGE_CLIENTS = {}
INFO_CLIENTS = {}
WAITING_CLIENTS = []
MESSAGE_HISTORY = []
MAX_HISTORY = 1000
MESSAGE_SOC = None
INFO_SOC = None
QUIT = False

logging = Logger(file_logging=False)

def messages_thread(conn, addr) -> None:
    global WAITING_CLIENTS, MESSAGE_CLIENTS, MESSAGE_HISTORY, MAX_HISTORY, QUIT
    try:
        WAITING_CLIENTS.append(conn)
        name = conn.recv(8192).decode()
        if len(name) > 16:
            name = name[:16]
        if name == "":
            logging.info(f"{addr} disconnected!")
            conn.close()
            return
        WAITING_CLIENTS.remove(conn)
        MESSAGE_CLIENTS.update({addr: [name, conn]})
        logging.info(f"{addr} connected as \"{name}\" (connected: {len(MESSAGE_CLIENTS)})")
    except ConnectionResetError:
            try:
                conn.close()
                MESSAGE_CLIENTS.pop(addr)
                logging.info(f"{name} {addr} disconnected! ({len(MESSAGE_CLIENTS)} left)")
                return
            except:
                return
    except Exception as e:
        if QUIT:
            return
        logging.error("An exception occurrend:\n", e)
        conn.close()
        MESSAGE_CLIENTS.pop(addr)
        logging.info(f"{name} {addr} disconnected! ({len(MESSAGE_CLIENTS)} left)")
        return
    while True:
        try:
            msg = conn.recv(8192)
            
            if msg == b"":
                logging.info(f"connection closed with {addr}")
                MESSAGE_CLIENTS.pop(addr)
                logging.info(f"{name} {addr} disconnected! ({len(MESSAGE_CLIENTS)} left)")
                conn.close()
                break
            
            msg = msg.decode()
            for char in msg:
                if ord(char) < 32 and ord(char) != 10:
                    raise Exception("Escape sequence detected")
                
            
            logging.info(f"message received from \"{name}\" {addr}: \"{msg}\"")
            
            now = datetime.now().strftime("[%Y-%m-%d - %H:%M:%S]")
            MESSAGE_HISTORY.append(str([now, f"{name} ({addr[1]})", msg]))
            if len(MESSAGE_HISTORY) >= MAX_HISTORY:
                for _ in range(0, MAX_HISTORY/10):
                    MESSAGE_HISTORY.pop(0)
            for client in MESSAGE_CLIENTS:
                MESSAGE_CLIENTS[client][1].sendall(str([now, f"{name} ({addr[1]})", msg]).encode())
        except ConnectionResetError:
            conn.close()
            MESSAGE_CLIENTS.pop(addr)
            logging.info(f"{name} {addr} disconnected! ({len(MESSAGE_CLIENTS)} left)")
            break
        except Exception as e:
            if QUIT:
                break
            logging.error("An exception occurrend:\n", e)
            conn.close()
            MESSAGE_CLIENTS.pop(addr)
            logging.info(f"{name} {addr} disconnected! ({len(MESSAGE_CLIENTS)} left)")
            break

def info_thread(conn, addr) -> None:
    global INFO_CLIENTS, MESSAGE_CLIENTS,  MESSAGE_HISTORY, QUIT
    INFO_CLIENTS.update({addr: conn})
    while True:
        try:
            msg = conn.recv(8192)
            
            if msg == b'':
                conn.close()
                INFO_CLIENTS.pop(addr)
                break

            if msg == b'\x00':
                if len(MESSAGE_CLIENTS) > 0:
                    conn.sendall(str([MESSAGE_CLIENTS[x][0] +  " " + f"({str(x[1])})" for x in MESSAGE_CLIENTS]).encode() + b'\x00')
                else:
                    conn.sendall(b' ')
            elif msg == b'\x01':
                if len(MESSAGE_HISTORY) > 0:
                    conn.sendall(str(MESSAGE_HISTORY).encode() + b'\x01')
                else:
                    conn.sendall(b' ')
        except ConnectionResetError:
            conn.close()
            INFO_CLIENTS.pop(addr)
            break
        except Exception:
            if QUIT : 
                break
            conn.close()
            INFO_CLIENTS.pop(addr)
            break

def messages_handler() -> None:
    global HOSTNAME, MESSAGE_SOC, MESSAGE_PORT, QUIT, WAITING_CLIENTS, MESSAGE_CLIENTS
    while True:
        try:
            MESSAGE_SOC = socket.socket()
            MESSAGE_SOC.bind((HOSTNAME, MESSAGE_PORT))
            MESSAGE_SOC.listen()
            while True:
                conn, addr = MESSAGE_SOC.accept()
                logging.info(f"client {addr} just connected!")
                threading.Thread(target=messages_thread, args=[conn, addr]).start()
        except Exception as e:
            if QUIT:
                for x in MESSAGE_CLIENTS:
                    MESSAGE_CLIENTS[x][1].close()
                for x in WAITING_CLIENTS:
                    x.close()
                MESSAGE_SOC.close()
                break
            MESSAGE_SOC.close()
            logging.error("An exception occurred:\n", e)

def info_handler() -> None:
    global HOSTNAME, INFO_SOC, INFO_PORT, QUIT, MESSAGE_CLIENTS
    while True:
        try:
            INFO_SOC = socket.socket()
            INFO_SOC.bind((HOSTNAME, INFO_PORT))
            INFO_SOC.listen()
            while True:
                conn, addr = INFO_SOC.accept()
                threading.Thread(target=info_thread, args=[conn, addr]).start()
        except Exception:
            if QUIT:
                for x in INFO_CLIENTS:
                    INFO_CLIENTS[x].close()
                INFO_SOC.close()
                break
            INFO_SOC.close()

def main() -> None:
    global MESSAGE_SOC, INFO_SOC, QUIT
    threading.Thread(target=messages_handler).start()
    threading.Thread(target=info_handler).start()
    while True:
        try:
            i = input()
            if i == "exit" or i == "q" or i == "quit":
                QUIT = True
                MESSAGE_SOC.close()
                INFO_SOC.close()
                exit(0)
        except KeyboardInterrupt:
            QUIT = True
            MESSAGE_SOC.close()
            INFO_SOC.close()
            exit(0)

if __name__ == "__main__":
    main()

#TODO: add a chat rate limiter