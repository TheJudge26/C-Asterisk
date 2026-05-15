from setuptools import setup, find_packages

setup(
    name="cstar",
    version="0.1.0",
    packages=find_packages(),
    # dependencies 
    install_requires=[
        "llvmlite",
    ],
    
    entry_points={
        "console_scripts": [
            "cstar = src.main:main",
        ],
    },
)