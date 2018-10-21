#!/usr/bin/env python2
import argparse
import socket
import netifaces
import collections
import threading
import sys


BACKEND_PORT = 2025
BackendServer = collections.namedtuple('BackendServer', ['name', 'addr', 'backends'])
Backend = collections.namedtuple('Backend', ['name', 'type', 'user', 'time'])


def get_udp_broadcast_interfaces():
    broadcast_addresses = []

    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        if socket.SOCK_DGRAM in addrs:
            addrs = addrs[socket.SOCK_DGRAM]
            for addr in addrs:
                if 'broadcast' in addr:
                    broadcast_addresses.append(addr['broadcast'])

    return broadcast_addresses

def get_connection_string(username, command, server="", backend_class=""):
    string = bytearray(b"\0" * 50)

    string[0] = b"C"
    if command == "list":
        string[1] = chr(4)
    elif command == "connect":
        string[1] = chr(9)
    else:
        raise ValueError("invalid command")

    string[2:2 + len(username)] = username.encode('utf8')
    string[18:18 + len(server)] = server.encode('utf8')
    string[34:34 + len(backend_class)] = backend_class.encode('utf8')

    return bytes(string) 

# Gets a string up to a null terminator, returning the length advanced
def get_string(s):
    string = bytearray()
    count = 0
    for char in s:
        count += 1
        if char == 0 or char == '\0':
            break
        string.append(char)

    string = string.decode('utf8')
    return string, count

def parse_backend_response(response):
    if len(response) < 76:
        raise ValueError("Invalid response size")
    if response[0] != b"C":
        raise ValueError("Invalid response version")
    backends = []
    
    server_name = response[2:65].replace(b"\0", b"").decode('utf8')

    num_backends = response[66:75].replace(b"\0", b"").decode('utf8')
    num_backends = int(num_backends)

    read_cursor = 76
    for i in range(num_backends):
        backend_name, length = get_string(response[read_cursor:]) 
        read_cursor += length
        backend_type, length = get_string(response[read_cursor:])
        read_cursor += length

        # if the backend has a user connected
        if response[read_cursor] != b"\0":
            read_cursor += 1
            user, length = get_string(response[read_cursor:])
            read_cursor += length
            time, length = get_string(response[read_cursor:])
            read_cursor += length
        else:
            read_cursor += 1
            user = None
            time = None

        b = Backend(backend_name, backend_type, user, time)
        backends.append(b)

    return server_name, backends

def parse_port(response):
    if response[0] != b"C":
        raise ValueError("Invalid response version")

    server_name = response[2:65].replace(b"\0", b"").decode('utf8')
    port = response[76:]
    print(port)
    port = port.split()
    port = int(port[0])

    return port

def get_free_backend(backend_servers):
    for server in backend_servers:
        for backend in server.backends:
            if backend.user is None:
                return server, backend

def get_specific_backend(backend_servers, backend_name):
    for server in backend_servers:
        for backend in server.backends:
            if backend.name == backend_name:
                return server, backend
    return None, None

