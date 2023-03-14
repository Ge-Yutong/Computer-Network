import socket
import struct
import time
import signal
from socket import timeout
#address
local_ip = '127.0.0.1'
local_port = 6000
buffersize = 270
#primitives
START_OF_PACKET = 0xFFFF
END_OF_PACKET = 0xFFFF
MAX_CLIENT_ID = 255
MAX_LENGTH = 255
MAX_RETRIES = 3
MAX_TIMEOUT = 3
ACK_LENGTH = 8
REJ_LENGTH = 10
#packet type
PACKET_DATA = 0xFFF1
PACKET_ACK = 0xFFF2
PACKET_REJECT = 0xFFF3
#reject type
REJECT_OUT_OF_SEQUENCE = 0xFFF4
REJECT_LENGTH_MISMATCH = 0xFFF5
REJECT_END_OF_PACKEY_MISSING = 0xFFF6
REJECT_DUPLICATE_PACKET = 0xFFF7
#create client socket
client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
#set timeout
client_socket.settimeout(MAX_TIMEOUT)

#create data packet 
def create_data_packet(client_id, segment_no, payload):
    data_packet = struct.pack('!H', START_OF_PACKET)
    data_packet += struct.pack('!B', client_id)
    data_packet += struct.pack('!H', PACKET_DATA)
    data_packet += struct.pack('!B', segment_no)
    data_packet += struct.pack('!B', len(payload.encode('utf-8')))
    data_packet += struct.pack('!' + str(len(payload.encode('utf-8'))) + 's', bytes(payload, encoding='utf-8'))
    data_packet += struct.pack('!H', END_OF_PACKET)
    return data_packet

#send packet
def send_packet(client_id, segment_no, payload):
    data = create_data_packet(client_id, segment_no, payload)
    client_socket.sendto(data, (local_ip, local_port))
    print("Send 'This is data " + str(segment_no) + "' to the sever, sequence " + str(sequence))
    return

#send length field not match, payload length is 1 less than actual length
def send_length_field_not_match(client_id, segment_no, payload):
    data = struct.pack('!H', START_OF_PACKET)
    data += struct.pack('!B', client_id)
    data += struct.pack('!H', PACKET_DATA)
    data += struct.pack('!B', segment_no)
    data += struct.pack('!B', len(payload.encode('utf-8')) - 10)
    data += struct.pack('!' + str(len(payload.encode('utf-8'))) + 's', bytes(payload, encoding='utf-8'))
    data += struct.pack('!H', END_OF_PACKET)
    client_socket.sendto(data, (local_ip, local_port))
    print("Send 'This is data " + str(segment_no) + "' to the sever, sequence " + str(sequence))
    return

#send data with no packet id
def send_no_end_packet_id(client_id, segment_no, payload):
    data = struct.pack('!H', START_OF_PACKET)
    data += struct.pack('!B', client_id)
    data += struct.pack('!H', PACKET_DATA)
    data += struct.pack('!B', segment_no)
    data += struct.pack('!B', len(payload.encode('utf-8')))
    data += struct.pack('!' + str(len(payload.encode('utf-8'))) + 's', bytes(payload, encoding='utf-8'))
    #miss end of packet id
    client_socket.sendto(data, (local_ip, local_port))
    print("Send 'This is data " + str(segment_no) + "' to the sever, sequence " + str(sequence))
    return

def receive_response(buffersize):
    response, addr = client_socket.recvfrom(buffersize)
    if len(response) == ACK_LENGTH:
        #ACK
        data = struct.unpack('!H B H B H', response)
    elif len(response) == REJ_LENGTH:
        #REJ
        data = struct.unpack('!H B H H B H', response)
    elif len(response) == 0:
        data = None
    else:
        print("Response format error, length: " + str(len(response)))
        data = None
    return data, addr

#retry
def retry(signum, sequence):
    if sequence <= 6:
        send_packet(1, sequence, "This is data " + str(sequence) + '. ')
    if sequence == 7:
        send_packet(1, sequence - 1, "This is data " + str(sequence - 1) + '. ')
    if sequence == 8:
        send_packet(1, sequence, "This is data " + str(sequence) + '. ')
    if sequence == 9:
        send_length_field_not_match(1, sequence - 2, "This is data " + str(sequence - 2) + '. ')
    if sequence == 10:
        send_no_end_packet_id(1, sequence - 3, "This is data " + str(sequence - 3) + '. ')
    
sequence = 1
response = None
addr = None
retry_counts = 0
retry_flag = False
while True:
    if not retry_flag:
        if sequence <= 6:
            send_packet(1, sequence, "This is data " + str(sequence) + '. ')
        elif sequence == 7:
            #duplicate packet
            send_packet(1, sequence - 1 , "This is data " + str(sequence - 1) + '. ')
        elif sequence == 8:
            #not in sequence packet
            send_packet(1, sequence, "This is data " + str(sequence - 1) + '. ')
        elif sequence == 9:
            #length field not match packet
            send_length_field_not_match(1, sequence - 2, "This is data " + str(sequence - 2) + '. ')
        elif sequence == 10:
            #no end packet id packet
            send_no_end_packet_id(1, sequence - 2, "This is data " + str(sequence - 2) + '. ')
        else:
            break
    
    try:
        response, addr = receive_response(buffersize)
        print("Response from the server is:" + str(response))
        if response[2] == PACKET_REJECT:
            #packet rejected
            segment_no = response[4]
            reject_case = response[3]
            if reject_case == REJECT_OUT_OF_SEQUENCE:
                print("Packet " + str(sequence) + " got rejected because of case Not in Sequence.\n")
            elif reject_case == REJECT_LENGTH_MISMATCH:
                print("Packet " + str(sequence) + " got rejected because of case Length Field Mismatch.\n")
            elif reject_case == REJECT_END_OF_PACKEY_MISSING:
                print("Packet " + str(sequence) + " got rejected because of case No End Pakcet ID.\n")
            elif reject_case == REJECT_DUPLICATE_PACKET:
                print("Packet " + str(sequence) + " got rejected because of case Duplicate Packet.\n")
            else:
                print("Reject case number error.\n")
                continue
        elif response[2] == PACKET_ACK:
            #packet acknowledged
            segment_no = response[3]
            print("Packet " + str(sequence) + " got received successfully\n")
        else:
            print("Reply packet format error!\n")
            continue

        sequence += 1
    #no response exception        
    except Exception:
        signal.alarm(0)
        if retry_counts < MAX_RETRIES:
            print("Server response timeout, retry...")
            retry(signal.SIGALRM, sequence)
            retry_counts += 1
            retry_flag = True
        else:
            print("Server not respond!")
            retry_counts = 0
            break
            

    

# while True:
#     data = input("Please input name: ")
#     if not data:
#         continue
#     client_socket.sendto(data.encode('utf-8'), (local_ip, local_port))
#     response, addr = client_socket.recvfrom(buffersize)
#     print(response.decode())
#     if data == "exit":
#         print("Session over from the sever %s:%s\n" %addr)
#         break

client_socket.close()


