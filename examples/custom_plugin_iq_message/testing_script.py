# /usr/bin/python3
import subprocess
import time


def start_shell(shell_string):
    subprocess.run(shell_string, shell=True, universal_newlines=True)

if __name__ == "__main__":
    #~ prefix = "xterm -e" # Separate terminal
    prefix = ""
    #~ postfix = " -d" # Debug
    postfix = ""

    sender_path = "./example/sender.py"
    sender_jid = "SENDER_JID"
    sender_password = "SENDER_PASSWORD"

    example_file = "./test_example_tag.xml"

    responder_path = "./example/responder.py"
    responder_jid = "RESPONDER_JID"
    responder_password = "RESPONDER_PASSWORD"

    SENDER_TEST = (" ".join([prefix, "python3", sender_path,
                             "-j", sender_jid, "-p", sender_password,
                             "-t", responder_jid, "--path", example_file,
                             postfix]),)

    RESPON_TEST = (" ".join([prefix, "python3", responder_path,
                             "-j", responder_jid, "-p", responder_password,
                             postfix]),)
    
    # Create two threads as follows
    try:
        start_shell(RESPON_TEST)
        time.sleep(4)
        start_shell(SENDER_TEST)
        while True:
            time.sleep(0.5)
    except:
       print ("Error: unable to start thread")

