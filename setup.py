import setuptools

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except:
    long_description = "A package with useful tools"

setuptools.setup(
    name="kitir",
    version="1.0.9",
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
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 5 - Production/Stable",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
