"""
Создание сервера
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login:str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                # проверка логина
                if self.login in self.server.logins:
                    self.transport.write(f"Пытаешься выдать себя за {self.login}? Найди себе другой логин.".encode())
                    self.login = None
                else:
                    self.transport.write(f"Привет, {self.login}!".encode())
                    self.server.logins.append(self.login)
                    self.send_history()  # отправка сообщений


        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        if len(self.server.messages) == 10:  # сохраненние десяти последних соообщений
            self.server.messages.pop(0)
        self.server.messages.append(encoded)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def send_history(self):  # функция, отправляющая последние сообщения
        for i in range(len(self.server.messages)):
            self.transport.write(self.server.messages[i])
            self.transport.write("\n".encode())


    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    logins: list
    messages: list


    def __init__(self):
        self.clients = []
        self.messages = []
        self.logins = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(self.create_protocol, "127.0.0.1", 8888)

        print("Сервер запущен.")

        await coroutine.serve_forever()

process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
