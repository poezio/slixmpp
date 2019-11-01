# /usr/bin/python3
import subprocess
import threading
import time

def start_shell(shell_string):
    subprocess.run(shell_string, shell=True, universal_newlines=True)

if __name__ == "__main__":
    #~ prefix = "x-terminal-emulator -e" # Separate terminal for every client, you can replace xterm with your terminal
    #~ prefix = "xterm -e" # Separate terminal for every client, you can replace xterm with your terminal
    prefix = ""
    #~ postfix = " -d" # Debug
    #~ postfix = " -q" # Quiet
    postfix = ""

    sender_path = "./example/sender.py"
    sender_jid = "SENDER_JID"
    sender_password = "SENDER_PASSWORD"

    example_file = "./test_example_tag.xml"

    responder_path = "./example/responder.py"
    responder_jid = "RESPONDER_JID"
    responder_password = "RESPONDER_PASSWORD"

    # Remember about rights to run your python files. (`chmod +x ./file.py`)
    SENDER_TEST = f"{prefix} {sender_path} -j {sender_jid} -p {sender_password}" + \
                   " -t {responder_jid} --path {example_file} {postfix}"

    RESPON_TEST = f"{prefix} {responder_path} -j {responder_jid}" + \
                   " -p {responder_password} {postfix}"
    
    try:
        responder = threading.Thread(target=start_shell, args=(RESPON_TEST, ))
        sender = threading.Thread(target=start_shell, args=(SENDER_TEST, ))
        responder.start()
        sender.start()
        while True:
            time.sleep(0.5)
    except:
       print ("Error: unable to start thread")

