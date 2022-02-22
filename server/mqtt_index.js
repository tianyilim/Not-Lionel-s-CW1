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

// Setting up Database
const sqlite3 = require('sqlite3').verbose();
// Qn: When do we need to close the database? is it on a per-query basis or can we avoid closing it?
let db = new sqlite3.Database("../db/es_cw1.db", sqlite3.OPEN_READWRITE, (err) => {
    if (err) { console.error(err.message); }
    console.log('JS Server connected to database.');
});

// listen to lock/out
// client.on('message', function (topic, message) {
//     const subtopics = topic.split('/');

//     // check that there are 5 subtopics:
//     // ic_embedded_group_4/lock_postcode/lock_cluster_id/lock_id/TOPIC
//     console.assert(subtopics.length==5, `Incorrect subtopic format, got ${topic}`)

//     let payload = JSON.parse(message.toString());
//     const timestamp = payload.timestamp;

//     console.log("Received message from lock/out");

// })

const moment = require('moment');

// send check in msg via mqtt when user check in
const mqtt_checkin = (lock_postcode, lock_cluster_id, lock_id, username, bike_sn) => {
    const topic = 'ic_embedded_group_4/' + lock_postcode + '/' + lock_cluster_id + '/' + lock_id + '/checkin';
    console.log(topic);
    const timestamp = moment().format('YYYY-MM-DD HH:mm:ss');
    const message = Buffer.from(JSON.stringify({
        "timestamp": timestamp,
        "username": username,
        "bike_sn": bike_sn,
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
app.use(express.json());
app.use(cors());
app.listen(5000, () => console.log("[HTTP] listening at port 5000"));

// listen for check in
app.post('/checkin',(request,response) => {
    var tmp = request.body;
    mqtt_checkin(tmp.lock_postcode, tmp.lock_cluster_id, tmp.lock_id, tmp.user, tmp.bike_sn);

    // TODO : wait for checkin confimration / unsucessful
    let state = true;
    response.json({state: state});
})

// prompt check out
// app.post('/usrauthen',(request,response) => {
//     var tmp = request.body;
//     // check does the username matches
//     response.json({
//         state: state, // state is tmp
//     });
// })

// listen for check out
app.post('/checkout',(request,response) => {
    var tmp = request.body;
    // serial key should be stored in the server
    mqtt_checkout(tmp.lock_postcode, tmp.lock_cluster_id, tmp.lock_id);

    response.json("Checkout Received");
})

// listen for user info
app.post('/usrinfo',(request,response) => {
    var tmp = request.body.username;

    // TODO: query SQL
    const msg = {
        checked: false,
        postcode: 'SW72AZ',
        cluster: 1,
        id: 1
    }

    response.json(msg);
})

// return user's bike name + sn
app.post('/usrbike',(request,response) => {
    var tmp = request.body.uername;
    console.log("usrbike")

    // TODO: query SQL
    const msg = [{
        bike_name: 'hello',
        bike_sn: '123',
    },{
        bike_name: 'world',
        bike_sn: "456",
    }]

    response.send(msg);
})

// check valid login
app.post('/login', (request,response) => {

    // TODO: query SQL to check logins
    var tmp = request.body;
    let state = false;
    if (tmp.username === 'abc' && tmp.pw === '123') {
        state = true;
    }

    response.json({state: state});
})

// return marker
app.get('/locks',(request,response) => {
    const sql = `SELECT * FROM cluster_coordinates;`;

    db.all(sql, [], (err,rows) => {
        if (err) throw err; 
        // rows.forEach(row => {
        //     console.log(row);
        // })  
        response.send(rows);
    })

})