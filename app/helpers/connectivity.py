import socket
import time


def database_ready(host, port):
    # check database is ready for use.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        try:
            connection.connect((host, int(port)))
            connection.shutdown(socket.SHUT_RDWR)
            return True
        except Exception as e:
            print(str(e))
            return False


def is_database_ready(host, port, retry):
    is_up = False
    for _ in range(retry):
        if database_ready(host, port):
            is_up = True
            break
        else:
            time.sleep(30)
    return is_up
