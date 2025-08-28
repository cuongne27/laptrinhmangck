import socket
import tkinter as tk
from tkinter import messagebox
import threading

class TicTacToeClient:
    def __init__(self, host='localhost', port=5000, udp_port=5001):
        self.host = self.discover_server(udp_port) or host  # Tìm server qua UDP
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)  # Buffer size (tối ưu)
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
        self.buttons = []
        for i in range(3):
            for j in range(3):
                btn = tk.Button(self.root, text=' ', font=('Helvetica', 20), height=3, width=6,
                                command=lambda x=i*3+j: self.make_move(x))
                btn.grid(row=i, column=j)
                self.buttons.append(btn)

        # Thông báo cho người chơi 1 chờ người chơi 2
        if self.player == 'X':
            self.root.after(100, lambda: messagebox.showinfo("Chờ đối thủ", "Đang chờ người chơi khác tham gia..."))

        threading.Thread(target=self.receive, daemon=True).start()
        self.root.mainloop()

    def discover_server(self, udp_port):
        # Sử dụng UDP để tìm server (bao quát UDP discovery)
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
                data = self.sock.recv(1024).decode()
                if data:
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
        # Show whose turn it is
        self.root.title(f"Tic Tac Toe - Player {self.player} ({'Your turn' if self.player == self.current_player else 'Waiting...'})")

    def make_move(self, pos):
        if self.board[pos] == ' ' and self.player == self.current_player:
            for btn in self.buttons:
                btn['state'] = 'disabled'  # Disable all buttons until server responds
            try:
                self.sock.send(str(pos).encode())
            except socket.error as e:
                print(f"Send move error: {e}")

if __name__ == '__main__':
    client = TicTacToeClient()