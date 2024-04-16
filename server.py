import socket
import threading
import select

class JServer:
    def __init__(self):
        self.socket_list = []

    def get_connection(self):
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.bind(('127.0.1.1', 7654))
            server_sock.listen()  # Allow up to 3 clients to connect
            print("Waiting for client connections on port 7654.")

            while True:
                connection_sock, addr = server_sock.accept()
                self.socket_list.append(connection_sock)
                handler = JClientHandler(connection_sock, self.socket_list)
                the_thread = threading.Thread(target=handler.run)
                the_thread.start()

        except Exception as e:
            print(str(e))

class JClientHandler:
    round = 0
    scores = [0, 0, 0]
    player_names = {}
    client_num = 0
    state = 0
    first_buzz_client_answered = False
    buzz_in = []
    client_to_answer = 0
    was_correct = False
    one = ""
    two = ""
    three = ""
    indiv_dict = {}
    winner_name = ""

    def __init__(self, sock, socket_list):
        self.connection_sock = sock
        self.socket_list = socket_list
        self.individual_client_num = {}
        self.current_question = 0
        self.questions_array = []

        try:
            with open("JeopardyQuestions.txt", "r") as file:
                for line in file:
                    self.questions_array.append(line.strip().split(','))
        except FileNotFoundError:
            pass

    def run(self):
        
        print(f"Connection made with socket {self.connection_sock}")
        client_input = self.connection_sock.makefile("rb",buffering=0)
        client_output = self.connection_sock.makefile("wb",buffering=0)
        connected = False

        name = ""
        buzz_in_str = ""

        while self.current_question != 2:

            JClientHandler.round = self.current_question + 1

            if self.state == 0:
                if not connected:
                    JClientHandler.client_num += 1
                    name = client_input.readline().strip().decode()
                    print(f"{name} Subscribed!!")
                    JClientHandler.player_names[self.connection_sock] = [name,JClientHandler.client_num]
                    client_output.write(f"name: {name}\n".encode())
                    client_output.write(f"You are contestant number: {JClientHandler.client_num}\n".encode())
                    self.individual_client_num[self.connection_sock] = JClientHandler.client_num
                    JClientHandler.indiv_dict.update(self.individual_client_num)
                    connected = True

                    if self.individual_client_num[self.connection_sock] == 1:
                        JClientHandler.one = name
                    elif self.individual_client_num[self.connection_sock] == 2:
                        JClientHandler.two = name
                    elif self.individual_client_num[self.connection_sock] == 3:
                        JClientHandler.three = name
                        
                        self.state = 1

            elif self.state == 1: #asking each client question
                for sock in self.socket_list:
                    out = sock.makefile("wb",buffering=0)
                    out.write(f"QUESTION: {self.questions_array[self.current_question][0]}\n".encode())
                    out.write("Enter 'b' to buzz in.\n".encode())
                    JClientHandler.was_correct = False
                self.state = 2

            elif self.state == 2: #Waiting for buzz from each client i.e. each client has to buzz
                readable, _, _ = select.select(self.socket_list, [], [], 0)  # Non-blocking check for readable sockets
                for sock in readable:
                    clin = sock.makefile("rb", buffering=0)
                    buzz_in_str = clin.readline().strip().decode()
                    if buzz_in_str == "b":
                        JClientHandler.buzz_in.append(sock)
                        print(f"{JClientHandler.player_names[sock][0]} buzzed in")  
                if JClientHandler.buzz_in and len(JClientHandler.buzz_in)==3 :  # moving on to the game
                    self.state = 3
                        

            elif self.state == 3:
                if JClientHandler.buzz_in[JClientHandler.client_to_answer]:
                    clou = JClientHandler.buzz_in[JClientHandler.client_to_answer].makefile("wb", buffering = 0)
                    if JClientHandler.client_to_answer == 0 :
                        clou.write("You were the first to buzz in\n".encode())
                        clou.write("Submit your answer\n".encode())
                    else:
                        clou.write("You were the next to buzz in\n".encode())
                        clou.write("Submit your answer\n".encode())

                    for s in self.socket_list:
                        if s != JClientHandler.buzz_in[JClientHandler.client_to_answer]:
                            s_output = s.makefile("wb",buffering = 0)
                            if JClientHandler.client_to_answer == 0 :
                                s_output.write(f"{JClientHandler.player_names[JClientHandler.buzz_in[JClientHandler.client_to_answer]][0]} was the first to buzz in!\n".encode())
                            else:
                                s_output.write(f"{JClientHandler.player_names[JClientHandler.buzz_in[JClientHandler.client_to_answer]][0]} was the next to buzz in!\n".encode())

                    self.state = 4

                else:
                    self.state = 5  

            elif self.state == 4: #Checking question from client who buzzed in

                answer = JClientHandler.buzz_in[JClientHandler.client_to_answer].makefile("rb",buffering=0)
                question = answer.readline().strip().decode()

                if question:
                    print(f"{JClientHandler.player_names[JClientHandler.buzz_in[JClientHandler.client_to_answer]][0]}: {question}")

                    for s in self.socket_list:
                        if s != JClientHandler.buzz_in[JClientHandler.client_to_answer]:
                            s_output = s.makefile("wb",buffering=0)
                            s_output.write(f"{JClientHandler.player_names[JClientHandler.buzz_in[JClientHandler.client_to_answer]][0]} answered: {question}\n".encode())

                if question.lower() == self.questions_array[self.current_question][1].lower():
                    print("That is correct\n")
                    for s in self.socket_list:
                        s_output = s.makefile("wb",buffering=0)
                        s_output.write("That is correct\n".encode())
                    
                    index = JClientHandler.buzz_in[JClientHandler.client_to_answer]
                    current = JClientHandler.scores[JClientHandler.indiv_dict[index] - 1]
                    JClientHandler.scores[JClientHandler.indiv_dict[index] - 1] = current + 10

                    JClientHandler.round += 1

                    print(f"\n******** ROUND SCORES ********\n")
                    print(f"{JClientHandler.one}: {JClientHandler.scores[0]}")
                    print(f"{JClientHandler.two}: {JClientHandler.scores[1]}")
                    print(f"{JClientHandler.three}: {JClientHandler.scores[2]}\n\n")

                    for s in self.socket_list:
                        s_output = s.makefile("wb",buffering=0)
                        s_output.write(f"\n******** ROUND SCORES ********\n".encode())
                        s_output.write(f"{JClientHandler.one}: {JClientHandler.scores[0]}\n".encode())
                        s_output.write(f"{JClientHandler.two}: {JClientHandler.scores[1]}\n".encode())
                        s_output.write(f"{JClientHandler.three}: {JClientHandler.scores[2]}\n\n\n".encode())

                    self.state = 5
                    JClientHandler.was_correct = True

                else:
                    print("\nThat is incorrect")
                    index = JClientHandler.buzz_in[JClientHandler.client_to_answer]
                    current = JClientHandler.scores[JClientHandler.indiv_dict[index] - 1]
                    JClientHandler.scores[JClientHandler.indiv_dict[index] - 1] = current + 10


                    for s in self.socket_list:
                        s_output = s.makefile("wb",buffering=0)
                        s_output.write("\nThat is incorrect\n".encode())

                    JClientHandler.client_to_answer += 1
                    JClientHandler.first_buzz_client_answered = True
                    self.state = 5

                    if JClientHandler.client_to_answer == 3:
                        for s in self.socket_list:
                            s_output = s.makefile("wb",buffering=0)
                            s_output.write(f"\nThe correct answer is: {self.questions_array[self.current_question][1]}\n".encode())
                        self.state = 1
                        self.current_question += 1
                        JClientHandler.client_to_answer = 0
                        JClientHandler.buzz_in.clear()
                        print(f"\n******** ROUND SCORES ********" + "\n")
                        print(f"{JClientHandler.one}: {JClientHandler.scores[0]}")
                        print(f"{JClientHandler.two}: {JClientHandler.scores[1]}")
                        print(f"{JClientHandler.three}: {JClientHandler.scores[2]}\n\n\n")

                        for s in self.socket_list:
                            s_output = s.makefile("wb",buffering=0)
                            s_output.write(f"\n******** ROUND SCORES ********\n".encode())
                            s_output.write(f"{JClientHandler.one}: {JClientHandler.scores[0]}\n".encode())
                            s_output.write(f"{JClientHandler.two}: {JClientHandler.scores[1]}\n".encode())
                            s_output.write(f"{JClientHandler.three}: {JClientHandler.scores[2]}\n\n\n".encode())
                        

            elif self.state == 5:
                if JClientHandler.was_correct:
                    self.state = 1
                    JClientHandler.buzz_in = []
                    JClientHandler.client_to_answer = 0
                    self.current_question += 1
                    
                else:
                    if JClientHandler.first_buzz_client_answered:
                        if JClientHandler.client_to_answer == 3:
                            JClientHandler.buzz_in.clear()
                            self.state = 1
                            JClientHandler.client_to_answer = 0
                        else:
                            self.state = 3
                            JClientHandler.first_buzz_client_answered = False

        temp_list = JClientHandler.scores
        max_score = max(JClientHandler.scores)
        index = temp_list.index(max_score)
        
        for value in JClientHandler.player_names:
            if int(JClientHandler.player_names[value][1]) == max_score:
                JClientHandler.winner_name  = JClientHandler.player_names[value][0]
                
        for sock in self.socket_list:
            s = sock.makefile("wb",buffering=0)
            s.write(f"{JClientHandler.winner_name} is the winner!!!!".encode())
            s.write(f"Game over!!!!".encode())
    
        print(f"Game over!!\n")
        
        

        '''except Exception as e:
            print(f"Error: {str(e)}")
            self.socket_list.remove(self.connection_sock)
            self.connection_sock.close()'''



def main():
    server = JServer()
    server.get_connection()

if __name__ == "__main__":
    main()


