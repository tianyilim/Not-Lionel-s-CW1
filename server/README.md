# Server
This is the server (javascript) for Imperial College's Embedded System CW1, it is expected to communicate with the Raspberry Pi by TCP protocol and communicate with the client.

## Usage
Node.js is required to be installed for running the script. (https://nodejs.org/en/download/). Dependencies of the script can installed by `npm install` <br>

Running the script:
```
node index.js
```

A TCP socket is actively listening at port 2000. It receives a string from the client and returns a "received" message. A prototype of the TCP client is set up in `TCPC.py`.

A webpage would be hosted in port 3001. However, as the React app / webpage is still under development, the feature is not working yet.

## Change Log
27-Jan-2022 : initial commit