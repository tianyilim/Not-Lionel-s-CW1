// HTTP socket to display React App
// currently not used
const express = require("express");
const react = express();
react.use(express.json());
react.listen(3001, () => console.log("listening at port 3000"));
react.use(express.static("../client"));

// TCP socket
var net = require('net');

const TCP_server = net.createServer(socket => {
    socket.on("data", data => {
        var tmp;
        try {
            tmp = data.toString();
        } catch(e) {
            return;
        }

        console.log(tmp);
    
        socket.write("received");
    })
})
TCP_server.listen(2000);