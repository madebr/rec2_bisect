from pathlib import Path
import tempfile


REC2_BISECT_ROOT = Path(__file__).resolve().parent
REC2_DEPS_ROOT = REC2_BISECT_ROOT / "deps"
REC2_DOWNLOAD_ROOT = Path(tempfile.gettempdir()) / "downloads"
REC2_CONFIG_PATH = REC2_BISECT_ROOT / "config.ini"
