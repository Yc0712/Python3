import socket

BUFFER_SIZE = 4096

PORT = 21111

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("localhost", PORT))
    sock.listen()

    while True:

        connection, address = sock.accept()

        with connection:
            print("Connection Established:{0}".format(address))

            while True:
                data = connection.recv(BUFFER_SIZE)

                if not data:
                    break

                if data.decode().strip() == "stop":
                    connection.sendall("Stopping server".encode())
                    connection.shutdown(1)
                    connection.close()
                    exit()

                connection.sendall(data)
