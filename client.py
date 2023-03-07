import socket
import struct
import time
#address
local_ip = '127.0.0.1'
local_port = 6000
buffersize = 270
#primitives
START_OF_PACKET = 'FFFF'
END_OF_PACKET = 'FFFF'
MAX_CLIENT_ID = 255
MAX_LENGTH = 255
MAX_RETRIES = 3
MAX_TIMEOUT = 3
ACK_LENGTH = 14
REJ_LENGTH = 18
#packet type
PACKET_DATA = 'FFF1'
PACKET_ACK = 'FFF2'
PACKET_REJECT = 'FFF3'
#reject type
REJECT_OUT_OF_SEQUENCE = 'FFF4'
REJECT_LENGTH_MISMATCH = 'FFF5'
REJECT_END_OF_PACKEY_MISSING = 'FFF6'
REJECT_DUPLICATE_PACKET = 'FFF7'
#create client socket
client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

#create data packet 
def create_data_packet(client_id, segment_no, payload):
    data_packet = struct.pack('!4s', bytes(START_OF_PACKET, encoding='utf-8'))
    data_packet += struct.pack('!B', client_id)
    data_packet += struct.pack('!4s', bytes(PACKET_DATA, encoding='utf-8'))
    data_packet += struct.pack('!B', segment_no)
    data_packet += struct.pack('!B', len(payload.encode('utf-8')))
    data_packet += struct.pack('!' + str(len(payload.encode('utf-8'))) + 's', bytes(payload, encoding='utf-8'))
    data_packet += struct.pack('!4s', bytes(END_OF_PACKET, encoding='utf-8'))
    return data_packet

#send packet
def send_packet(client_id, segment_no, payload):
    data = create_data_packet(client_id, segment_no, payload)
    client_socket.sendto(data, (local_ip, local_port))
    print("Send 'This is data " + str(segment_no) + "' to the sever, sequence " + str(sequence))
    return

#send length field not match, payload length is 1 less than actual length
def send_length_field_not_match(client_id, segment_no, payload):
    data = struct.pack('!4s', bytes(START_OF_PACKET, encoding='utf-8'))
    data += struct.pack('!B', client_id)
    data += struct.pack('!4s', bytes(PACKET_DATA, encoding='utf-8'))
    data += struct.pack('!B', segment_no)
    data += struct.pack('!B', len(payload.encode('utf-8')) - 10)
    data += struct.pack('!' + str(len(payload.encode('utf-8'))) + 's', bytes(payload, encoding='utf-8'))
    data += struct.pack('!4s', bytes(END_OF_PACKET, encoding='utf-8'))
    client_socket.sendto(data, (local_ip, local_port))
    return

#send data with no packet id
def send_no_end_packet_id(client_id, segment_no, payload):
    data = struct.pack('!4s', bytes(START_OF_PACKET, encoding='utf-8'))
    data += struct.pack('!B', client_id)
    data += struct.pack('!4s', bytes(PACKET_DATA, encoding='utf-8'))
    data += struct.pack('!B', segment_no)
    data += struct.pack('!B', len(payload.encode('utf-8')))
    data += struct.pack('!' + str(len(payload.encode('utf-8'))) + 's', bytes(payload, encoding='utf-8'))
    data += struct.pack('!p', bytes(payload, encoding='utf-8'))
    #miss end of packet id
    client_socket.sendto(data, (local_ip, local_port))
    return

def receive_response(buffersize):
    response, addr = client_socket.recvfrom(buffersize)
    if len(response) == ACK_LENGTH:
        #ACK
        data = struct.unpack('!4s B 4s B 4s', response)
    elif len(response) == REJ_LENGTH:
        #REJ
        data = struct.unpack('!4s B 4s 4s B 4s', response)
    elif len(response) == 0:
        data = None
    else:
        print("Response format error, length: " + str(len(response)))
        data = None
    return data, addr

#retry
def retry(sequence):
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
while True:

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

    response, addr = receive_response(buffersize)
    print("Response from the server is:" + str(response))

    start_time = time.time()
    retry_counts = 0
    #retry
    while True:
        if response is None:
            end_time = time.time()
            if end_time - start_time < MAX_TIMEOUT:
                continue
            else:
                if retry_counts > MAX_RETRIES:
                    print("Server does not respond")
                    break
                else:
                    retry(sequence)
                    response, addr = receive_response(buffersize)
                    retry_counts += 1
                    continue
        else:
            sequence += 1
            break
    
    if response[2] == bytes(PACKET_REJECT, encoding='utf-8'):
        #packet rejected
        segment_no = response[4]
        reject_case = response[3].decode('utf-8')
        if reject_case == REJECT_OUT_OF_SEQUENCE:
            print("Packet " + str(segment_no) + " got rejected because of case Not in Sequence.")
        elif reject_case == REJECT_LENGTH_MISMATCH:
            print("Packet " + str(segment_no) + " got rejected because of case Length Field Mismatch.")
        elif reject_case == REJECT_END_OF_PACKEY_MISSING:
            print("Packet " + str(segment_no) + " got rejected because of case No End Pakcet ID.")
        elif reject_case == REJECT_DUPLICATE_PACKET:
            print("Packet " + str(segment_no) + " got rejected because of case Duplicate Packet.")
        else:
            print("Reject case number error.")
        continue
    elif response[2] == bytes(PACKET_ACK, encoding='utf-8'):
        #packet got ack
        segment_no = response[3]
        print("Packet " + str(segment_no) + " got received successfully")
        continue
    else:
        print("Reply packet format error!\n")



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


