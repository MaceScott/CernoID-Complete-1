from setuptools import setup, find_packages
import os

def read_requirements():
    """Read the requirements file."""
    with open('requirements.txt') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="cernoid",
    version="1.0.0",
    packages=find_packages(where="backend/src"),
    package_dir={"": "backend/src"},
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "cernoid=main:run_app",
        ],
    },
    package_data={
        "core.face_recognition": ["data/*.xml", "data/*.dat"],
        "config": ["*.json", "*.yaml"],
    }
) 