import socket
import json


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False

    def send_request(self, request):
        try:
            request_json = json.dumps(request)
            self.socket.sendall(request_json.encode())
            return True
        except Exception as e:
            print(f"Error sending request: {e}")
            return False

    def receive_response(self):
        try:
            response_json = self.socket.recv(4096).decode()
            response = json.loads(response_json)
            return response
        except Exception as e:
            print(f"Error receiving response: {e}")
            return None

    def close(self):
        try:
            self.socket.close()
        except Exception as e:
            print(f"Error closing connection: {e}")


if __name__ == "__main__":
    client = Client("localhost", 8000)
    if client.connect():
        request = {"query": "hello"}
        if client.send_request(request):
            response = client.receive_response()
            print(f"Response: {response}")
        client.close()
    else:
        print("Could not connect to the server.")
