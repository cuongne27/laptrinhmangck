import socket
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
from binascii import hexlify

class TicTacToeServer:
    def __init__(self, host='', port=5000, udp_port=5001):
        self.host = host
        self.port = port
        self.udp_port = udp_port
        self.board = [' '] * 9
        self.current_player = 'X'
        self.players = []
        self.sockets = []
        self.lock = threading.Lock()

    def broadcast_server(self):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"SERVER_AT:{self.port}"
        while True:
            udp_sock.sendto(message.encode(), ('<broadcast>', self.udp_port))
            time.sleep(5)

    def start(self):
        threading.Thread(target=self.broadcast_server, daemon=True).start()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(60)
        s.bind((self.host, self.port))
        s.listen(2)
        print(f"Server listening on {self.host}:{self.port}")

        try:
            for i in range(2):
                conn, addr = s.accept()
                print(f"Player {i+1} connected: {addr}")
                packed_ip = socket.inet_aton(addr[0])
                print(f"Packed IP: {hexlify(packed_ip)}")
                self.players.append('X' if i == 0 else 'O')
                self.sockets.append(conn)
                conn.send(self.players[i].encode())
                threading.Thread(target=self.handle_client, args=(conn, i)).start()
        except socket.timeout:
            print("Connection timeout")
            return
        except socket.error as e:
            print(f"Socket error: {e}")
            return

        self.send_board()

    def handle_client(self, conn, player_idx):
        while True:
            try:
                data = conn.recv(2048)
                if not data:
                    break
                msg = data.decode()
                if msg.startswith("CHAT:"):
                    # Broadcast chat cho cả 2 client
                    self.send_message_to_all(msg)
                else:
                    move = int(msg)
                    with self.lock:
                        if self.board[move] == ' ' and self.current_player == self.players[player_idx]:
                            self.board[move] = self.current_player
                            winner = self.check_winner()
                            if winner:
                                self.send_message_to_all(f"{winner} wins!")
                                break
                            elif ' ' not in self.board:
                                self.send_message_to_all("Tie!")
                                break
                            self.current_player = 'O' if self.current_player == 'X' else 'X'
                            self.send_board()
            except socket.error as e:
                print(f"Error: {e}")
                break

    def send_board(self):
        board_str = ','.join(self.board) + ',' + self.current_player
        self.send_message_to_all(board_str)

    def send_message_to_all(self, msg):
        for conn in self.sockets:
            try:
                conn.send(msg.encode())
            except socket.error as e:
                print(f"Send error: {e}")

    def check_winner(self):
        winning = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for w in winning:
            if self.board[w[0]] == self.board[w[1]] == self.board[w[2]] != ' ':
                return self.board[w[0]]
        return None

if __name__ == '__main__':
    server = TicTacToeServer()
    server.start()