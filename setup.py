from setuptools import setup, find_packages

setup(
    name='lightdb',
    version='0.1.0',
    description='A lightweight key-value database using SQLite and APSW.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Hexa',
    author_email='shexa.developer@gmail.com',
    url='https://github.com/superhexa/lightdb',  
    packages=find_packages(),
    install_requires=[
        'apsw',  
    ],
    python_requires='>=3.6',  
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    keywords='database key-value sqlite apsw',
    project_urls={
        'Documentation': 'https://github.com/superhexa/lightdb#readme',  
        'Source': 'https://github.com/superhexa/lightdb',  
        'Tracker': 'https://github.com/superhexa/lightdb/issues',  
    },
    include_package_data=True,
    zip_safe=False,
)