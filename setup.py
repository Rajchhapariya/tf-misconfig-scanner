from setuptools import setup, find_packages

setup(
    name="tf-misconfig-scanner",
    version="1.0.0",
    description="Static Terraform misconfiguration scanner with a measured comparison to Checkov",
    author="Raj Chhapariya",
    author_email="rajchhapariya8@gmail.com",
    packages=find_packages(),
    install_requires=[
        "python-hcl2>=8.1.4",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "tfscan = tfscan.cli:main",
        ],
    },
    python_requires=">=3.10",
)
