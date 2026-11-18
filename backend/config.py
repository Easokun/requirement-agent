import os


def _load_dotenv():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except OSError:
        pass


_load_dotenv()

API_KEY = os.environ.get("BAILIAN_API_KEY", "")

BASE_URL = os.environ.get(
    "BAILIAN_BASE_URL",
    "https://ws-snssl43i8q90cnoj.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
