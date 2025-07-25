from setuptools import setup, find_packages

setup(
    name="api-diagnostics",
    version="1.0.0",
    description="CLI tool for debugging API calls with correlation tracking",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        'console_scripts': [
            'api-diagnostics=src.commands:cli',
        ],
    },
    python_requires=">=3.8",
)
