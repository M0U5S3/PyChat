from setuptools import setup, find_packages

VERSION = '0.1.0' 
DESCRIPTION = 'PyChat'
LONG_DESCRIPTION = 'A fully encrypted chat server + client (includes a GUI)'

# Setting up
setup(
        name="PyChatM0", 
        version=VERSION,
        author="M0U5S3",
        author_email="dariushwalker28@gmail.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['cryptography==37.0.2', 'rsa==4.9'],
        
        keywords=['python', 'package', 'socket', 'encryption', 'server', 'client', 'M0U5S3', 'chat', 'social'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)
