import socket
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading

class TicTacToeClient:
    def __init__(self, host='localhost', port=5000, udp_port=5001):
        self.host = self.discover_server(udp_port) or host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        try:
            self.sock.connect((self.host, self.port))
        except socket.error as e:
            print(f"Connection error: {e}")
            return
        self.player = self.sock.recv(1024).decode()
        self.current_player = 'X'
        self.board = [' '] * 9

        self.root = tk.Tk()
        self.root.title(f"Tic Tac Toe - Player {self.player}")
        self.root.resizable(False, False)

        # Frame cho bàn cờ
        board_frame = tk.Frame(self.root)
        board_frame.grid(row=0, column=0, padx=10, pady=10)

        self.buttons = []
        for i in range(3):
            for j in range(3):
                btn = tk.Button(board_frame, text=' ', font=('Helvetica', 20), height=3, width=6,
                                command=lambda x=i*3+j: self.make_move(x))
                btn.grid(row=i, column=j)
                self.buttons.append(btn)

        # Thông báo cho người chơi 1 chờ người chơi 2
        if self.player == 'X':
            self.root.after(100, lambda: messagebox.showinfo("Chờ đối thủ", "Đang chờ người chơi khác tham gia..."))

        # Frame cho chat
        chat_frame = tk.Frame(self.root)
        chat_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        tk.Label(chat_frame, text="Chat với đối thủ:").pack(anchor="w")

        self.chat_history = scrolledtext.ScrolledText(chat_frame, width=30, height=15, state='disabled', font=('Helvetica', 12))
        self.chat_history.pack(pady=5)

        self.chat_entry = tk.Entry(chat_frame, width=25, font=('Helvetica', 12))
        self.chat_entry.pack(side='left', pady=5)
        self.send_btn = tk.Button(chat_frame, text="Gửi", command=self.send_chat)
        self.send_btn.pack(side='left', padx=5)

        threading.Thread(target=self.receive, daemon=True).start()
        self.root.mainloop()

    def discover_server(self, udp_port):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(('', udp_port))
        udp_sock.settimeout(10)
        try:
            data, addr = udp_sock.recvfrom(1024)
            if data.startswith(b"SERVER_AT:"):
                port = int(data.decode().split(':')[1])
                print(f"Discovered server at {addr[0]}:{port}")
                return addr[0]
        except socket.timeout:
            print("No server discovered")
        return None

    def receive(self):
        while True:
            try:
                data = self.sock.recv(2048).decode()
                if data:
                    if data.startswith("CHAT:"):
                        chat_msg = data[5:]
                        self.root.after(0, lambda: self.update_chat(chat_msg))
                    else:
                        parts = data.split(',')
                        if len(parts) == 10:
                            self.board = parts[:9]
                            self.current_player = parts[9]
                            self.root.after(0, self.update_board)
                        else:
                            self.root.after(0, lambda: messagebox.showinfo("Game Over", data))
                            self.root.after(0, self.root.quit)
            except socket.error as e:
                print(f"Receive error: {e}")
                break

    def update_board(self):
        for i in range(9):
            self.buttons[i]['text'] = self.board[i]
            state = 'normal' if self.board[i] == ' ' and self.player == self.current_player else 'disabled'
            self.buttons[i]['state'] = state
        self.root.title(f"Tic Tac Toe - Player {self.player} ({'Your turn' if self.player == self.current_player else 'Waiting...'})")

    def make_move(self, pos):
        if self.board[pos] == ' ' and self.player == self.current_player:
            for btn in self.buttons:
                btn['state'] = 'disabled'
            try:
                self.sock.send(str(pos).encode())
            except socket.error as e:
                print(f"Send move error: {e}")

    def send_chat(self):
        msg = self.chat_entry.get().strip()
        if msg:
            try:
                self.sock.send(f"CHAT:{self.player}: {msg}".encode())
                self.chat_entry.delete(0, tk.END)
            except socket.error as e:
                print(f"Send chat error: {e}")

    def update_chat(self, msg):
        self.chat_history['state'] = 'normal'
        self.chat_history.insert(tk.END, msg + '\n')
        self.chat_history['state'] = 'disabled'
        self.chat_history.see(tk.END)

if __name__ == '__main__':
    client = TicTacToeClient()

import socket
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