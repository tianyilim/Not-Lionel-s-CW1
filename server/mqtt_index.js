var state = false;

const mqtt = require('mqtt');

const mqtt_options = {
    // Clean session
    clean: true,
    connectTimeout: 4000,
    // Auth
    clientId: 'js_server',
}

// On connecting to server
const client  = mqtt.connect('mqtt://localhost:1883', mqtt_options)
client.on('connect', function () {
  console.log('JS Server connecting to MQTT Broker')
  client.subscribe('ic_embedded_group_4/+/+/+/out', function (err) {
    if (!err) { console.log("JS Server connected to MQTT Broker") }
  })
})

// listen to lock/out
client.on('message', function (topic, message) {
    const subtopics = topic.split('/');

    // check that there are 5 subtopics:
    // ic_embedded_group_4/lock_postcode/lock_cluster_id/lock_id/TOPIC
    console.assert(subtopics.length==5, `Incorrect subtopic format, got ${topic}`)

    let payload = JSON.parse(message.toString());
    const timestamp = payload.timestamp;

    // EVENT: prompt user 
    // TODO
    state = true;

    console.log("Received message from lock/out");

})

const moment = require('moment');

// send check in msg via mqtt when user check in
const mqtt_checkin = (lock_postcode, lock_cluster_id, lock_id) => {
    const topic = 'ic_embedded_group_4/' + lock_postcode + '/' + lock_cluster_id + '/' + lock_id + '/checkin';
    console.log(topic);
    const timestamp = moment().format('YYYY-MM-DD HH:mm:ss');
    const message = Buffer.from(JSON.stringify({
        "timestamp": timestamp,
        "username": "token",
        "bike_sn": "",
    }));
    
    client.publish(topic, message);
    console.log("MQTT Check In Message sent");
}

// send check out msg via mqtt when user check out
const mqtt_checkout = (lock_postcode, lock_cluster_id, lock_id) => {
    const topic = 'ic_embedded_group_4/' + lock_postcode + '/' + lock_cluster_id + '/' + lock_id + '/checkout';
    const timestamp = moment().format('YYYY-MM-DD HH:mm:ss');
    const message = Buffer.from(JSON.stringify({
        "timestamp": timestamp,
    }));
    
    client.publish(topic, message);
    console.log("MQTT Check Out Message Send")
}

const express = require("express");
const app = express();
const cors = require('cors');
const { response } = require('express');
app.use(express.json());
app.use(cors());
app.listen(5000, () => console.log("[HTTP] listening at port 5000"));

// listen for check in
app.post('/checkin',(request,response) => {
    var tmp = request.body;
    mqtt_checkin(tmp.lock_postcode, tmp.lock_cluster_id, tmp.lock_id);

    response.json("Checkin Received");
})

// prompt check out
app.post('/usrauthen',(request,response) => {
    var tmp = request.body;
    // check does the username matches
    response.json({
        state: state, // state is tmp
    });
})

// listen for check out
app.post('/checkout',(request,response) => {
    var tmp = request.body;
    // serial key should be stored in the server
    mqtt_checkout(tmp.lock_postcode, tmp.lock_cluster_id, tmp.lock_id);
    state = false;

    response.json("Checkout Received");
})

// listen for user info
app.post('/usrinfo',(request,response) => {
    var tmp = request.body.username;

    // play around with the database
    const msg = {
        checked: true,
        postcode: 'SW72AZ',
        cluster: 1,
        id: 1
    }

    response.json(msg);
})

const sqlite3 = require('sqlite3').verbose();

// Qn: When do we need to close the database? is it on a per-query basis or can we avoid closing it?
let db = new sqlite3.Database("../db/es_cw1.db", sqlite3.OPEN_READWRITE, (err) => {
    if (err) { console.error(err.message); }
    console.log('JS Server connected to database.');
});
  
// return marker
app.get('/locks',(request,response) => {
    const sql = `SELECT * FROM cluster_coordinates;`;

    db.all(sql, [], (err,rows) => {
        if (err) throw err; 
        // rows.forEach(row => {
        //     console.log(row);
        // })  
        response.send(rows);
        // console.log("send response on initial fetch");
    })

})