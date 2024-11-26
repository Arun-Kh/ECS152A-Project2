# Rahul Padhi 
# ECS 152A Part 1 DNS client from scratch
import socket
import struct
import time


def build_dns_query(domain_name):
    # Transaction ID: Random 16-bit identifier
    transaction_id = b'\xaa\xbb'

    # Flags: Standard query (0x0100)
    flags = b'\x01\x00'

    # Questions, Answer RRs, Authority RRs, Additional RRs
    qdcount = b'\x00\x01'  # One question
    ancount = b'\x00\x00'  # No answers
    nscount = b'\x00\x00'  # No name servers
    arcount = b'\x00\x00'  # No additional records

    # Question Section
    qname = b''.join(
        struct.pack('B', len(part)) + part.encode('utf-8') for part in domain_name.split('.')
    ) + b'\x00'  # End of QNAME
    qtype = b'\x00\x01'  # Type A
    qclass = b'\x00\x01'  # Class IN

    # Combine all sections
    return transaction_id + flags + qdcount + ancount + nscount + arcount + qname + qtype + qclass


def parse_dns_response(data):
    transaction_id = data[:2]
    flags = data[2:4]
    qdcount = struct.unpack('>H', data[4:6])[0]
    ancount = struct.unpack('>H', data[6:8])[0]
    nscount = struct.unpack('>H', data[8:10])[0]
    arcount = struct.unpack('>H', data[10:12])[0]

    # Parse the answer section
    offset = 12  # Start of the Question Section
    for _ in range(qdcount):
        while data[offset] != 0:
            offset += 1
        offset += 5  # Skip null byte, QTYPE, QCLASS

    ip_addresses = []
    for _ in range(ancount):
        offset += 10  # Skip Name, Type, Class, TTL
        rdlength = struct.unpack('>H', data[offset:offset + 2])[0]
        offset += 2
        rdata = data[offset:offset + rdlength]
        if len(rdata) == 4:  # IPv4 address
            ip = '.'.join(map(str, rdata))
            ip_addresses.append(ip)
        offset += rdlength

    return ip_addresses


def measure_rtt(target, query):
    start_time = time.time()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(10)
        s.sendto(query, (target, 53))
        data, _ = s.recvfrom(512)
    end_time = time.time()
    return data, (end_time - start_time) * 1000  # RTT in milliseconds


def dns_client():
    domain_name = "tmz.com"
    public_dns_resolvers = ["8.8.8.8", "8.8.4.4"]  # Google's public DNS servers
    query = build_dns_query(domain_name)

    for resolver in public_dns_resolvers:
        try:
            print(f"Querying {resolver}...")
            response, rtt = measure_rtt(resolver, query)
            print(f"RTT to resolver {resolver}: {rtt:.2f} ms")
            ip_addresses = parse_dns_response(response)
            if ip_addresses:
                print(f"Resolved IP addresses for {domain_name}: {ip_addresses}")
                return ip_addresses, resolver
        except socket.timeout:
            print(f"Resolver {resolver} timed out.")
    return None, None


def http_request(ip_address):
    request = (
        "GET / HTTP/1.1\r\n"
        f"Host: tmz.com\r\n"
        "Connection: close\r\n\r\n"
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        start_time = time.time()
        s.connect((ip_address, 80)) # using port 80 
        s.sendall(request.encode())
        response = s.recv(4096)
        end_time = time.time()

    rtt = (end_time - start_time) * 1000  # RTT in milliseconds
    print(f"RTT to {ip_address}: {rtt:.2f} ms")
    print("HTTP Response Header:")
    print(response.decode().split("\r\n\r\n")[0])


if __name__ == "__main__":
    ip_addresses, resolver = dns_client()
    if ip_addresses:
        for ip in ip_addresses:
            http_request(ip)
    else:
        print("Failed to resolve the domain.")
