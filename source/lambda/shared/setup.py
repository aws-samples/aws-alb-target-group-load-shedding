import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="elbloadmonitor",
    version="0.0.1",

    description="Library to shed and restore load on AWS ALB",

    author="author",
    license='APACHE',
    # packages=setuptools.find_packages(where="elb_load_monitor"),
    packages=['elb_load_monitor'],
    install_requires=[
        'boto3', 'botocore'
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",

        "Typing :: Typed",
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=True
)
