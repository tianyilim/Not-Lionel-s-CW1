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

### Securing Mosquitto MQTT broker
- TODO: understand how TLS works...
- Steps to configure Mosquitto broker and MQTT client: [Source](https://mcuoneclipse.com/2017/04/14/enable-secure-communication-with-tls-and-the-mosquitto-broker/)
1. Create a **CA Key Pair**
   1. `openssl genrsa -out m2mqtt_ca.key 2048`
   2. TODO: Figure out if we need a passphrase (the `-des3` flag in `openssl`)
   3. The passphrase is used to protect the private key. We shall use `ic_embedded_cw1` as the passphrase.
   4. A `.key` file will be generated with both a private and public key.
2. Create a **CA Certificate** and sign it with the CA Private Key from (1)
   1. `openssl req -new -x509 -days 3650 -key m2mqtt_ca.key -out m2mqtt_ca.crt`
   2. An additional passphrase would ...
3. Create the **Broker Key Pair**
   1. `openssl genrsa -out m2mqtt_srv.key 2048`
   2. Not using the `-des3` flag here, as a password would need to be entered when the broker is started.
4. Create a **CA Certificate Sign Request** using the Broker Key from (3)
   1. `openssl req -new -out m2mqtt_srv.csr -key m2mqtt_srv.key`
5. Use the **CA Certificate** from (2) to sign the request from (4) to get the broker certificate
   1. `openssl x509 -req -in m2mqtt_srv.csr -CA m2mqtt_ca.crt -CAkey m2mqtt_ca.key -CAcreateserial -out m2mqtt_srv.crt -days 3650`

- At the end of this, the following files should have been created:
  - `m2mqtt_ca.crt`  : CA Certificate
  - `m2mqtt_ca.key`  : CA key pair (private, public)
  - `m2mqtt_ca.srl`  : CA serial number file
  - `m2mqtt_srv.crt` : server certificate
  - `m2mqtt_srv.csr` : certificate sign request, not needed any more
  - `m2mqtt_srv.key` : server key pair

- Inside mosquitto (`/etc/mosquitto`), create a folder called `certs` and put in `m2mqtt_ca.crt`, `m2mqtt_srv.crt`, and `m2mqtt_srv.key`.
- Then create a new mosquitto conf file (it's in `comms/ic_es_mosquitto.conf`)
- From the root of the Git repo, you can then run `mosquitto -c comms/ic_es_mosquitto.conf -v`.

- For the clients, we can use the following from this [source](http://www.steves-internet-guide.com/mosquitto-tls/)
- `client.tls_set(‘PATH_TO_STUFF/m2mqtt_ca.crt‘)`
- We bind to port `8883`, the default for MQTT on TLS.