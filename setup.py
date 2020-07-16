import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="redisevents", 
    version="0.0.3",
    author="Grayden Shand",
    author_email="graydenshand@gmail.com",
    description="A small package for building a microservice event system in python with redis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/graydenshand/redisevents",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)