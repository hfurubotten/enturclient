import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="enturclient",
    version="0.1.3",
    author="Heine Furubotten",
    description="An API client for public transport data from Entur.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hfurubotten/enturclient",
    license='MIT',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
