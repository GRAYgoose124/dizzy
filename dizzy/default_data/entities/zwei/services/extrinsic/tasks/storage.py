import json
from dizzy import Task
from dizzy.daemon.settings import SettingsManager

SM = SettingsManager()

data_root = SM.settings.data_root


class Store(Task):
    """storage task, see 'store.json'"""

    @staticmethod
    def run(ctx):
        with open(data_root / "store.json", "w") as f:
            f.write(json.dumps(ctx))

        return "Unused, see 'store.json'"
