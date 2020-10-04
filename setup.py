import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dracoon-UNBEKANNTES-PFERD", # Replace with your own username
    version="0.1.0",
    author="Octavio Simone",
    author_email="octsim@gmail.com",
    description="DRACOON API connector for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)