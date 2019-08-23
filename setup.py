import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="puredata-compiler",
    version="0.0.1",
    author="Dylan Burati",
    author_email="dylanburati@protonmail.com",
    description="A tool for writing PureData patches",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dylanburati/puredata-compiler",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio",
    ],
)