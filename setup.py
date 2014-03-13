from setuptools import setup

VERSION = '0.1'

DESCRIPTION = "A little library for using callback properties"
NAME = "echo"
AUTHOR = "Chris Beaumont"
AUTHOR_EMAIL = "cbeaumont@cfa.harvard.edu"
MAINTAINER = AUTHOR
MAINTAINER_EMAIL = AUTHOR_EMAIL
LICENSE = "MIT"

setup(name=NAME,
      description=DESCRIPTION,
      version=VERSION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      maintainer=MAINTAINER,
      maintainer_email=MAINTAINER_EMAIL,
      license=LICENSE,
      py_modules=['echo'],
      classifiers=[
          'Development STatus :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Operating System :: OS Independent',
          'Topic :: Utilities'],
      )
