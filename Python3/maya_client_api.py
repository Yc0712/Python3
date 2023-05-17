import socket
import traceback


class MayaClient(object):
    """
    """
    PORT = 20231  # e.g. 20230-Maya 2023(mel), 20181-Maya 2023(python)

    BUFFER_SIZE = 4096

    def __init__(self):
        self.maya_socket = None
        self.port = MayaClient.PORT

    def connect(self, port=-1):
        if port >= 0:
            self.port = port

        try:
            self.maya_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.maya_socket.connect(("localhost", self.port))
        except:
            traceback.print_exc()
            return False

        return True

    def disconnect(self):
        try:
            self.maya_socket.close()
        except:
            traceback.print_exc()
            return False

        return True

    def send(self, cmd):
        try:
            self.maya_socket.sendall(cmd.encode())
        except:
            traceback.print_exc()
            return None

        return self.recv()

    def recv(self):
        try:
            data = self.maya_socket.recv(maya_client.BUFFER_SIZE)
        except:
            traceback.print_exc()
            return None

        return data.decode().replace("\x00", "")

    def echo(self, text):
        cmd = "eval(\"'{0}'\")".format(text)

        return self.send(cmd)

    def new_file(self):
        cmd = "cmds.file(new=True, force=True)"

        return self.send(cmd)


if __name__ == "__main__":
    maya_client = MayaClient()
    if maya_client.connect():
        print("connect successfully")

        filename = maya_client.new_file()
        print(filename)

        if maya_client.disconnect():
            print("Disconnected")

    else:
        print("Failed to connect")
