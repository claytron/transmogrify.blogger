from setuptools import setup, find_packages
import os

version = '1.0'

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


description_parts = (
    read("transmogrify", "blogger", "README.rst"),
    '',
    read("docs", "HISTORY.rst"),
    '',
    )
long_description = "\n".join(description_parts)

setup(
    name='transmogrify.blogger',
    version=version,
    description="A transmogrifier source for Blogger Atom exports",
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Text Processing :: Markup :: XML",
        ],
    keywords='blogger transmogrifier atom xml source',
    author='Clayton Parker',
    author_email='robots@claytron.com',
    url='http://github.com/claytron/transmogrify.blogger',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['transmogrify'],
    include_package_data=True,
    install_requires=[
        'setuptools',
        'collective.transmogrifier',
        ],
    zip_safe=False,
    )
