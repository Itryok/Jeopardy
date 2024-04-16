import socket
import threading

class JClient:
    def __init__(self, name, hostname, port):
        self.name = name
        self.hostname = hostname
        self.port = port

    def run(self):
        try:
            print(f"Connecting to server on port {self.port}")
            connection_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection_sock.connect((self.hostname, self.port))

            server_output = connection_sock.makefile("wb",buffering = 0)
            

            print("Connection made.")

            # Start a thread to listen and display data sent by the server
            listener = JClientListener(connection_sock)
            listener_thread = threading.Thread(target=listener.run)
            listener_thread.start()

            server_output.write(f"{self.name}\n".encode())
            #server_output.flush()

            # Read input from the keyboard and send it to everyone else.
            # The only way to quit is to hit control-c, but a quit command
            # could easily be added.
            while True:
                data = input()
                server_output.write(f"{data}\n".encode())

        except Exception as e:
            print(f"Error: {str(e)}")

class JClientListener:
    def __init__(self, connection_sock):
        self.connection_sock = connection_sock

    def run(self):
        try:
            server_input = self.connection_sock.makefile("rb",buffering=0)
            while True:
                # Get data sent from the server
                server_text = server_input.readline().strip().decode()
                if server_text:
                    print(server_text)
                '''else:
                    # Connection was lost
                    print(f"Closing connection for socket {self.connection_sock}")
                    self.connection_sock.close()
                    break'''
        except Exception as e:
            print(f"Error: {str(e)}")

# Example usage:
# Replace "YourName" with the desired name, and execute the script.

if __name__ == "__main__":
    client_name = input("Enter your name: ")
    server_host = "127.0.1.1"
    server_port = 7654

    client = JClient(client_name, server_host, server_port)
    client.run()

