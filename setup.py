from setuptools import setup, find_packages

setup(
    name="vip-data-prep",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "xlsxwriter",
        "colorlog",
        "streamlit",
        "pytest",
        "types-requests",
        "types-python-dotenv",
        "pandas-stubs",
    ],
)
