import setuptools


with open('repixelator/repixelator.py', encoding='utf-8') as f:
    for line in f.readlines():
        if '__version__' in line:
            __version__ = line.split("'")[1].strip()
            break

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name='repixelator',
    version=__version__,
    author='YeongChan Lee',
    author_email='yclee126@gmail.com',
    description='Converts resized pixel arts to their original resolution',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT License',
    url='https://github.com/yclee126/RePixelator',
    entry_points ={
        'console_scripts': [
            'repixelator = repixelator:cmd',
            'repixelator-gui = repixelator:gui',
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=['repixelator'],
    package_data={'repixelator' : ['icon.ico']},
    install_requires = [
        'opencv-python',
        'numpy',
    ],
    python_requires='>=3.5',
)