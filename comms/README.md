# Setup
## Software dependencies
### RPi setup
- `pip install -r requirements_rpi.txt`

### Server setup
- Create a conda environment if you wish. Then either run
- `pip install -r requirements_server.txt` or `conda install --file requirements_server.txt`

#### Setup the MQTT broker on the server
- [Instruction source](http://www.steves-internet-guide.com/install-mosquitto-linux/)
```
sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo apt clean
```

#### Stopping and Starting Mosquitto MQTT broker
- For now, run `mosquitto -v` manually on the command line.
- To start using a config file, do `mosquitto -c FILENAME`
- References: 
  - [Mosquitto Config Options](https://mosquitto.org/man/mosquitto-conf-5.html) (Put a `.conf` file in `/etc/mosquitto/conf.d/`)
  - 