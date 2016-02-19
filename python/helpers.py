"""
Copyright 2016 Andriy Drozdyuk

This file is part of zmq-soundtouch.

zmq-soundtouch is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

zmq-soundtouch is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with zmq-soundtouch.  If not, see <http://www.gnu.org/licenses/>.
"""

import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
from contextlib import contextmanager
import os
import logging
import sys

@contextmanager
def secure_server_creator():
    # These directories are generated by the generate_certificates script
    base_dir = os.path.dirname(__file__)
    public_keys_dir = os.path.join(base_dir, 'public_keys')
    secret_keys_dir = os.path.join(base_dir, 'private_keys')

    if not (os.path.exists(public_keys_dir) and
            os.path.exists(secret_keys_dir)):
        logging.critical("Certificates are missing - run generate_certificates.py script first")
        sys.exit(1)

    ctx = zmq.Context.instance()

    # Start an authenticator for this context.
    auth = ThreadAuthenticator(ctx)
    auth.start()
    #auth.allow('127.0.0.1','99.241.90.9')
    # Tell authenticator to use the certificate in a directory
    auth.configure_curve(domain='*', location=public_keys_dir)

    def creator(zmq_sock_type):
        server = ctx.socket(zmq_sock_type)


        server_secret_file = os.path.join(secret_keys_dir, "server.key_secret")
        server_public, server_secret = zmq.auth.load_certificate(server_secret_file)
        server.curve_secretkey = server_secret
        server.curve_publickey = server_public
        server.curve_server = True  # must come before bind
        return server
    
    yield creator
    
    # stop auth thread
    auth.stop()
    

@contextmanager
def secure_client(zmq_sock_type):
    # These directories are generated by the generate_certificates script
    base_dir = os.path.dirname(__file__)
    public_keys_dir = os.path.join(base_dir, 'public_keys')
    secret_keys_dir = os.path.join(base_dir, 'private_keys')

    if not (os.path.exists(public_keys_dir) and
            os.path.exists(secret_keys_dir)):
        logging.critical("Certificates are missing - run generate_certificates.py script first")
        sys.exit(1)

    ctx = zmq.Context.instance()

    # Start an authenticator for this context.
    auth = ThreadAuthenticator(ctx)
    auth.start()
    # Tell authenticator to use the certificate in a directory
    auth.configure_curve(domain='*', location=public_keys_dir)

    client = ctx.socket(zmq_sock_type)

    # We need two certificates, one for the client and one for
    # the server. The client must know the server's public key
    # to make a CURVE connection.
    client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
    client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
    client.curve_secretkey = client_secret
    client.curve_publickey = client_public

    server_public_file = os.path.join(public_keys_dir, "server.key")
    server_public, _ = zmq.auth.load_certificate(server_public_file)
    # The client must know the server's public key to make a CURVE connection.
    client.curve_serverkey = server_public
    yield client
    # stop auth thread
    auth.stop()


@contextmanager
def insecure_server_creator():
    """Insecure server - meant for temporary testing"""
    ctx = zmq.Context.instance()
    def creator(zmq_sock_type):
        server = ctx.socket(zmq_sock_type)
        return server
    
    yield creator

@contextmanager
def insecure_client(zmq_sock_type):
    """Insecure client - meant for temporary testing"""
    ctx = zmq.Context.instance()
    client = ctx.socket(zmq_sock_type)

    yield client