import os

from dotenv import load_dotenv

load_dotenv()
env = os.getenv("RUNNING_ENVIRONMENT")

if env=="dev":
    # TODO: In memory persistence
    pass
else:
    # TODO: Use perstent storage
    pass