def get_backend_servers(backend_class="cortex"):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.bind(("0.0.0.0", 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 40000)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    addresses = get_udp_broadcast_interfaces()
    backend_servers = []

    connection_string = get_connection_string("test", command="list", backend_class=backend_class)
    for address in addresses:
        s.sendto(connection_string, (address, BACKEND_PORT))
        response, addr = s.recvfrom(125004)
        server_name, backends = parse_backend_response(response)

        backend_server = BackendServer(server_name, addr[0], backends)
        backend_servers.append(backend_server)

    # Close the udp socket
    s.close()
    return backend_servers

class GDBRequestHandler:
    def __init__(self, xinu_sock):
        self.xinu_sock = xinu_sock
        self.gdb_conn = None
        self.send_buffer = b""

        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.bind(("localhost", 0))
        _, self.port = self.listen_sock.getsockname()
        self.listen_sock.listen(1)

        thrd = threading.Thread(target=self.accept_connection)
        thrd.daemon = True
        thrd.start()
        
    def accept_connection(self):
        conn, addr = self.listen_sock.accept()
        self.gdb_conn = conn
        
        if len(self.send_buffer) > 0:
            self.gdb_conn.send(self.send_buffer)

        data = conn.recv(1024)
        while data is not None:
            self.xinu_sock.send(data)
            data = conn.recv(1024)

    def send_to_gdb(self, data):
        if self.gdb_conn is not None:
            self.gdb_conn.send(data)
        else:
            self.send_buffer += data

def main():
    parser = argparse.ArgumentParser(description='Access a Xinu backend with GDB support')
    parser.add_argument('--status', '-u', dest='status', action='store_true',
                        help='print out status of backends and exit')
    parser.add_argument('--type', '-t', '--class', '-c', dest='type', 
                        action='store', default='quark',
                        help='the type of backend board to connect to (default=quark)')
    parser.add_argument('backend', metavar='BACKEND', type=str, nargs='?', default=None,
                        help='optionally specify a backend board to connect to')
    args = parser.parse_args()

    backend_servers = get_backend_servers(backend_class=args.type)

    if args.status:
        row_format = "| {:<12}| {:<10}| {:<12}| {:<10}|"
        print(row_format.format("Backend", "Type", "User", "Time"))
        print("|-" + ('-' * 12) + '+-' + ('-' * 10) + '+-' + ('-' * 12) + '+-' + ('-' * 10) + '|') 
        for server in backend_servers:
            for backend in server.backends:
                print(row_format.format(
                    backend.name, backend.type, str(backend.user), str(backend.time)
                ))
        return

    if args.backend is None:
        server, backend = get_free_backend(backend_servers)
    else:
        server, backend = get_specific_backend(backend_servers, args.backend)
        if server is None:
            print("Backend {} not found, use --status to list backends".format(args.backend))
            return
        if backend.user is not None:
            print("Backend {} is in use by {}".format(backend.name, backend.user))
            return
    
    connection_string = get_connection_string("test", command="connect", 
                                              server=backend.name, 
                                              backend_class=backend.type)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 0))
    sock.sendto(connection_string, (server.addr, BACKEND_PORT))

    response, addr = sock.recvfrom(125004)
    addr = addr[0]

    sock.close()

    try:
        port = parse_port(response)
    except ValueError:
        print("Invalid port from server")
        raise ValueError()


    print("Connecting to {}, backend: {}, address: {}:{}".format(server.name, backend.name, addr, port))

    # Establish a tcp connection on the provided port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((addr, port))

    gdb_handler = GDBRequestHandler(s)

    print("GDB server listening on localhost:{}".format(gdb_handler.port))

    data = s.recv(1024)
    idx = 0

    byte, idx, data = recv_one(idx, data, s)
    while byte is not None:
        if byte == '\02':
            byte, idx, data = handle_gdb_msg(idx, data, s, gdb_handler)
        sys.stdout.write(byte)
        # sys.stdout.flush()
        byte, idx, data = recv_one(idx, data, s)

def handle_gdb_msg(idx, data, s, gdb_handler):
    byte, idx, data = recv_one(idx, data, s)
    if byte != b"G":
        return b"\02" + byte, idx, data
    else:
        msg = b""
        byte, idx, data = recv_one(idx, data, s)
        while byte != b'\04':
            msg += byte
            byte, idx, data = recv_one(idx, data, s)
        #do something with msg
        gdb_handler.send_to_gdb(msg)
        print("Got GDB msg:{}".format(msg))
        return b"", idx, data

def recv_one(idx, data, s):
    if idx != len(data):
        byte = data[idx]
        idx += 1
        return byte, idx, data
    else:
        data = s.recv(1024)
        idx = 1
        return data[0], idx, data

if __name__ == "__main__":
    main()
