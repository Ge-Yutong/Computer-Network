import struct
import socket
import time
import pandas as pd

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
#bind address
server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
server_socket.bind((local_ip, local_port))
#read data base
database = pd.read_csv('Verification_Database.csv')

#create response packet
def create_response_packet(client_id, segment_no, technology, subscriber_no, packet_type):
    res_packet = struct.pack('!H', START_PACKET_ID)
    res_packet += struct.pack('!B', client_id)
    if packet_type == ACCESS_OK:
        res_packet += struct.pack('!H', ACCESS_OK)
    if packet_type == NOT_PAID:
        res_packet += struct.pack('!H', NOT_PAID)
    if packet_type == NOT_EXIST:
        res_packet += struct.pack('!H', NOT_EXIST)

    res_packet += struct.pack('!B', segment_no)
    payload_length = 1 + len(subscriber_no)
    res_packet += struct.pack('!B', payload_length)
    res_packet += struct.pack('!B', technology)
    res_packet += struct.pack('!12s', bytes(subscriber_no, encoding='utf-8'))
    res_packet += struct.pack('!H', END_PACKET_ID)
    return res_packet

def send_packet(res_packet, addr):
    server_socket.sendto(res_packet, addr)
    print("Response to the client: " + str(res_packet) + '\n')
    return

def receive_packet(buffer_size):
    response, addr = server_socket.recvfrom(buffer_size)
    print("The data got is: " + str(response))
    if response is None:
        data = None
    else:
        format = '!H B H B B B 12s H'
        data = struct.unpack(format, response)
        return data, addr

print("Server listening on port " + str(local_port) + "...")
send_flag = False
while True:
    
    received_data, addr = receive_packet(buffer_size)
    send_flag = False
    if received_data[6].decode('utf-8') in database['Subscriber Number'].values:
        index = database['Subscriber Number'].to_list().index(received_data[6].decode('utf-8'))
        if database['Paid'][index] == 1:
            #Paid
            print("This user has paid and has access.")
            response = create_response_packet(received_data[1], received_data[3], received_data[5], received_data[6].decode('utf-8'), ACCESS_OK)
            send_packet(response, addr)
        else:
            #Unpaid
            print("This user has not paid and has no access.")
            response = create_response_packet(received_data[1], received_data[3], received_data[5], received_data[6].decode('utf-8'), NOT_PAID)
            send_packet(response, addr)
    else:
        #user not exist
        print("This user does not exist.")
        response = create_response_packet(received_data[1], received_data[3], received_data[5], received_data[6].decode('utf-8'), NOT_EXIST)
        send_packet(response, addr)







