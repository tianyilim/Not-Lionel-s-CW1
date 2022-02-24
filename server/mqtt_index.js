// setting up web-app
const express = require("express");
const react = express();
react.use(express.json());
react.listen(3001, () => console.log("listening at port 3000"));
react.use(express.static("public"));

// FileSync
const fs = require ('fs');

// MQTT
const mqtt = require('mqtt');
const mqtt_options = {
    // Clean session
    clean: true,
    connectTimeout: 4000,
    // Auth
    clientId: 'js_server',
    username:'user',
    password:'user',

    protocol: 'mqtts',
    ca: fs.readFileSync('../comms/auth/ca.crt'),
    rejectUnauthorized: true,
    minVersion: 'TLSv1.2',
}

const mqtt_address = 'mqtts://35.178.122.34:8883'    // secure

// On connecting to server
const client  = mqtt.connect(mqtt_address, mqtt_options)
client.on('connect', function () {
  console.log('JS Server connecting to MQTT Broker')
  // subscribe to checkinresponse
  client.subscribe('ic_embedded_group_4/+/+/+/checkinresponse', function (err) {
    if (!err) { console.log("JS Server connected to MQTT Broker: checkinresponse") }
  })
  client.subscribe('ic_embedded_group_4/+/+/+/stolen', function (err) {
    if (!err) { console.log("JS Server connected to MQTT Broker: stolen") }
  })
})

// Setting up Database
const sqlite3 = require('sqlite3').verbose();
// Qn: When do we need to close the database? is it on a per-query basis or can we avoid closing it?
let db = new sqlite3.Database("../db/es_cw1.db", sqlite3.OPEN_READWRITE, (err) => {
    if (err) { console.error(err.message); }
    console.log('JS Server connected to database.');
});

// Setting up Email Account
const nodemailer = require('nodemailer');
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: 'ic.embedded.group4@gmail.com',
      pass: 'not_lionel_s'
    }
});
const ip_address = 'localhost'

// hacky way to open HTTP channel while waiting for MQTT message
var desired_msg = '';
var resp = null;

client.on('message', function (topic, message) {
    let payload = JSON.parse(message.toString());

    if (resp !== null && desired_msg === topic) {
        console.log("Received checkin payload", payload);
        resp.json({state: payload.status, msg: payload.message});

        // reset variables
        desired_msg = '';
        resp = null;
    }
})

// listen to /stolen
client.on('message', function (topic, message) {
    let subtopics = topic.split('/');
    if (subtopics[4] !== 'stolen') return;

    // query db to find user's email address
    const address = 'mm.aderation@gmail.com';
    
    const mailOptions = {
        from: 'ic.embedded.group4@gmail.com',
        to: address,
        subject: 'Critical Security Alert',
        html: `<p>
                We have detected unusual behaviour at your bike. 
                If this was you, please log-in into your account to review your activity <br/> <br/>
                <a href="http://` + ip_address + `:3000/profile">Review Activity </a>
            </p>`
    }

    transporter.sendMail(mailOptions, function(error, info){
        if (error) {
          console.log(error);
        } else {
          console.log('Email sent: ' + info.response);
        }
    });
})

const moment = require('moment');

// send check in msg via mqtt when user check in
// prompt by app.post('/checkin')
const mqtt_checkin = (lock_postcode, lock_cluster_id, lock_id, username, bike_sn) => {
    const topic = 'ic_embedded_group_4/' + lock_postcode + '/' + lock_cluster_id + '/' + lock_id + '/checkin';
    const timestamp = moment().format('YYYY-MM-DD HH:mm:ss');
    const message = Buffer.from(JSON.stringify({
        "timestamp": timestamp,
        "username": username,
        "bike_sn": bike_sn,
    }));
    
    client.publish(topic, message);
    console.log("MQTT Check In Message sent at: " + topic + "\n"+ message );
}

// send check out msg via mqtt when user check out
// prompt by app.post('/checkout')
const mqtt_checkout = (lock_postcode, lock_cluster_id, lock_id) => {
    const topic = 'ic_embedded_group_4/' + lock_postcode + '/' + lock_cluster_id + '/' + lock_id + '/checkout';
    const timestamp = moment().format('YYYY-MM-DD HH:mm:ss');
    const message = Buffer.from(JSON.stringify({
        "timestamp": timestamp,
    }));
    
    client.publish(topic, message);
    console.log("MQTT Check Out Message Send")
}

