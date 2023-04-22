import socket
import sys

BUFFER_SIZE = 4096

prot = 21111

if len(sys.argv) > 1:
    prot = sys.argv[1]

maya_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 连接
maya_socket.connect(("localhost", prot))

maya_socket.sendall("stop".encode())  # 发送数值
data = maya_socket.recv(BUFFER_SIZE)  # 从maya返回数值 等待回复
print(data.decode())
#
# maya_socket.sendall("cmds.polySphere()".encode())  # 发送数值
# data = maya_socket.recv(BUFFER_SIZE)  # 从maya返回数值 等待回复
# result = eval(data.decode().replace("\x00", ""))
# print(result)

maya_socket.close()
