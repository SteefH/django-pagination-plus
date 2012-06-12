from setuptools import setup, find_packages
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

README = read('README.rst')

setup(
    name = "django-pagination-plus",
    packages = find_packages(),
    version = "0.0.3",
    author = "Stefan van der Haven",
    author_email = "stefan@steeffie.net",
    url = "https://github.com/SteefH/django-pagination-plus",
    description = "Utilities for pagination in Django templates",
    long_description = README,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords = ['django', 'pagination'],
)