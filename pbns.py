#!/usr/bin/env python
"""
A notification handler for Pushbullet that sends pushes via dbus.
"""

import argparse
import functools
import json
import logging
import os
import socket
import sys
import time

import dbus
import pushbullet
import requests.exceptions

HTTP_PROXY_HOST = None
HTTP_PROXY_PORT = None

CONFIG_BASEDIR = os.path.join(os.path.expanduser("~"), ".config", "pbns")
API_KEY_PATH = os.path.join(CONFIG_BASEDIR, "apikey")
PASSWORD_PATH = os.path.join(CONFIG_BASEDIR, "password")

ICON = os.path.join(os.path.abspath(sys.path[0]), "resources", "pb_logo.png")


def wait_for_internet():
    """
    Loop until an internet connection to pushbullet.com port 80 is
    available.
    """

    while True:
        try:
            logging.debug("Trying connection to Pushbullet API.")
            socket.create_connection(('api.pushbullet.com', '80'), timeout=30)
            logging.debug("Connection successful.")
            break

        except (socket.gaierror, socket.timeout, ConnectionRefusedError):
            logging.debug("Connection failed. Retrying in 10 seconds")
            time.sleep(10)


def get_encryption_password(passwd_path):
    """
    Return the encryption password
    """

    try:
        with open(passwd_path) as passwd_file:
            password = passwd_file.read()
            password = password.strip()

        return password

    except FileNotFoundError:
        no_crypto_warn = ("Can't use encryption due to inexistent password. "
                          "If you wish to use encryption, place your "
                          "encryption password into %s")
        logging.warning(no_crypto_warn, passwd_path)


def get_api_key(api_key_path):
    """
    Return the API key from config file
    """

    try:
        with open(api_key_path) as api_key:
            api_key = api_key.read()
            api_key = api_key.strip()

        return api_key

    except FileNotFoundError:
        err_msg = ("Couldn't load your access token. Create one at "
                   "'https://www.pushbullet.com/#settings/account' "
                   "and paste it into '{}'.")

        err_msg = err_msg.format(API_KEY_PATH)
        logging.error(err_msg)
        sys.exit(1)


def notify(title, body):
    logging.debug("Sending notification via D-Bus")

    interface = "org.freedesktop.Notifications"
    item = "org.freedesktop.Notifications"
    path = "/org/freedesktop/Notifications"

    bus = dbus.SessionBus()
    proxy = bus.get_object(item, path)
    notifications = dbus.Interface(proxy, interface)

    title = title.strip()
    body = body.strip()

    notifications.Notify("Pushbullet", 0, ICON, title, body, "", "", 5000)


def handle_mirror(push):
    """
    Returns two strings:
        1. title in the format '[appname] push title'
        2. push body
    """

    title = "[{}] {}"
    title = title.format(push["application_name"], push["title"])

    return title, push["body"]


def handle_push(push):
    """
    Returns two strings: the title and the body
    """

    if "title" not in push.keys():
        if "sender_name" in push.keys():
            title = push["sender_name"]
        else:
            title = ""
    else:
        title = push["title"]

    return title, push["body"]


def check_if_dismissed(push):
    """
    Returns True if `push` is dismissed
    """

    return "dismissed" in push.keys() and push["dismissed"]


def on_push(account, push):
    """
    Handle last push
    """

    title, body = None, None

    logging.debug("Got push: %s", push)

    if push["type"] == "tickle":
        # Overwrite push with latest push
        push = account.get_pushes()[0]

        logging.debug("Last push: %s", push)
        title, body = handle_push(push)

    elif push["type"] == "push":
        push = push["push"]

        logging.debug("Push contents: %s", push)
        if push["encrypted"]:
            decrypted = account._decrypt_data(push["ciphertext"])
            push = json.loads(decrypted)
            logging.debug("Decrypted contents: %s", push)

        if push["type"] == "mirror":
            title, body = handle_mirror(push)

    if title and body and not check_if_dismissed(push):
        notify(title, body)


def on_error(_, exception):
    """
    Handle errors during listener.run_forever().
    """

    raise exception


def connect(api_key, password):
    """
    Return the account and the listener object we'll use to fetch pushes,
    etc. We'll pass it to the `on_push` handler afterwards.
    """

    pb_account = pushbullet.Pushbullet(api_key, encryption_password=password)

    listener = pushbullet.Listener(account=pb_account,
                                   on_push=functools.partial(on_push, pb_account),
                                   on_error=on_error,
                                   http_proxy_host=HTTP_PROXY_HOST,
                                   http_proxy_port=HTTP_PROXY_PORT)

    return listener


def main():
    """
    Initialize app and listen for new pushes
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Output debugging information",
                        action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    logging.basicConfig(format="%(asctime)s [%(levelname)5s] %(message)s")

    api_key = get_api_key(API_KEY_PATH)
    password = get_encryption_password(PASSWORD_PATH)

    wait_for_internet()

    listener = connect(api_key, password)

    try:
        while True:
            listener.run_forever()
            wait_for_internet()

    except KeyboardInterrupt:
        logging.debug("Keyboard interrupt. Cleaning up.")
        listener.close()
        sys.exit()


if __name__ == "__main__":
    main()
