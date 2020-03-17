import setuptools

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except:
    long_description = "A package with useful tools"

setuptools.setup(
    name="kitir",
    version="1.0.8",
    author="Inbar Rose",
    author_email="inbar.rose1@gmail.com",
    python_requires=">=3.7.4",
    summary="A package with useful tools",
    description="A package with useful tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/InbarRose/kitir",
    packages=setuptools.find_packages(),
    install_requires=[
        'pytz',
        'requests'
    ],
    classifiers=(
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
