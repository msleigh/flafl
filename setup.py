import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flafl",
    version="0.0.4",
    author="M Sleigh",
    author_email="author@example.com",
    description="Flask application for listening to Bitbucket webhooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/msleigh/flafl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    scripts=["flafld"],
    install_requires=["flask"],
)
