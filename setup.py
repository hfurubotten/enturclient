import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="enturclient",
    version="0.2.1",
    python_requires=">=3.5.3",
    author="Heine Furubotten",
    description="An API client for public transport data from Entur.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hfurubotten/enturclient",
    license="MIT",
    packages=setuptools.find_packages(),
    install_requires=["aiohttp>=3.5.4", "async_timeout>=3.0.1"],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
