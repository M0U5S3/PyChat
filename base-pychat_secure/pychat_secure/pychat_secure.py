import socket
import threading
import time
import rsa
from cryptography.fernet import Fernet
import pickle
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog
import hashlib


VERSION = "v1.0.0"
REPOSITORY = "https://github.com/M0U5S3/pychat_secure"


class User:
    def __init__(self, cs, address):
        self.cs = cs
        self.address = address
        self.ip = self.address[0]
        self.fernet = None


class PyServer:
    def __init__(self, port, password, log_file, header=64, rsa_keys_size=4096):
        print(f'Thank you for using PyChat {VERSION} | The fully encrypted communications package by M0U5S3')
        print(f'Github repository: {REPOSITORY}\n')
        print('<< SERVER LOGS >>\n')
        self.log('initialisation', f'New server ({self}) initialised')

        self.port = int(port)
        self.header = int(header)
        self.RSA_keys_size = int(rsa_keys_size)
        self.password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        self.log_file = log_file

        self.log('startup', f'Password set to {self.password}')

        self.users = []
        self.commands = []

        self.HOST = socket.gethostbyname(socket.gethostname())

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.HOST, self.port))
        self.server.listen()
        self.log('startup', f'Listening on {self.HOST}, port {self.port}')

        # Attributes to be set by user
        self.message_prefix = ''
        self.command_prefix = '/'

        start = time.process_time()
        self.publicKey, self.privateKey = rsa.newkeys(self.RSA_keys_size)
        self.log(
            'rsa_encryption',
            f'Generated new keypair in {str(round(time.process_time() - start, 2))} second(s), '
            f'size: {self.RSA_keys_size}'
        )

        self.accept_thread = threading.Thread(target=self.accept)
        self.handle_thread = threading.Thread(target=self.handle)

    def start_thread(self):
        self.accept_thread.start()
        self.log('startup', 'Server thread is running')

    @staticmethod
    def log(catagory, string):
        print(f'[{catagory.upper()}] {string}')
        with open('log.txt', 'a') as f:
            f.write(f'[{catagory.upper()}] {string}\n')

    def handle(self, client, address):
        def encrytion_handshake(user):
            length = str(len(pickle.dumps(self.publicKey))).rjust(self.header, " ").encode('utf-8')
            user.cs.send(length)
            user.cs.send(pickle.dumps(self.publicKey))

            recvheader = int(user.cs.recv(self.header).decode('utf-8'))
            masterkey = rsa.decrypt(pickle.loads(user.cs.recv(recvheader)), self.privateKey)
            self.log('rsa_handshake', f"{user.ip}'s masterkey: {masterkey.decode('utf-8')}")

            user.fernet = Fernet(masterkey)
            self.log('rsa_handshake', f'Secure connection to {user.ip} has been established')

        def check_password():
            while True:
                if hashlib.sha256(self.precv(user, encrypted=True).encode('utf-8')).hexdigest() == self.password:
                    self.targeted_send('VALID', user)
                    self.log('authentication', f'{user.ip} access granted')
                    return True
                else:
                    self.targeted_send('INVALID', user)
                    self.log('authentication', f'{user.ip} access denied')

        def detect_command(user, string):
            def execute(args):
                try:
                    command['func'](user=user, args=args)
                except Exception as e:
                    self.log('error',
                             f"An exception occurred when trying to execute the '{command['name']}' command's function")
                    raise e

            def remove_all_elements(list_, remove_string):
                try:
                    while True:
                        list_.remove(remove_string)
                except ValueError:
                    # All elements have been removed
                    pass

            for command in self.commands:
                i = len(self.command_prefix + command['name'])
                if self.command_prefix + command['name'] == string[:i]:  # Detect the first part of the command

                    self.log('command_detection', f"Command detected ({user.ip}): "
                                                  f"'{self.command_prefix}{command['name']}'")
                    listed_args = string.split(' ')
                    remove_all_elements(listed_args, '')

                    if command['return_data']:
                        if command['expected_args'] == -1:
                            # When expected amount of args is not set infinite arguments are allowed
                            execute(listed_args)
                            break

                        else:
                            if len(listed_args) == command['expected_args']:
                                execute(listed_args)
                                break
                            else:
                                self.targeted_send(f"[Server] Error: expected {command['expected_args']} argument(s)", user)
                                break
                    else:
                        command['func']()
                        break
            else:
                self.targeted_send('[Server] Command is not valid', user)

        user = User(client, address)
        encrytion_handshake(user)

        run = True
        try:
            check_password()
        except ConnectionResetError:
            run = False
            self.log('disconnection', f'{user.ip} disconnected')
        except ValueError:
            run = False
            self.log('disconnection', f'{user.ip} disconnected')
        else:
            self.users.append(user)

        while run:
            try:
                message = self.precv(user, encrypted=True).strip('\n ')
                if message[:len(self.command_prefix)] != self.command_prefix:
                    self.broadcast(self.construct_message_prefix(user) + message)
                else:
                    detect_command(user, message)
            except ConnectionResetError:
                self.users.remove(user)
                user.cs.close()
                self.log('disconnection', f'{user.ip} disconnected')
                break

    def accept(self):
        while True:
            client, address = self.server.accept()
            self.log('connection', f'{address[0]} connected')

            self.handle_thread = threading.Thread(target=self.handle, args=(client, address))
            self.handle_thread.start()

    def targeted_send(self, msg, target_user):
        msg = pickle.dumps(target_user.fernet.encrypt(str(msg).encode('utf-8')))
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

    def broadcast(self, message, confidential=True):
        if confidential:
            self.log('global_broadcast', 'A confidential message was broadcasted')
        else:
            self.log('global_broadcast', message)

        for user in self.users:
            self.targeted_send(message, user)

    def construct_message_prefix(self, user):
        def replace(string, sub_string, replace_with, escape_char='%'):
            index = string.find(sub_string)
            if index != -1:
                if not string[index-1] == escape_char and index != 0:
                    constructed_prefix = string[:index] + replace_with + string[index + 2:]
                    return constructed_prefix
            return string

        final = replace(self.message_prefix, '%H', time.strftime('%H', time.localtime()))
        final = replace(final, '%M', time.strftime('%M', time.localtime()))
        final = replace(final, '%u', user.ip)
        final = replace(final, '%%', '%')

        '''

            --===FORMAT CODES FOR MESSAGE PREFIX===--

            >> User Data
                %u | user ip

            >> Time & Date
                %H | current hour (24hr)
                %M | current minute (24hr)

            >> Other
                %% | escape '%'

        '''

        return final

    def set_message_prefix(self, prefix):
        self.message_prefix = str(prefix)

    def make_command(self, command_name, on_recieve_function, expected_args=-1, return_data=False):
        self.commands.append({
            'name': command_name,
            'func': on_recieve_function,
            'expected_args': expected_args,
            'return_data': return_data
            })

    def set_command_prefix(self, prefix):
        self.command_prefix = str(prefix)


class PyClient:

    def __init__(self, host, port, header=64):

        def send_password():
            msg = tkinter.Tk()
            msg.withdraw()
            while True:
                password = simpledialog.askstring("Password", "Please enter the password", parent=msg)
                self.psend(password)
                if self.precv() == 'VALID':
                    break

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

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

        send_password()

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
