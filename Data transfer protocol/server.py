import socket
import struct
import time

local_ip = '127.0.0.1'
local_port = 6000
buffer_size = 270
#primitives
START_OF_PACKET = 0xFFFF
END_OF_PACKET = 0xFFFF
MAX_CLIENT_ID = 255
MAX_LENGTH = 255
PAYLOAD_LENGTH = 255
MAX_RETRIES = 3
MAX_TIMEOUT = 3
HEADER_LENGTH = 9
#packet type
PACKET_DATA = 0xFFF1
PACKET_ACK = 0xFFF2
PACKET_REJECT = 0xFFF3
#reject type
REJECT_OUT_OF_SEQUENCE = 0xFFF4
REJECT_LENGTH_MISMATCH = 0xFFF5
REJECT_END_OF_PACKET_MISSING = 0xFFF6
REJECT_DUPLICATE_PACKET = 0xFFF7
#track packet sequence
expected_sequence = 1
#create a socket
server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
#bind address and ip
server_socket.bind((local_ip, local_port))

#create ack packet
def create_ack_packet(client_id, received_segment_no):
    ack_packet = struct.pack('!H', START_OF_PACKET)
    ack_packet += struct.pack('!B', client_id)
    ack_packet += struct.pack('!H', PACKET_ACK)
    ack_packet += struct.pack('!B', received_segment_no)
    ack_packet += struct.pack('!H', END_OF_PACKET)
    return ack_packet

#create rej packet
def create_rej_packet(client_id, reject_sub_code, received_segment_no):
    reject_packet = struct.pack('!H', START_OF_PACKET)
    reject_packet += struct.pack('!B', client_id)
    reject_packet += struct.pack('!H', PACKET_REJECT)
    if reject_sub_code == REJECT_OUT_OF_SEQUENCE:
        reject_packet += struct.pack('!H', REJECT_OUT_OF_SEQUENCE)
    if reject_sub_code == REJECT_LENGTH_MISMATCH:
        reject_packet += struct.pack('!H', REJECT_LENGTH_MISMATCH)
    if reject_sub_code == REJECT_END_OF_PACKET_MISSING:
        reject_packet += struct.pack('!H', REJECT_END_OF_PACKET_MISSING)
    if reject_sub_code == REJECT_DUPLICATE_PACKET:
        reject_packet += struct.pack('!H', REJECT_DUPLICATE_PACKET)
    reject_packet += struct.pack('!B', received_segment_no)
    reject_packet += struct.pack('!H', END_OF_PACKET)
    return reject_packet

#receive packet
def receive_data_packet(buffer_size):
    response, addr = server_socket.recvfrom(buffer_size)
    print("The data got is: " + str(response))
    if response is None:
        data = None
        return data, addr
    data_len  = len(response) - HEADER_LENGTH
    format = '!H B H B B' + str(data_len) + 's H'
    data = struct.unpack(format, response)
    return data, addr

def send_packet(data, addr):
    server_socket.sendto(data, addr)
    print("Response send to the client: " + str(data))
    return

print("Server listening on port 6000...")

while True:
    print("expecting sequence: " + str(expected_sequence))
    received_data, addr = receive_data_packet(buffer_size)
    if received_data[0] != START_OF_PACKET or received_data[6] != END_OF_PACKET:
        #case 3, miss packet id
        reject_packet = create_rej_packet(received_data[1], REJECT_END_OF_PACKET_MISSING, received_data[3])
        send_packet(reject_packet, addr)
        print("Data got rejected becuase of case 3.\n")
        continue
    else:
        if int(received_data[3]) > expected_sequence:
            #case 1, not in sequence packet
            reject_packet = create_rej_packet(received_data[1], REJECT_OUT_OF_SEQUENCE, received_data[3])
            send_packet(reject_packet, addr)
            print("Data got rejected becuase of case 1.\n")
            continue
        elif int(received_data[3]) < expected_sequence:
            #case 4, duplicate packet
            reject_packet = create_rej_packet(received_data[1], REJECT_DUPLICATE_PACKET, received_data[3])
            send_packet(reject_packet, addr)
            print("Data got rejected becuase of case 4.\n")
            continue
        else:
            payload_length = len(received_data[5])
            if int(received_data[4]) != payload_length:
                #case 2, length field mismatch
                reject_packet = create_rej_packet(received_data[1], REJECT_LENGTH_MISMATCH, received_data[3])
                send_packet(reject_packet, addr)
                print("Data got rejected becuase of case 2.\n")
                continue
            else:
                #ack
                ack_packet = create_ack_packet(received_data[1], received_data[3])
                send_packet(ack_packet, addr)
                print("Data received correctly.\n")
                expected_sequence += 1
    

    
        


# while True:
#     data, addr = server_socket.recvfrom(buffer_size)
#     if data == bytes("exit", encoding='utf-8'):
#         server_socket.sendto(bytes("Good bye!\n", encoding='utf-8'), addr)
#         continue
#     data = b"Hello " + data + b'\n'
#     server_socket.sendto(data, addr)
    # print(str(data))
    # message = "Hello I am upd server".encode('utf-8')
    # server_socket.sendto(message, addr)
    