const app = express();
const cors = require('cors');
app.use(express.json());
app.use(cors());
app.listen(5000, () => console.log("[HTTP] listening at port 5000"));

// listen for check in
app.post('/checkin',(request,response) => {
    var tmp = request.body;
    mqtt_checkin(tmp.lock_postcode, tmp.lock_cluster_id, tmp.lock_id, tmp.user, tmp.bike_sn);
    resp = response;
    desired_msg = "ic_embedded_group_4/" + tmp.lock_postcode + "/" + tmp.lock_cluster_id.toString() + "/" + tmp.lock_id.toString() + "/checkinresponse";
  
    // should there be some timeout thing?
    // response.json({state: true});  
})

// listen for check out
app.post('/checkout',(request,response) => {
    var tmp = request.body;
    mqtt_checkout(tmp.lock_postcode, tmp.lock_cluster_id, tmp.lock_id);

    response.json("Checkout Received");
})

// listen for user info
app.post('/usrinfo',(request,response) => {
    var tmp = request.body.username;

    const sql = `SELECT lock_postcode, lock_cluster_id, lock_id, bike_sn FROM current_usage WHERE username=?;`;

    db.all(sql, [tmp], (err,row) => {
        if (err) throw err; 
        // console.log(row);
        let msg = {};
        if (row.length) {
            let tmp = row[0];
            msg = {
                checked: true,
                postcode: tmp.lock_postcode,
                cluster: tmp.lock_cluster_id,
                id: tmp.lock_id,
                bike_sn: tmp.bike_sn
            }
        } else {
            msg = {
                checked: false,
                postcode: '',
                cluster: 0,
                id: 0,
                bike_sn: ''
            }
        }
        response.json(msg);
    })    

    // for testing
    // const msg = {
    //     checked: true,
    //     postcode: 'SW72AZ',
    //     cluster: 1,
    //     id: 1,
    //     bike_sn: 123
    // }
    // response.json(msg);
})

// return user's bike name + sn
app.post('/usrbike',(request,response) => {
    var tmp = request.body.username;

    const sql = `SELECT bike_name, bike_sn FROM bicycles WHERE username=?;`;

    db.all(sql, [tmp], (err,rows) => {
        if (err) throw err; 
        // console.log(rows);
        response.send(rows)
    })    
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
    const sql = `SELECT * FROM cluster_coordinates;`

    const try1 = `SELECT * FROM cluster_coordinates
    WHERE lock_postcode=? 
    AND lock_cluster_id=?;`
    
    // -> lat, lon, lock_postcode, lock_cluster_id, num_lock
    /*pseudocode:
        for postcode in lock_postcode:
            for cluster in lock_cluster_id:
                `SELECT COUNT(*) FROM current_usage
                WHERE lock_postcode=?, lock_cluster_id=?, occupied=1;
                `
                retval = count of occupied items
                -> get occupancy based on retval/num_lock
                -> append to list?
    */
    
    /*
    `SELECT cluster_coordinates.lock_postcode, cluster_coordinates.lock_cluster_id, cluster_coordinates.num_lock, COUNT(*) FROM current_usage
    JOIN cluster_coordinates 
    ON cluster_coordinates.lock_postcode=current_usage.lock_postcode 
    AND cluster_coordinates.lock_cluster_id=current_usage.lock_cluster_id 
    WHERE current_usage.occupied=0
    GROUP BY current_usage.lock_postcode, current_usage.lock_cluster_id;`

    `SELECT DISTINCT COUNT(*)
    FROM cluster_coordinates INNER JOIN current_usage 
    ON cluster_coordinates.lock_postcode=current_usage.lock_postcode 
    AND cluster_coordinates.lock_cluster_id=current_usage.lock_cluster_id 
    AND current_usage.occupied=0;`

    // IN: postcode, cluster_id
    // OUT: lat, lon, number of locks(num_lock), available locks/occupied locks
    */

    db.all(sql, [], (err,rows) => {
        if (err) throw err; 
        response.send(rows);
    })

})
