import socket
import struct
import time

def create_dns_request(domain_name):
    # Transaction ID: 2 bytes
    transaction_id = b'\xaa\xbb'

    # Flags: Standard query with recursion desired (1 byte each)
    flags = b'\x01\x00'

    # Questions, Answer RRs, Authority RRs, Additional RRs: 2 bytes each
    qdcount = b'\x00\x01'
    ancount = b'\x00\x00'
    nscount = b'\x00\x00'
    arcount = b'\x00\x00'

    # Header
    header = transaction_id + flags + qdcount + ancount + nscount + arcount

    # Convert domain name to DNS query format
    domain_parts = domain_name.split('.')
    query = b''
    for part in domain_parts:
        query += struct.pack('B', len(part)) + part.encode('utf-8')
    query += b'\x00'  # End of domain name

    # Type: A (1), Class: IN (1)
    qtype = b'\x00\x01'
    qclass = b'\x00\x01'

    # Full DNS request
    dns_request = header + query + qtype + qclass
    return dns_request

def parse_dns_response(response):
    # Skip the header (12 bytes) and the question section
    answer_start = response[12:].find(b'\xc0') + 12
    answer = response[answer_start:]
    
    # Extract the IP address from the answer section
    ip_start = answer.find(b'\x00\x01\x00\x01') + 10  # After Type, Class, TTL
    ip_address = '.'.join(map(str, answer[ip_start:ip_start+4]))
    return ip_address

def measure_rtt(send_func, *args):
    start_time = time.time()
    result = send_func(*args)
    rtt = time.time() - start_time
    return result, rtt

def main():
    domain = "tmz.com"
    dns_servers = [
        "8.8.8.8",  # Google DNS
        "1.1.1.1",  # Cloudflare DNS
        "9.9.9.9"   # Quad9 DNS
    ]
    port = 53

    for dns_server in dns_servers:
        try:
            # Create UDP socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(10)

                # Build and send DNS request
                dns_request = create_dns_request(domain)
                send_func = lambda: sock.sendto(dns_request, (dns_server, port))
                _, rtt_dns = measure_rtt(send_func)
                print(f"RTT to DNS server ({dns_server}): {rtt_dns:.4f} seconds")

                # Receive DNS response
                response, _ = sock.recvfrom(512)
                ip_address = parse_dns_response(response)
                print(f"Resolved IP for {domain}: {ip_address}")

                # Make HTTP request to resolved IP
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
                    tcp_sock.settimeout(10)
                    send_func = lambda: tcp_sock.connect((ip_address, 80))
                    _, rtt_http = measure_rtt(send_func)

                    # Send HTTP GET request
                    http_request = f"GET / HTTP/1.1\r\nHost: {domain}\r\n\r\n"
                    tcp_sock.sendall(http_request.encode('utf-8'))
                    response = tcp_sock.recv(4096)
                    print("HTTP response received.")
                
                print(f"RTT to {domain} server: {rtt_http:.4f} seconds")
                break
        except Exception as e:
            print(f"Error with DNS server {dns_server}: {e}")
            continue

if __name__ == "__main__":
    main()
