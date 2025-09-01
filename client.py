import socket
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading

class TicTacToeClient:
    def __init__(self, host='localhost', port=5000, udp_port=5001):
        # Tìm server qua UDP hoặc dùng host mặc định
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
        self.chat_entry.bind('<Return>', lambda event: self.send_chat())
        self.send_btn = tk.Button(chat_frame, text="Gửi", command=self.send_chat)
        self.send_btn.pack(side='left', padx=5)

        threading.Thread(target=self.receive, daemon=True).start()
        self.root.mainloop()

    def discover_server(self, udp_port):
        # Tìm địa chỉ server qua UDP broadcast
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
        # Nhận dữ liệu từ server (bàn cờ hoặc chat)
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
        # Cập nhật giao diện bàn cờ và trạng thái nút
        for i in range(9):
            self.buttons[i]['text'] = self.board[i]
            state = 'normal' if self.board[i] == ' ' and self.player == self.current_player else 'disabled'
            self.buttons[i]['state'] = state
        self.root.title(f"Tic Tac Toe - Player {self.player} ({'Your turn' if self.player == self.current_player else 'Waiting...'})")

    def make_move(self, pos):
        # Gửi nước đi lên server nếu là lượt của mình
        if self.board[pos] == ' ' and self.player == self.current_player:
            for btn in self.buttons:
                btn['state'] = 'disabled'
            try:
                self.sock.send(str(pos).encode())
            except socket.error as e:
                print(f"Send move error: {e}")

    def send_chat(self):
        # Gửi tin nhắn chat lên server
        msg = self.chat_entry.get().strip()
        if msg:
            try:
                self.sock.send(f"CHAT:{self.player}: {msg}".encode())
                self.chat_entry.delete(0, tk.END)
            except socket.error as e:
                print(f"Send chat error: {e}")

    def update_chat(self, msg):
        # Hiển thị lịch sử chat
        self.chat_history['state'] = 'normal'
        self.chat_history.insert(tk.END, msg + '\n')
        self.chat_history['state'] = 'disabled'
        self.chat_history.see(tk.END)

if __name__ == '__main__':
    client = TicTacToeClient()

