import socket
import threading
import tkinter
import tkinter.scrolledtext
import random
import os
import time

VERSION = "v0.1.0"

PORT = 9090
HEADER = 64

PCOLS = {
    'NICK': {'ROOT': "/PCOL/NICK>>\\", 'DENY': "/PCOL/NICK>>/DENIED>>\\", 'VALIDATE': "/PCOL/NICK>>/VALID>>\\"},
    'ROOM_CODE': {'ROOT': "/PCOL/CODE>>\\"},
    'DISCONNECT': {'ROOT': "/PCOL/DCON>>\\"}
}


def wipe(string, speed=0.1, end='\n'):    # Animate strings
    for char in string:
        print(char, end='')
        time.sleep(speed)
    print(end)


def title():
    rand_file = os.path.join("data", "title-fonts", random.choice(os.listdir(os.path.join("data", "title-fonts"))))

    with open(rand_file, 'r') as f:
        print(f.read() + f"\t\t\t\t\t\t{VERSION}-client")

    print('\n\t\t\t', end='')
    wipe(f"BY M0U5S3", end='')
    print('\n\n\t\t\t\t\t\t\t\t\t', end='')
    wipe("GIT REPO: https://github.com/M0U5S3/chatsocket")


def gethost():
    uinp = input("\n\nEnter server IP: (or press enter to load saved IP) ")

    if not uinp:
        with open("data/host.txt", "r") as f:
            uinp = f.read()
            print("Joining " + uinp)

    elif input("save host ip? y/n ") == "y":
        print("saving ip")
        with open("data/host.txt", "w") as f:
            f.write(uinp)

    return uinp


class Client:

    def __init__(self, host, port):
        msg = tkinter.Tk()
        msg.withdraw()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
        except TimeoutError:
            print("TimeoutError: Server probably is offline or doesnt exist")
            quit()

        print("Launching GUI. You may minimise this window")

        self.gui_done = False
        self.running = True

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
        length = str(len(str(msg))).encode('utf-8') + b" " * (HEADER - len(str(len(str(msg))).encode('utf-8')))
        self.sock.send(length)
        self.sock.send(msg.encode('utf-8'))

    def precv(self):
        recvheader = int(self.sock.recv(HEADER).decode('utf-8'))
        message = self.sock.recv(recvheader).decode('utf-8')
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
            except Exception as e:
                print(e)
                exit()
                break


if __name__ == '__main__':
    #title()
    host = gethost()
    client = Client(host, PORT)
