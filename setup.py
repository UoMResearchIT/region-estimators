import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="region_estimators",
    version="0.1.43",
    author="Ann Gledson",
    author_email="ann.gledson@manchester.ac.uk",
    description="Make estimations for geographic regions, based on actual data (e.g. from sensors)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/UoMResearchIT/region_estimators",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
