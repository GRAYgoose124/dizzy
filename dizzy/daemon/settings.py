import os
from pathlib import Path
from dataclasses import dataclass, fields
import shutil
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    data_root: Path
    all_common_services: dict
    all_entities: dict
    common_services: dict
    default_entities: dict


@dataclass
class MetaSettings:
    entities_dir: Path
    common_services_dir: Path


class SettingsManager:
    _instance = None
    settings: Settings
    _meta: MetaSettings

    def __new__(
        cls,
        *args,
        write_to_disk=False,
        live_reload=False,
        force_use_default_data=False,
        **kwargs
    ):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)

        # TODO: Probably should do this another way, but it works for now.
        # Get from DIZZY_DATA_ROOT, ~/.dizzy, or packaged default_data.
        env_var = os.getenv("DIZZY_DATA_ROOT")
        env_root = Path(env_var) if env_var else None
        home_root = Path("~/.dizzy")
        packaged_root = Path(__file__).parent.parent / "default_data"

        if env_var and not (env_root / "settings.yml").exists() and write_to_disk:
            shutil.copytree(packaged_root, env_root, dirs_exist_ok=True)
        # if not (home_root / "settings.yml").exists() and write_to_disk:
        #    shutil.copytree(packaged_root, home_root, dirs_exist_ok=True)

        cls._instance.live_reload = live_reload

        cls._instance.data_root = (
            env_root
            if env_var and env_root.exists()
            else home_root
            if home_root.exists()
            else packaged_root
        )

        # if force_use_default_data:
        #    cls._instance.data_root = packaged_root

        return cls._instance

    def load_settings(
        self,
    ) -> Settings:
        daemon_settings_file = self.data_root / "settings.yml"
        common_service_dir = self.data_root / "common_services"
        entities_dir = self.data_root / "entities"

        with open(daemon_settings_file, "r") as f:
            settings_from_yaml = yaml.safe_load(f)["settings"]
            default_common_services = settings_from_yaml["common_services"]
            default_entities = settings_from_yaml["entities"]

            _all_common_service_files = [
                common_service_dir / s / "service.yml"
                for s in common_service_dir.iterdir()
                if s.is_dir()
            ]

            _all_entity_files = [
                entities_dir / e / "entity.yml"
                for e in entities_dir.iterdir()
                if e.is_dir()
            ]

        all_common_services = {
            s.name: f
            for s, f in zip(common_service_dir.iterdir(), _all_common_service_files)
        }
        common_services = {
            s: f for s, f in all_common_services.items() if s in default_common_services
        }

        all_entities = {
            e.name: f for e, f in zip(entities_dir.iterdir(), _all_entity_files)
        }
        default_entities = {
            e: f for e, f in all_entities.items() if e in default_entities
        }

        self._settings = Settings(
            self.data_root,
            all_common_services,
            all_entities,
            common_services,
            default_entities,
        )

        self._meta = MetaSettings(entities_dir, common_service_dir)

    @property
    def settings(self):
        if not hasattr(self, "_settings") or not self._settings or self.live_reload:
            self.load_settings()
        return self._settings

    @property
    def meta(self):
        if not hasattr(self, "_meta") or not self._meta or self.live_reload:
            self.load_settings()
        return self._meta

    @staticmethod
    def default():
        root = Path(__file__).parent.parent.parent / "data"
        return Settings(
            root,
            {},
            {},
            {},
            {},
        )

    def inject(self, globals):
        """Injects settings into the global namespace provided - pass `globals()`."""
        for k in [f.name for f in fields(Settings)]:
            if k in globals:
                del globals[k]
            globals[k] = getattr(self.settings, k)

        if "__all__" not in globals:
            globals["__all__"] = []
        globals["__all__"].extend(self.settings.__dict__.keys())


# Basically, Anything in Settings can be accessed as if it were a global in settings... Ie settings.data_root.
# If you pass something like SettingsManager(write_to_disk=True) it will allow copying of the default_data to ~/.dizzy.
# If you pass something like SettingsManager(write_to_disk=True, force_use_default_data=True) it will use the default_data packaged with dizzy and write it wherever you specify.
SettingsManager().inject(globals())
