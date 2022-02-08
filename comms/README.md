# Setup
## Software dependencies
### RPi setup
- `pip install -r requirements_rpi.txt`

## Server setup
### Connecting to the AWS Instance
- This assumes you are using Linux.
- Download the `.pem` authentication key located in whatsapp and place it in a linux directory.
- Run `sudo chmod 400 KEY.pem` where KEY is the key filename.
- Find out the instance public IPV4 DNS from the AWS console. For instance, `ec2-18-170-215-85.eu-west-2.compute.amazonaws.com`.
- SSH into the device:
  - `ssh -i PATH_TO_KEY.pem ec2-user@PUBLIC_IPV4_DNS`. 
  - For example: `ssh -i ~/.ssh/icl_embeddedsystems_cw.pem ec2-user@ec2-18-170-215-85.eu-west-2.compute.amazonaws.com`

### Setting up the AWS instance
- Create a conda environment if you wish. Then either run
- `pip install -r requirements_server.txt` or `conda install --file requirements_server.txt`
### Setup the MQTT broker on the server
#### Instructions for local installation (`apt`)
- [Instruction source](http://www.steves-internet-guide.com/install-mosquitto-linux/)
```bash
sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo apt clean
```
#### Instructions for Amazon Linux (`yum`)
- [Instruction source](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-the-mosquitto-mqtt-messaging-broker-on-centos-7)
```bash
sudo amazon-linux-extras install epel   # install extras for Amazon Linux
sudo -y yum install mosquitto
```

### Stopping and Starting Mosquitto MQTT broker
- For now, run `mosquitto -v` manually on the command line.
- To start using a config file, do `mosquitto -c FILENAME`
- References: 
  - [Mosquitto Config Options](https://mosquitto.org/man/mosquitto-conf-5.html) (Put a `.conf` file in `/etc/mosquitto/conf.d/`)
  - [MQTT Topic Hierarchy Convention](https://homieiot.github.io/)