import socket
import threading
import time
import rsa
from cryptography.fernet import Fernet
import pickle
import tkinter
import tkinter.scrolledtext


VERSION = "v0.1.0"
REPOSITORY = "https://github.com/M0U5S3/PyChat"


class User:
    def __init__(self, cs, address):
        self.cs = cs
        self.address = address
        self.ip = self.address[0]
        self.fernet = None


class PyServer:
    def __init__(self, port, header=64, rsa_keys_size=2048):
        print(f'Thank you for using PyChat {VERSION} | The fully encrypted communications package by M0U5S3')
        print(f'Github Repo: {REPOSITORY}')

        self.port = int(port)
        self.header = int(header)
        self.RSA_keys_size = int(rsa_keys_size)

        self.users = []
        self.commands = []

        self.HOST = socket.gethostbyname(socket.gethostname())

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.HOST, self.port))
        self.server.listen()
        print(f"[STARTING] Listening on {self.HOST}, port {self.port}")
        print("[STARTING] Server starting...")

        # Attributes to be set by user
        self.message_prefix = ''
        self.command_prefix = '/'

        self.publicKey, self.privateKey = rsa.newkeys(self.RSA_keys_size)
        print(f'[RSA_ENCRYPTION] Generated new keypair, size: {self.RSA_keys_size}')

        self.accept_thread = threading.Thread(target=self.accept)
        self.handle_thread = threading.Thread(target=self.handle)

    def start_thread(self):
        self.accept_thread.start()

    def handle(self, user):

        def detect_command(string):
            for command in self.commands:
                if self.command_prefix + command[0] == string:
                    command[1](string)

        time.sleep(1)
        while True:
            try:
                message = self.precv(user, encrypted=True).strip('\n ')
                self.broadcast(self.construct_message_prefix(user) + message)
                detect_command(message)
            except Exception:
                self.users.remove(user)
                user.cs.close()
                print(f"[DISCONNECTION] {user.ip} disconnected")
                break

    def accept(self):

        def encrytion_handshake(user):
            length = str(len(pickle.dumps(self.publicKey))).rjust(self.header, " ").encode('utf-8')
            user.cs.send(length)
            user.cs.send(pickle.dumps(self.publicKey))

            recvheader = int(user.cs.recv(self.header).decode('utf-8'))
            masterkey = rsa.decrypt(pickle.loads(user.cs.recv(recvheader)), self.privateKey)
            print(f"[RSA_HANDSHAKE] {user.ip}'s masterkey: {masterkey.decode('utf-8')}")

            user.fernet = Fernet(masterkey)
            print(f'[RSA_HANDSHAKE] Secure connection to {user.ip} has been established')

        while True:
            client, address = self.server.accept()
            print(f"[CONNECTION] {address[0]} connected.")

            user = User(client, address)
            self.users.append(user)

            encrytion_handshake(user)

            self.handle_thread = threading.Thread(target=self.handle, args=(user,))
            self.handle_thread.start()

    def targeted_send(self, msg, target_user):
        msg = pickle.dumps(target_user.fernet.encrypt(msg.encode('utf-8')))
        length = str(len(msg)).rjust(self.header, " ").encode('utf-8')
        target_user.cs.send(length)
        target_user.cs.send(msg)

    def precv(self, from_user, encrypted=False):
        recvheader = int(from_user.cs.recv(self.header).decode('utf-8'))
        if encrypted:
            message = from_user.fernet.decrypt(pickle.loads(from_user.cs.recv(recvheader))).decode('utf-8')
        else:
            message = pickle.loads(from_user.cs.recv(recvheader).decode('utf-8'))
        return message

    def broadcast(self, message):
        print(f"[GLOBAL_BROADCAST] " + message)
        for user in self.users:
            self.targeted_send(message, user)

    def construct_message_prefix(self, user):
        def replace(string, sub_string, replace_with):
            index = string.find(sub_string)
            if index != -1:
                constructed_prefix = string[:index] + replace_with + string[index + 2:]
                return constructed_prefix
            return string

        return replace(self.message_prefix, '%u', user.ip)

    def set_message_prefix(self, prefix):
        self.message_prefix = prefix
        # self.construct_message_prefix replaces %u with username

    def make_command(self, command_name, on_recieve_function):
        self.commands.append((command_name, on_recieve_function))

    def set_command_prefix(self, prefix):
        self.command_prefix = prefix


class PyClient:

    def __init__(self, host, port, header=64):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((host, port))
        except TimeoutError:
            print("TimeoutError: Server probably is offline or doesnt exist")
            quit()

        print("Launching GUI. You may minimise this window")

        self.gui_done = False
        self.running = True

        self.port = port
        self.header = header

        self.ferkey = Fernet.generate_key()
        self.fernet = Fernet(self.ferkey)

        rh = int(self.sock.recv(self.header).decode('utf-8'))
        server_pubkey = pickle.loads(self.sock.recv(rh))

        serialised_masterkey = pickle.dumps(rsa.encrypt(self.ferkey, server_pubkey))
        length = str(len(serialised_masterkey)).rjust(self.header, " ").encode('utf-8')

        self.sock.send(length)
        self.sock.send(serialised_masterkey)

        gui_thread = threading.Thread(target=self.gui_loop)
        recieve_thread = threading.Thread(target=self.recieve_loop)

        gui_thread.start()
        recieve_thread.start()

    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.configure(bg="lightgray")

        self.chat_label = tkinter.Label(self.win, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.pack(padx=20, pady=5)

        self.text_area = tkinter.scrolledtext.ScrolledText(self.win)
        self.text_area.pack(padx=20, pady=5)
        self.text_area.config(state="disabled")

        self.msg_label = tkinter.Label(self.win, text="Message:", bg="lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.pack(padx=20, pady=5)

        self.input_area = tkinter.Text(self.win, height=3)
        self.input_area.pack(padx=20, pady=5)

        self.send_button = tkinter.Button(self.win, text="Send", command=self.write)
        self.send_button.config(font=("Arial", 12))
        self.send_button.pack(padx=20, pady=5)

        self.gui_done = True

        self.win.protocol("WM_DELETE_WINDOW", self.stop)

        self.win.mainloop()

    def psend(self, msg):
        msg = pickle.dumps(self.fernet.encrypt(msg.encode('utf-8')))
        length = str(len(msg)).rjust(self.header, " ").encode('utf-8')
        self.sock.send(length)
        self.sock.send(msg)

    def precv(self):
        recvheader = int(self.sock.recv(self.header).decode('utf-8'))
        message = self.fernet.decrypt(pickle.loads(self.sock.recv(recvheader))).decode('utf-8')
        return message

    def write(self):
        message = self.input_area.get('1.0', 'end')
        self.psend(message)
        self.input_area.delete('1.0', 'end')

    def stop(self):
        self.running = False
        self.win.destroy()
        self.sock.close()
        exit(0)

    def recieve_loop(self):
        while self.running:
            try:
                message = self.precv()

                if self.gui_done:
                    self.text_area.config(state='normal')
                    self.text_area.insert('end', message + "\n")
                    self.text_area.yview('end')
                    self.text_area.config(state='disabled')
            except ConnectionAbortedError:
                pass
