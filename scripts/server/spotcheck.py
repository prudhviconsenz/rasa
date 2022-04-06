#!/usr/bin/env python
from threading import Thread
from time import sleep
import sys
import os
from configparser import ConfigParser

from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
import requests

HOME = os.path.expanduser("~")


def main():
    """ monitor aws termination notice and save image before termination
    pass name of node to spotcheck
    """
    name = sys.argv[1]
    t = Thread(target=spotcheck, args=(name,))
    t.start()
    t.join()


def get_libcloud():
    """ get libcloud driver """
    cfg = ConfigParser()
    cfg.read(f"{HOME}/.aws/credentials")
    access = cfg.get("default", "aws_access_key_id")
    secret = cfg.get("default", "aws_secret_access_key")
    cls = get_driver(Provider.EC2)
    lc = cls(access, secret, region="eu-west-1")
    return lc


lc = get_libcloud()


def spotcheck(name):
    nodes = [
        node
        for node in lc.list_nodes()
        if (node.name == name) and (node.state == "running")
    ]
    node = nodes[0]

    while True:
        r = requests.get(
            "http://169.254.169.254/latest/meta-data/spot/termination-time"
        )
        if r.status_code == 200:
            lc.create_image(node, name)
            break
        sleep(5)


if __name__ == "__main__":
    main()
