#!/usr/bin/env python
import logging
import os
from configparser import ConfigParser
import sys

import yaml
from docopt import docopt
from fabric import Connection
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from retrying import retry

log = logging.getLogger()

# config loaded from file as changes are rare during a project
HOME = os.path.expanduser("~")
with open("server.yml") as f:
    CONFIG = yaml.safe_load(f.read())


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


class Node:
    """ named AWS spot instance that can be saved and started later """

    def __init__(self):
        d = self.__dict__
        for k, v in CONFIG["aws"].items():
            d[k] = v

        # size and node
        self.size = [s for s in lc.list_sizes() if s.name == self.size][0]
        nodes = [
            node
            for node in lc.list_nodes()
            if (node.name == self.name) and (node.state == "running")
        ]
        if len(nodes) > 0:
            self.node = nodes[0]
        else:
            self.node = None

        # defaults
        d.setdefault("security", [self.name])
        d.setdefault("tags", dict(app=self.name))
        d.setdefault("volumesize", 8)

        # self.ip separate so can attempt connection before node.ip ready
        # TODO better to wait for associate ip but not clear if that is possible in libcloud
        self.ip = None
        if self.node:
            self.ip = self.node.public_ips[0]
        self._connection = None

    @property
    @retry(stop_max_attempt_number=300, wait_fixed=1000)
    def connection(self):
        if not self._connection:
            try:
                self._connection = Connection(
                    self.ip,
                    user="ubuntu",
                    connect_kwargs=dict(key_filename=f"{HOME}/.aws/key"),
                    connect_timeout=10,
                )
                self._connection.run("pwd", hide="stdout")
            except:
                self._connection = None
                raise
        return self._connection

    def start(self):
        if self.node:
            log.warning("node already exists")
            return

        # define image
        saved = lc.list_images(ex_owner="self", ex_filters=dict(name=self.name))
        if len(saved) == 0:
            log.info(f"{self.name} launching new server")
            image = lc.list_images(ex_image_ids=[self.image])[0]
        else:
            log.info(f"{self.name} relaunching saved server")
            image = saved[0]

        # create node
        self.node = lc.create_node(
            self.name,
            self.size,
            image,
            ex_keyname="key",
            ex_blockdevicemappings=[
                dict(DeviceName="/dev/sda1", Ebs=dict(VolumeSize=self.volumesize)),
            ],
            ex_spot=True,
            ex_security_groups=self.security,
            ex_metadata=self.tags,
        )

        log.info(f"waiting for {self.name} to start")
        _, ipaddresses = lc.wait_until_running([self.node])[0]
        self.ip = ipaddresses[0]

        # fix ip address
        fixedip = CONFIG["aws"].get("ip")
        if fixedip:
            ip_obj = [x for x in lc.ex_describe_all_addresses() if x.ip == fixedip][0]
            lc.ex_associate_address_with_node(self.node, ip_obj)
            self.ip = fixedip

        log.info(f"launched {self.name} at {self.ip}")

        c = self.connection

        if not saved:
            self.configure()
            self.upload()
            self.configure_project()

        # background thread to save if aws terminates
        c.run("chmod +x spotcheck.py")
        c.run(f"./spotcheck.py {self.name} &")

    def upload(self):
        c = self.connection

        # upload files
        saved = os.getcwd()
        os.chdir("server")
        for item in CONFIG["upload"]:
            if isinstance(item, list):
                src, dst = item
            else:
                src = item
                dst = os.path.basename(item)
            src = src.replace("~", HOME)
            if os.path.dirname(dst):
                c.run(f"sudo mkdir -p {os.path.dirname(dst)}")
            # upload to home then move as put does not accept sudo
            temp = os.path.basename(src)
            c.put(src, temp)
            c.run(f"dos2unix {temp}")
            if dst != temp:
                c.sudo(f"mv {temp} {dst}")
        os.chdir(saved)

    def configure(self):
        """ configure new server """
        c = self.connection
        c.sudo("apt-get update")
        c.sudo("apt-get install -y dos2unix python3-pip")
        c.sudo("pip install apache-libcloud requests")
        c.sudo("cp /usr/bin/python3 /usr/bin/python")

    def configure_project(self):
        """ configure for specific project"""
        c = self.connection
        c.run("bash ./configure.sh")

    def stop(self, save=True):
        if save:
            image = lc.list_images(ex_owner="self", ex_filters=dict(name=self.name))[0]
            lc.delete_image(image)
            lc.create_image(self.node, self.name)
        lc.destroy_node(self.node)


def main():
    """
    Usage:
        server.py (start|stop|upload) [--nosave]

    start=start server using config in server.yml
    stop=save image and stop server
    upload=upload latest files to server as defined in server.yml

    Options:
        -h --help       Show this screen.
        --nosave        Stop without saving
    """
    from defaultlog import log

    params = docopt(main.__doc__)
    log.info(params)
    save = not params["--nosave"]

    n = Node()
    if params["start"]:
        n.start()
    elif params["stop"]:
        n.stop(save)
    elif params["upload"]:
        n.upload()


if __name__ == "__main__":
    main()

"""
TODO upgrade to rasax 1.0
curl -s get-rasa-x.rasa.com | sudo bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
v0YeS1JOlbb6MRF4kEfC
"""
