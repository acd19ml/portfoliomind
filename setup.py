from setuptools import setup, find_packages

setup(
    name="cryptomcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastmcp>=2.3.3",
        "websockets>=10.0",
        "aiohttp>=3.9.3",
    ],
    extras_require={
        "test": [
            "pytest>=8.3.5",
            "pytest-asyncio>=0.23.5",
        ]
    },
    python_requires=">=3.8",
) 