from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='latextree',
    version='1.1.3',
    description='Document object model for Latex',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='http://github.com/dimbyd/latextree',
    author='D Evans',
    author_email='evansd8@cf.ac.uk',
    license='MIT',
    packages=['latextree'],
    install_requires=[
        'jinja2',
        'bibtexparser',
        'lxml',
        'six',
    ],
    entry_points={
        'console_scripts': ['ltree=latextree.ltree:main'],
    },
    zip_safe=False,
)
