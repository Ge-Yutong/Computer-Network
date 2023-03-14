import socket
from socket import timeout
import struct
import signal
#primitives
START_PACKET_ID = 0xFFFF
END_PACKET_ID = 0xFFFF
ACC_PERMISSION = 0xFFF8
NOT_PAID = 0xFFF9
NOT_EXIST = 0xFFFA
ACCESS_OK = 0xFFFB
MAX_TIMEOUT = 3
MAX_RETRY = 3
#address
local_ip = '127.0.0.1'
local_port = 6000
#buffersize
buffer_size = 270
#technology
G_2 = 2
G_3 = 3
G_4 = 4
G_5 = 5
#bind address
client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
#set timeout
client_socket.settimeout(MAX_TIMEOUT)

def create_permission_request(client_id, segment_no, technology, subscriber_no):
    data_packet = struct.pack('!H', START_PACKET_ID)
    data_packet += struct.pack('!B', client_id)
    data_packet += struct.pack('!H', ACC_PERMISSION)
    data_packet += struct.pack('!B', segment_no)
    payload_length = 1 + len(bytes(subscriber_no, encoding='utf-8'))
    data_packet += struct.pack('!B', payload_length)
    data_packet += struct.pack('!B', technology)
    data_packet += struct.pack('!' + str(payload_length - 1) + 's', bytes(subscriber_no, encoding='utf-8'))
    data_packet += struct.pack('!H', END_PACKET_ID)
    return data_packet

def send_request(request_packet):
    client_socket.sendto(request_packet, (local_ip, local_port))
    return

def retry(signum, retry_packet):
    #retry_packet = create_permission_request(client_id, sequence, technology, subscriber_no)
    send_request(retry_packet)
    return

def response_unpack(response_packet):
    data = struct.unpack('!H B H B B B 12s H', response_packet)
    return data

def receive_packet(buffer_size):
    response, addr = client_socket.recvfrom(buffer_size)
    return response, addr

signal.signal(signal.SIGALRM, retry)
sequence = 1
retry_count = 0
while True:

    if sequence == 1:
        #paid
        packet = create_permission_request(1, sequence, G_4, '408-554-6805')
        send_request(packet)
    elif sequence == 2:
        #not paid
        packet = create_permission_request(1, sequence, G_3, '408-666-8821')
        send_request(packet)
    elif sequence == 3:
        #not exist
        packet = create_permission_request(1, sequence, G_5, '669-388-1602')
        send_request(packet)
    else:
        break
    
    try:
        response, addr = receive_packet(buffer_size)
        response_data = response_unpack(response)
        if response_data[2] == ACCESS_OK:
            print("Access permitted with sequence " + str(sequence))
        elif response_data[2] == NOT_PAID:
            print("User not paid with sequence " + str(sequence))
        elif response_data[2] == NOT_EXIST:
            print("User not exist with sequence " + str(sequence))
        else:
            print("Response format error.")
            continue
        sequence += 1

    except Exception:
        signal.alarm(0)
        if retry_count < MAX_RETRY:
            print("Server response timeout, retry...")
            retry(signal.SIGALRM, packet)
            retry_count += 1
        else:
            print("Server not respond!")
            retry_count = 0
            break
            

        
        



client_socket.close()