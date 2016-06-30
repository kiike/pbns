#!/usr/bin/env python
"""
A notification handler for Pushbullet that sends pushes via dbus.
"""

import argparse
from functools import partial
import json
import logging
import os
import sys

import dbus
import pushbullet

HTTP_PROXY_HOST = None
HTTP_PROXY_PORT = None

CONFIG_BASEDIR = os.path.join(os.path.expanduser("~"), ".config", "pbns")
API_KEY_PATH = os.path.join(CONFIG_BASEDIR, "apikey")
PASSWORD_PATH = os.path.join(CONFIG_BASEDIR, "password")

ICON = os.path.join(os.path.abspath(sys.path[0]), "resources", "pb_logo.png")


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

    return push["title"], push["body"]


def check_if_dismissed(push):
    """
    Returns True if `push` is dismissed
    """

    return "dismissed" in push.keys() and push["dismissed"]


def on_push(push, account):
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

    account = pushbullet.Pushbullet(api_key, encryption_password=password)

    listener = pushbullet.Listener(account=account,
                                   on_push=partial(on_push, account),
                                   http_proxy_host=HTTP_PROXY_HOST,
                                   http_proxy_port=HTTP_PROXY_PORT)
    try:
        listener.run_forever()
    except KeyboardInterrupt:
        listener.close()


if __name__ == "__main__":
    main()
