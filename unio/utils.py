import socket

def linesplit(socket):
    buffer_string = socket.recv(4048)
    done = False
    while not done:
        if b'\n' in buffer_string:
            (line, buffer_string) = buffer_string.split(b"\n", 1)
            yield line
        else:
            more = socket.recv(4048)
            if not more:
                done = True
            else:
                buffer_string = buffer_string + more
    if buffer_string:
        yield buffer_string