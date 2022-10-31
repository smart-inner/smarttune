# What is SmartTune?
SmartTune is a black-box optimization that can automatically find good performance settings for a complex system's configuration knobs. 
It consists of two parts: client and server. When deploying the system, which makes it easier for users to find better performance settings.
Many complex systems have hundreds or even thousands of configuration knobs, Manual tuning can be time-consuming and expertise dependent.
SmartTune can quickly find better settings by using AI methods without manual intervention. So far, SmartTune supports configuration tuning of
TiDB@v6.1.0.

# Quick start
If you want to quick start, try the following commands, enjoy it!
### Start server
Server can be complied and used on Linux, CentOS. Python(>=3.6.0) is requirement, It is as simple as:
```shell
$ make
python3 setup.py bdist_wheel
running bdist_wheel
...
adding 'smarttune-0.0.1.dist-info/top_level.txt'
adding 'smarttune-0.0.1.dist-info/RECORD'
removing build/bdist.macosx-10.14.6-arm64/wheel
cp dist/*.whl ./
```
It is very easy to install the server, the command is as follows:
```shell
$ pip3 install smarttune-0.0.1-py3-none-any.whl
Processing /root/develop/smarttune/smarttune-0.0.1-py3-none-any.whl
Collecting scikit-learn==0.19.1
...
Successfully installed smarttune-0.0.1
```
Run the following command to start the server:
```shell
$ smarttune --config=/root/config.json
* Serving Flask app 'app' (lazy loading)
* Environment: production
...
INFO:werkzeug: * Running on http://172.16.7.68:5000/ (Press CTRL+C to quit)
```
The contents of config.json are as follows:
```json
{
    "db_url": "mysql://<username>:<password>@127.0.0.1:3306/smarttune",
    "testing": false
}
```
The 'db_url' specifies the url of mysql to store metadata.

### Start client

# Architecture

# License
