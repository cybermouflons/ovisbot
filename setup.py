import os

from setuptools import setup

kwargs = {
    "include_package_data": True,
}

if os.getenv("READTHEDOCS", False):
    setup(
        install_requires=[
            "aiohttp==3.6.2",
            "async-timeout==3.0.1",
            "attrs==20.1.0",
            "beautifulsoup4==4.9.1",
            "certifi==2022.12.7",
            "cffi==1.14.2",
            "chardet==3.0.4",
            "colorama==0.4.3",
            "colorthief==0.2.1",
            "discord-py==1.4.1",
            "feedparser==5.2.1",
            "gitdb==4.0.5",
            "gitpython==3.1.7",
            "idna==2.10",
            "multidict==4.7.6",
            "parse==1.17.0",
            "pillow==7.2.0",
            "pycparser==2.20",
            "pycryptodome==3.9.8",
            "pymodm==0.4.3",
            "pymongo==3.11.0",
            "pynacl==1.4.0",
            "python-dateutil==2.8.1",
            "python-dotenv==0.14.0",
            "pytz==2020.1",
            "requests==2.24.0",
            "six==1.15.0",
            "smmap==3.0.4",
            "soupsieve==2.0.1",
            "texttable==1.6.2",
            "typing-extensions==3.7.4.3; python_version < '3.8'",
            "urllib3==1.25.10",
            "yarl==1.5.1",
        ],
        **kwargs,
        python_requires=">=3.7",
    )
else:
    setup(**kwargs)
