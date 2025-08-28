import socket
import threading
import time
from binascii import hexlify  # Để demo chuyển đổi IP

class TicTacToeServer:
    def __init__(self, host='', port=5000, udp_port=5001):
        # Khởi tạo server, thiết lập thông tin mạng, bảng chơi, danh sách người chơi và các biến đồng bộ.
        self.host = host
        self.port = port
        self.udp_port = udp_port
        self.board = [' '] * 9
        self.current_player = 'X'
        self.players = []
        self.sockets = []
        self.lock = threading.Lock()

    def broadcast_server(self):
        # Gửi thông báo vị trí server qua UDP broadcast để client tự động phát hiện server.
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"SERVER_AT:{self.port}"
        while True:
            udp_sock.sendto(message.encode(), ('<broadcast>', self.udp_port))
            time.sleep(5)  # Broadcast mỗi 5s

    def start(self):
        # Khởi động server, lắng nghe kết nối từ 2 client, gán ký hiệu X/O cho từng người chơi và tạo luồng xử lý cho mỗi client.
        threading.Thread(target=self.broadcast_server, daemon=True).start()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(60)  # Đặt timeout socket 
        s.bind((self.host, self.port))
        s.listen(2)
        print(f"Server listening on {self.host}:{self.port}")

        try:
            for i in range(2):
                conn, addr = s.accept()
                print(f"Player {i+1} connected: {addr}")
                # Demo chuyển đổi IP address
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
        # Nhận nước đi từ client, kiểm tra hợp lệ, cập nhật bảng, kiểm tra thắng/thua/hòa và gửi trạng thái mới cho cả hai client.
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                move = int(data.decode())
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
        # Gửi trạng thái bảng hiện tại và lượt chơi cho tất cả client.
        board_str = ','.join(self.board) + ',' + self.current_player
        self.send_message_to_all(board_str)

    def send_message_to_all(self, msg):
        # Gửi một thông điệp (bảng hoặc kết quả) cho tất cả client.
        for conn in self.sockets:
            try:
                conn.send(msg.encode())
            except socket.error as e:
                print(f"Send error: {e}")

    def check_winner(self):
        # Kiểm tra xem có người chơi nào thắng chưa. Trả về ký hiệu người thắng hoặc None.
        winning = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for w in winning:
            if self.board[w[0]] == self.board[w[1]] == self.board[w[2]] != ' ':
                return self.board[w[0]]
        return None

if __name__ == '__main__':
    server = TicTacToeServer()
    server.start()