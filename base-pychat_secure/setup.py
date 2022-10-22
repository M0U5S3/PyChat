from setuptools import setup, find_packages

VERSION = '1.0.0'
DESCRIPTION = 'PyChat - M0U5S3'
LONG_DESCRIPTION = 'An easy to use fully encrypted chat server/client package that can be used to create your own chat servers'

# Setting up
setup(
        name="pychat_secure",
        version=VERSION,
        author="M0U5S3",
        author_email="dariushwalker28@gmail.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['cryptography==37.0.2', 'rsa==4.9'],
        
        keywords=['python', 'PyChat','pychat_secure', 'package', 'socket', 'encryption', 'server', 'client', 'M0U5S3', 'chat', 'social', 'cryptography', 'RSA'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)
