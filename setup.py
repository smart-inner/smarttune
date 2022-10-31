from setuptools import setup, find_packages

setup(
    name="smarttune", 
    version="0.0.1",
    description="A black box optimization service for tuning system knobs",
    url='https://github.com/smart-inner/smarttune',
    author='Yaozheng Wang',
    author_email='wyaozheng@gmail.com',
    packages= find_packages(),
    include_package_data=True,
    install_requires=[
        'flask==2.0.3',
        'flask-sqlalchemy==2.5.1',
        'flask-executor==1.0.0',
        'flask-apscheduler==1.12.4',
        'gpflow==1.5.0',
        'numpy==1.15.4',
        'scipy==1.0.0',
        'loguru==0.6.0',
        'scikit-learn==0.19.1'
    ],
    python_requires='>=3.6.0',
    entry_points = {
        'console_scripts': ['smarttune = server.run:main']
    })