import glob
import hashlib
import hmac
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pgpy

BUF_SIZE = 65536
PUBKEY = """-----BEGIN PGP PUBLIC KEY BLOCK-----

mDMEaTlEoRYJKwYBBAHaRw8BAQdAbeDZb0eSYzoCc+4DbVJRopT3wse4gkldOR5X
u0Vy8EK0FkFSREZFdmVudCBWRVJJRklDQVRJT06IlgQTFgoAPhYhBDyElvboa11c
suaaTZLUcEDoxMEyBQJpOUShAhsDBQkFo5qABQsJCAcCBhUKCQgLAgQWAgMBAh4B
AheAAAoJEJLUcEDoxMEybr8A/j0W9tOPnTJwVNrk8qR/bTeIjea+2bzEPUMFOFaJ
1RvsAQCDooNWnT0YGGkmrEBgNoV0HN0UAMjvH/5cSHN99mjCC7g4BGk5RKESCisG
AQQBl1UBBQEBB0DjRHH+GuJ71FZlHEnKytuKazXChh58Wt+eD6PxAaBZPAMBCAeI
fgQYFgoAJhYhBDyElvboa11csuaaTZLUcEDoxMEyBQJpOUShAhsMBQkFo5qAAAoJ
EJLUcEDoxMEySEIBAM+PC2R7QnwFGo+8RaUxIbYXdXMlLeWmgleFcS5LTY3hAQCB
mCiXisGw+TiHVkXygFACasPp3dklqdSUdSfJaeSABQ==
=I1Kh
-----END PGP PUBLIC KEY BLOCK-----""".lstrip()


class PluginManager:
    def __init__(self, mw):
        self.mw = mw
        self.plugins = []
        self.pub_key = pgpy.PGPKey()
        self.pub_key.parse(PUBKEY)

    def load(self):
        plugins = glob.glob(str((Path.home() / ".ardfevent" / "plugins").absolute()) + "/**/plugin.json")
        for pluginp in plugins:
            with open(pluginp, "r", encoding="utf-8") as pf:
                plugin = json.load(pf)

            yield self.load_plugin(pluginp), plugin

    def verify_plugindir(self, plugroot: Path):
        if os.getenv("ARDF_NO_PLUGIN_VERIFY", "0") == "1":
            return True
        verfile = plugroot / "verify.ardf"
        versig = plugroot / "verify.ardf.asc"
        if not (verfile.exists() and versig.exists()):
            return False
        files = {}
        with open(verfile, "rb") as verf, open(versig, "rb") as sigf:
            ver = verf.read()
            s = pgpy.PGPSignature()
            s.parse(sigf.read())
            try:
                self.pub_key.verify(ver, s)
            except:
                return False
            for line in ver.decode("utf-8").splitlines():
                data = line.split("  ")
                files[data[1]] = data[0]
        for file in glob.glob(str(plugroot) + "/*"):
            path = Path(file)
            if path.name in ["verify.ardf", "verify.ardf.asc"]:
                continue
            if path.is_dir():
                if path.name == "__pycache__":
                    shutil.rmtree(str(path.absolute()))
                    continue
                if not self.verify_plugindir(path):
                    return False
            else:
                if not path.name in files.keys():
                    return False
                hsh = hashlib.sha256()
                with open(path, 'rb') as f:
                    while True:
                        data = f.read(BUF_SIZE)
                        if not data:
                            break
                        hsh.update(data)
                if not hmac.compare_digest(hsh.hexdigest(), files[path.name]):
                    return False
        return True

    def load_plugin(self, pluginp: str):
        if not self.verify_plugindir(Path(pluginp).parent.absolute()):
            return False
        with open(pluginp, "r", encoding="utf-8") as pf:
            plugin = json.load(pf)
        sys.path.append(str(Path(pluginp).parent.absolute()))
        spec = importlib.util.spec_from_file_location(plugin["name"],
                                                      Path(pluginp).parent / plugin["file"])
        plugmod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugmod)

        self.plugins.append(plugmod.fileplugin(self.mw))

        return True

    def startup(self):
        for plugin in self.plugins:
            plugin.on_startup()

    def readout(self, sinum: int):
        for plugin in self.plugins:
            plugin.on_readout(sinum)
