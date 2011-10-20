# Copyright (C) 2011 Linaro Limited
#
# Author: Michael Hudson-Doyle <michael.hudson@linaro.org>
#
# This file is part of LAVA Dispatcher.
#
# LAVA Dispatcher is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# LAVA Dispatcher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along
# with this program; if not, see <http://www.gnu.org/licenses>.

import logging
import time

import pexpect


class LavaConmuxConnection(object):

    def __init__(self, device_config, sio):
        self.device_config = device_config
        cmd = "conmux-console %s" % self.device_option("hostname")
        self.proc = pexpect.spawn(cmd, timeout=3600, logfile=sio)
        #serial can be slow, races do funny things if you don't increase delay
        self.proc.delaybeforesend=1

    def device_option(self, option_name):
        return self.device_config.get(option_name)

    def device_option_int(self, option_name):
        return self.device_config.getint(option_name)



    def sendline(self, *args, **kw):
        self.proc.sendline()

    def expect(self, *args, **kw):
        self.proc.expect(*args, **kw)

    def sendcontrol(self, *args, **kw):
        self.proc.sendcontrol(*args, **kw)

    @property
    def match(self):
        return self.proc.match



    def soft_reboot(self):
        self.proc.sendline("reboot")
        # set soft reboot timeout 120s, or do a hard reset
        id = self.proc.expect(
            ['Will now restart', pexpect.TIMEOUT], timeout=120)
        if id != 0:
            self.hard_reboot()

    def hard_reboot(self):
        self.proc.send("~$")
        self.proc.sendline("hardreset")
        # XXX Workaround for snowball
        if self.device_type == "snowball_sd":
            time.sleep(10)
            self.in_master_shell()
            # Intentionally avoid self.soft_reboot() to prevent looping
            self.proc.sendline("reboot")
            self.enter_uboot()

    def enter_uboot(self):
        self.proc.expect("Hit any key to stop autoboot")
        self.proc.sendline("")

    def _boot(self, boot_cmds):
        self.soft_reboot()
        try:
            self.enter_uboot()
        except:
            logging.exception("enter_uboot failed")
            self.hard_reboot()
            self.enter_uboot()
        self.proc.sendline(boot_cmds[0])
        for line in range(1, len(boot_cmds)):
            if self.device_type in ["mx51evk", "mx53loco"]:
                self.proc.expect(">", timeout=300)
            elif self.device_type == "snowball_sd":
                self.proc.expect("\$", timeout=300)
            else:
                self.proc.expect("#", timeout=300)
            self.proc.sendline(boot_cmds[line])
