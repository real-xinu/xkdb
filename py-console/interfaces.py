# Linux only, utility functions to get broadcast addresses of all
# the network interfaces on the system.
import socket
import fcntl
import struct

SIOCGIFBRDADDR = 0x8919

def get_interfaces():
    interfaces = []
    with open("/proc/net/dev", "r") as f:
        for i, line in enumerate(f):
            # The first 2 lines are headers
            if i <= 1:
                continue
            iface_name = line.split(':')[0].strip()
            interfaces.append(iface_name)

    return interfaces

def get_broadcast_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        SIOCGIFBRDADDR,
        struct.pack('256s', ifname[:15])
    )[20:24])

def get_udp_broadcast_addrs():
    addresses = []

    for iface in get_interfaces():
        try:
            address = get_broadcast_ip_address(iface)

            if address == "0.0.0.0":
                continue

            addresses.append(address)
        except IOError:
            pass

    return addresses
