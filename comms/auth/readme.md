Authentication Steps

- Create a AWS EC2 instance and install Mosquitto, as described in the Readme in `comms/`
- Assign the appropriate in/outbound rules:
  - Over TCP:
    - SSH (22)
    - MQTT (1883)
    - MQTT-S (8883)
- Assign an Elastic IP address to the EC2 instance.
- This is described [here](https://medium.com/@achildrenmile/mqtt-broker-on-aws-ec2-hands-on-install-configure-test-out-f12dd2f5c9d0)


## Setting up Client and Server Keys
- Follow the steps detailed on [Stack Overflow](https://stackoverflow.com/questions/70110392/mqtt-tls-certificate-verify-failed-self-signed-certificate)
- Running in the EC2 instance:
1. Create a file called `v3.ext` containing:
  ```
  authorityKeyIdentifier=keyid,issuer
  basicConstraints=CA:FALSE
  keyUsage = digitalSignature, keyEncipherment
  subjectAltName=DNS:localhost, IP:${IP_ADDR}
  ```
  Where `${IP_ADDR}` is the Elastic IP address of the EC2 instance. 
2. `openssl genrsa -des3 -out ca.key 2048`
   1. For the passphrase, I used `ic_es_cw1`.
3. `openssl req -new -key ca.key -out ca.csr -sha256`
  1. We don't actually enter a Common Name as the CA does not live on a server with a name.
   ```
   Country Name (2 letter code) [XX]:GB
   State or Province Name (full name) []:London
   Locality Name (eg, city) [Default City]:Fulham
   Organization Name (eg, company) [Default Company Ltd]:IC_ES_CA
   Organizational Unit Name (eg, section) []:.
   Common Name (eg, your name or your server's hostname) []:.
   Email Address []:.

   Please enter the following 'extra' attributes
   to be sent with your certificate request
   A challenge password []:ic_es_cw1
   An optional company name []:.
   ```
4. `openssl x509 -req -in ca.csr -signkey ca.key -out ca.crt -days 365 -sha256`
5. `openssl genrsa -out server.key 2048`
6. `openssl req -new -key server.key -out server.csr -sha256`
  2. For this, key in the assigned Elastic IP address:
   ```
   Country Name (2 letter code) [XX]:GB
   State or Province Name (full name) []:London
   Locality Name (eg, city) [Default City]:Fulham
   Organization Name (eg, company) [Default Company Ltd]:IC_ES_Server
   Organizational Unit Name (eg, section) []:.
   Common Name (eg, your name or your server's hostname) []: ${ELASTIC_IP_ADDR_HERE}
   Email Address []:.

   Please enter the following 'extra' attributes
   to be sent with your certificate request
   A challenge password []:ic_es_cw1
   An optional company name []:ic_es_cw1
   ```
7. `openssl x509 -req -in server.csr -CA ca.crt -extfile v3.ext -CAkey ca.key -CAcreateserial -out server.crt -days 360`

## Setting up user authentication
- Follow the instructions on [Steve's Internet Guide](http://www.steves-internet-guide.com/mqtt-username-password-example/)
1. Create a simple text file and enter the username and passwords, one for each line, with the username and password separated by a colon.
    ```
    echo "user:user" > pw_plaintext.txt
    cp pw_plaintext.txt pw_cipher.txt
    ```
2. Encrypt the password file using `mosquitto_passwd -U pw_cipher.txt`

## Setting up `mosquitto.conf`
- Put the following in `mosquitto.conf`:
- (assuming that everything is put in `/home/ec2-user/auth`)...
```
listener 8883

cafile /home/ec2-user/auth/ca.crt
keyfile /home/ec2-user/auth/server.key
certfile /home/ec2-user/auth/server.crt

allow_anonymous false
password_file /home/ec2-user/pw_cipher.txt

tls_version tlsv1.2
```
- Then you can run `mosquitto -v -c /home/ec2-user/auth/mosquitto.conf` from in the EC2 instance.

## Publishing and Subscribing
- Run this on the client machine. The current valid `ca.crt` is in the same directory as this readme.
- 
- Publishing in debug mode on topic `ic_es_test` with message "test"
- Port is 8883 and hostname is the Elastic IP address found earlier.
- We use the username and password defined earlier, "user" for both.
  - `mosquitto_pub -d -t ic_es_test -m "test" --cafile ${PATH_TO_ca_crt} -p 8883 -h ${ELASTIC_IP_ADDR_HERE} -u user -P user`
- Subscribing in debug mode, very much similar to above
  - `mosquitto_sub -d -t ic_es_test --cafile ${PATH_TO_ca_crt} -p 8883 -h ${ELASTIC_IP_ADDR_HERE} -u user -P user`
  - Examples of secure Python connection are in `mqtt_client.py` and `mqtt_server.py` in the containing folder.