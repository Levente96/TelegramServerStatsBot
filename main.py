#!/usr/bin/env python3
import requests
import time
import os
import subprocess

# Global variables
chat_id = 0
TOKEN = "<TOKEN>"
get_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset="
send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text="
update_id = 0
_exit = False


# Send a mesage
def _send(message):
    requests.get(f"{send_url}{message}")


# Define default commands
def help():
    for key in commands.keys():
        _send(key)

def exit():
    global _exit
    _exit = True
    _send("Bye")

def reboot():
    _send("Rebooting...")
    os.system("reboot")

def ip():
    _send(subprocess.check_output("hostname -I", shell=True, text=True))

def free():
    _send(subprocess.check_output("df -h", shell=True, text=True))
    _send(subprocess.check_output("free", shell=True, text=True))


# Collect all commands for parsing
commands = {"/help"   : help,
            "/exit"   : exit,
            "/reboot" : reboot,
            "/ip"     : ip,
            "/free"   : free}

# Start message
_send("✅Server Started!✅")

# Empty message queue
response = requests.get(f"{get_url}{update_id}").json()
if len(response["result"]) > 0:
    # Increment update counter to discard previous messages
    update_id = int(response["result"][0]["update_id"]) + 1


# Main loop
while not _exit:
    time.sleep(3)
    response = requests.get(f"{get_url}{update_id}").json()
    # Check if the response actually contains any results
    if len(response["result"]) > 0:
        # Increment update counter to discard previous messages
        update_id = int(response["result"][0]["update_id"]) + 1
        print(response["result"][0])

        # Check if its the correct chat (only accept messages from a single sender)
        if response["result"][0]["message"]["chat"]["id"] == chat_id:
            command = response["result"][0]["message"]["text"]
            # Received a command from the correct chat, lets process it
            print(f"Command: {command}")
            result = ""
            try:
                commands[command]()
            except:
                requests.get(f"{send_url}Not a command")
