# PBNS: Pushbullet Notifications via D-BUS

PBNS is an application that uses the `pushbullet.py` module by @randomchars to
integrate [Pushbullet](https://www.pushbullet.com) notifications and pushes
into your desktop. It forwards both mirrored notifications and regular text
pushes (such as from chat messages) to D-Bus so that they show up via your
regular notifications daemon.

Click the following screenshot to view a video of PBNS in action.

![screencast](https://github.com/kiike/pbns/blob/readme-assets/readme-assets/demo.gif?raw=true)

# Features

* Mirrors your devices' notifications to your desktop
* Displays your pushes as soon as they're received
* Decryption of your End-to-End-encrypted pushes and notifications


# Why

The motivation behind the development of this app was to experiment with the
Pushbullet API, so I could integrate the notifications with my desktop.


# How to run

1. `pip install requirements.txt`
2. `git clone htts://github.com/kiike/pbns`
3. source `$YOUR_VIRTUALENV/bin/activate`
4. `python $CLONE_DIR/pbns.py`

# License and contributions

The Pushbullet.com logo under `resources` directory is property of Pushbullet,
Inc. This project is in no way endorsed nor affiliated with Pushbullet.

This project's code is licensed under the ISC license. For details, see the
`LICENSE` file.

I welcome contributions and suggestions very much. Please file bugs and (pull)
requests!
