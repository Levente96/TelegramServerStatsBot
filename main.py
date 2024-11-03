#!/usr/bin/env python3
import requests
import time
import os
import subprocess
import systemd.daemon
import sys
import signal

# Global variables

chat_id = 0
TOKEN = "<TOKEN>"

# chat_id = 0
# TOKEN = "<TOKEN>"
get_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=5&offset="
send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text="
update_id = 0
_exit = False
FAILED_TO_START = False

# Define what to do based on systemd signals
def term_signal_handler(signal, frame):
    _exit = True
    _send("♻Rebooting Server")


# Send a mesage
def _send(message):
    _messageSent = False

    # Retry sending the message until it is successful
    while not _messageSent:
        try:
            print(f"Sending Message: {message}")
            requests.get(f"{send_url}{message}")
            _messageSent = True
        except requests.ConnectionError:
            # Failed to send the message wait 3 seconds and retry
            time.sleep(3)


# Define default commands
def help():
    _reply = "Available commands:\n"
    for key in commands.keys():
        _reply += key + "\n"
    _send(_reply)

def exit():
    global _exit
    _exit = True
    _send("📛Server Stopping")
    signal.pause()
    sys.exit(0)

def reboot():
    _send("♻Rebooting Server")
    os.system("reboot")

def ip():
    r = subprocess.check_output("hostname -I", shell=True, text=True)
    _found = False
    for ip in r.split(" "):
        if "192" in ip:
            _found = True
            _send(f"IP: {ip}")
    if not _found:
        _send(r)

def status():
    raid_status = subprocess.check_output("mdadm -D /dev/md0 | grep \"State :\"", shell=True, text=True).split(":")[1]
    _send(f"RAID: {raid_status}")

def dobackup():
    _send("💾Starting Manual Backup...")
    backup = subprocess.call('docker exec -t immich_postgres pg_dumpall --clean --if-exists --username=postgres | gzip > "/mnt/md0/backup/manual.sql.gz"', timeout=600, shell=True, text=True)
    if "0" in str(backup):
        _send("✅Backup finished!")
    else:
        _send("🚨Backup failed!")

def todo():
    _send("🚧TODO")

# Collect all commands for parsing
commands = {"/help"   : help,
            "/status" : status,
            "/backup" : dobackup,
            "/ip"     : ip,
            "/unban"  : todo,
            "/stop"   : todo,
            "/exit"   : exit,
            "/reboot" : reboot
            }


########################################
##          SERVER START              ##
########################################
print("Starting SERVER")

# Start message
_send("🚀Server Starting...")

signal.signal(signal.SIGTERM, term_signal_handler)
# Empty  incoming telegram message queue
response = requests.get(f"{get_url}{update_id}").json()
if len(response["result"]) > 0:
    # Increment update counter to discard previous messages
    update_id = int(response["result"][0]["update_id"]) + 1
print("Message queue emptyed")

# Check RAID status
raid_status = subprocess.check_output("mdadm -D /dev/md0 | grep \"State :\"", shell=True, text=True)
if "clean" not in raid_status:
    FAILED_TO_START = True
    _send("🚨Failed to start RAID!")
print("Raid status checked")

# TODO: Check IMMICH, NGNIX, VAULTWARDEN STATUS
# Check if Immich staerted on local network
immich_retry_cout = 120
immich_ok = False
while immich_retry_cout > 0:
    immich_status = subprocess.check_output("wget --server-response 192.168.0.253:2283 2>&1 | awk '/^  HTTP/{print $2}'", shell=True, text=True)
    print(f"Immich_status: {immich_status}")
    if "200" in immich_status:
        immich_ok = True
        immich_retry_cout = 0
    else:
        immich_retry_cout -= 1
if not immich_ok:
    FAILED_TO_START = True
    _send("🚨Failed to start Immich!")
print("Immich status checked")

# Server finished starting:
if not FAILED_TO_START:
    _send("✅Server Started!")
systemd.daemon.notify('READY=1')

print("Starting main loop")
# Main loop
while not _exit:
    response = requests.get(f"{get_url}{update_id}").json()
    # Check if the response actually contains any results
    if len(response["result"]) > 0:
        # Increment update counter to discard previous messages
        update_id = int(response["result"][0]["update_id"]) + 1

        # Check if its the correct chat (only accept messages from a single sender)
        if response["result"][0]["message"]["chat"]["id"] == chat_id:
            command = response["result"][0]["message"]["text"]
            # Received a command from the correct chat, lets process it
            print(f"New command: {command}")
            result = ""
            try:
                commands[command]()
            except Exception as e:
                exc = type(e).__name__
                _send(f"{exc}")
signal.pause()
