import socket
import threading
import time


class Server:
    def __init__(self, port=9090, header=64):
        self.port = port
        self.header = header

        self.HOST = socket.gethostbyname(socket.gethostname())

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.HOST, self.port))
        self.server.listen()
        print(f"[STARTING] Listening on {self.HOST}, port {self.port}")
        print("[STARTING] Server starting...")

        class User:
            def __init__(self, cs, address):
                self.cs = cs
                self.address = address
                self.ip = self.address[0]
                self.users = []

            def targeted_send(self, msg, target_user):
                length = str(len(str(msg))).rjust(self.header, " ").encode('utf-8')
                target_user.cs.send(length)
                target_user.cs.send(msg.encode('utf-8'))

            def precv(self):
                recvheader = int(self.cs.recv(self.header).decode('utf-8'))
                message = self.cs.recv(recvheader).decode('utf-8')
                return message

            def broadcast(self, message):
                print(f"[RO_BROADCAST] " + message)
                for user in self.users:
                    self.targeted_send(message, user)

        self.accept()


    def handle(self, user):
        time.sleep(1)
        while True:
            try:
                message = user.precv().strip('\n ')
                user.broadcast(message)
            except Exception:
                self.users.remove(user)
                user.cs.close()
                print(f"[DISCONNECTION] {user.ip} disconnected")
                break


    def accept(self):
        while True:
            client, address = self.server.accept()
            print(f"[CONNECTION] {address[0]} connected.")

            user = User(client, address)
            self.users.append(user)

            thread = threading.Thread(target=self.handle, args=(user,))
            thread.start()
