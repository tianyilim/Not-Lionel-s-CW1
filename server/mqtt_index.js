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

// const mqtt_address = 'mqtts://35.178.122.34:8883'    // secure
const mqtt_address = 'mqtts://localhost:8883';

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
const ip_address = '35.178.122.34'

// hacky way to open HTTP channel while waiting for MQTT message
var desired_msg = '';
var resp = null;

client.on('message', function (topic, message) {
    let payload = JSON.parse(message.toString());

    if (resp !== null && desired_msg === topic) {
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

    const sql = `SELECT users.email, users.username FROM users 
    JOIN current_usage 
    ON users.username=current_usage.username 
    WHERE current_usage.lock_postcode=? 
    AND current_usage.lock_cluster_id=? 
    AND current_usage.lock_id=?;`

    let address = '';
    let username = '';
    let rtn_flag = false;

    db.get(sql, [subtopics[1], Number(subtopics[2]), Number(subtopics[3])], (err, row) => {
        if (err) {return console.log(err.message);}

        if (row === undefined) {
            rtn_flag = true;
            return;
        }
        address = row.email;
        username = row.username;
        if (address === null || address === '') return;

        const mailOptions = {
            from: 'ic.embedded.group4@gmail.com',
            to: address,
            subject: 'Critical Security Alert',
            html: `<p>
                    We have detected unusual behaviour at your bike. 
                    If this was you, please log-in into your account to review your activity <br/> <br/>
                    <a href="http://` + ip_address + `:3000/reportstolen">Review Activity </a>
                </p>`
        }
    
        transporter.sendMail(mailOptions, function(error, info){
            if (error) {
              console.log(error);
            } 
        });

        const timestamp = moment().format('YYYY-MM-DD HH:mm:ss');
        const sql2 = `UPDATE users SET email_flag=? WHERE username=?;`
        db.run(sql2, [timestamp, username], (err) => {
            if (err) {
                return console.error(err.message); 
            }
        });
    });

    if (rtn_flag) return;

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
const { response } = require("express");
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
})

// return user's bike name + sn
app.post('/usrbike',(request,response) => {
    var tmp = request.body.username;

    const sql = `SELECT bike_name, bike_sn FROM bicycles WHERE username=?;`;

    db.all(sql, [tmp], (err,rows) => {
        if (err) throw err; 
        response.send(rows)
    })    
})

// return user's email flag
app.post('/emailflag', (request, response) => {
    var tmp = request.body.username;

    const sql = `SELECT email_flag FROM users WHERE username=?;`
    db.get(sql, [tmp], (err, row) => {
      if (err) { return console.error(err.message); }
      if (row === undefined || row === null) response.json({email_flag: null});
      else response.json({email_flag: row.email_flag})
    });
})

// user update bike info
app.post('/bikeupdate', (request,response) => {
    var tmp = request.body;

    var sql = '';
    var params = [];
    
    switch(tmp.state) {
        case 'insert':
            sql = `INSERT INTO bicycles 
            (bike_sn, bike_name, username)
            VALUES (?, ?, ?);
            `
            params = [tmp.new.bike_sn, tmp.new.bike_name, tmp.user];
            break;
        case 'update':
            sql =  `UPDATE bicycles SET
            bike_sn=?, bike_name=?
            WHERE username=? AND bike_sn=? AND bike_name=?;
            `
            params = [tmp.new.bike_sn, tmp.new.bike_name, tmp.user, tmp.original.bike_sn, tmp.original.bike_name];
            break;
        case 'delete':
            sql = `DELETE FROM bicycles WHERE
            bike_sn=? AND
            bike_name=? AND
            username=?;
            `
            params = [tmp.original.bike_sn, tmp.original.bike_name, tmp.user];
            break;
    }
    
    db.run(sql, params, function(err){
        if (err) { response.json("Error!"); return console.error(err.message); }
        response.json("Received");
    });
})

// check valid login
app.post('/login', (request,response) => {
    var tmp = request.body;
    let state = false;
    if (tmp.username === 'abc' && tmp.pw === '123') {
        state = true;
    }
    const sql = `SELECT password_hash FROM users WHERE username=?;`
    db.get(sql, [tmp.username], (err,row) => {
        if (err) { return console.error(err.message); }
        
        if (row === null) response.json({state: false});
        else response.json({state: row.password_hash === tmp.pw})
    })
})

// register new users
app.post('/register', (request, response) => {
    var tmp = request.body;
    const sql = `INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?);`
    db.run(sql, [tmp.username, tmp.email, tmp.pw], (err)=> {
        if (err) {return console.log(err);}
        response.json("Received");
    })
})

app.post('/stolenstate', (request, response) => {
    var tmp = request.body;

    // 0: false alarm (bike in)
    // 1: check out
    // 2: true alarm

    const timestamp = moment().format('YYYY-MM-DD HH:mm:ss');
    const message = Buffer.from(JSON.stringify({
      "timestamp": timestamp, state: tmp.state
    }));

    // report -> true alarm. checkout -> false alarm.
    let base_topic = 'ic_embedded_group_4/' + tmp.postcode + '/' + tmp.cluster + '/' + tmp.id;
    
    if (tmp.state !== 0) {
      base_topic+='/report';
      client.publish(base_topic, message);
    }

    // remove email flag
    if (tmp.user !== '') {
      // we might be reporting anonymously
      const sql = `UPDATE users SET email_flag=NULL WHERE username=?;`
      db.run(sql, [tmp.user], (err) =>{
        if (err) {return console.log(err.message);}
      });
    }

    response.json("Processed stolen state");
})

app.get('/locks',(request,response) => {

    const sql1 = `SELECT * FROM cluster_coordinates;`
    db.all(sql1, [], (err, rows) => {
        if (err) { return console.log(err); }
        response.send(rows);
    });
    
})

app.get('/lockavail',(request,response) => {
    // Need to make sure that we match the lock postcode, cluster id 
    // with appropriate vals on the other side
    const sql2 = `SELECT lock_postcode, lock_cluster_id, COUNT(*) as count
        FROM current_usage WHERE occupied=0 
        GROUP BY lock_postcode, lock_cluster_id;`
    db.all(sql2, [], (err, rows) => {
        if (err) { return console.log(err.message); }
        response.send(rows);
    });
})

app.post('/lockstat',(request, response) => {
    // hardcoded stat, in percentage
    const data = Array(7).fill().map(()=> Array(8).fill(0));

    // query for occupancy percentage
    const tmp = request.body;

    const usage_query = `SELECT avg_usage FROM cluster_coordinates WHERE lock_postcode=? AND lock_cluster_id=?;`
    db.get(usage_query, [tmp.postcode, tmp.cluster], (err, row) => {
        if (err) { return console.log(err.message); }

        // deserialise json object
        let usage = JSON.parse(row.avg_usage.toString());

        data[0] = usage.sun;
        data[1] = usage.mon;
        data[2] = usage.tue;
        data[3] = usage.wed;
        data[4] = usage.thu;
        data[5] = usage.fri;
        data[6] = usage.sat;

        response.json({data:data});
    })
})

app.post('/avg_time', (request, response) => {
    const tmp = request.body;

    const sql = `SELECT AVG(stay_duration) AS avg FROM overall_usage WHERE lock_postcode=? AND lock_cluster_id=?;`

    db.get(sql, [tmp.postcode, tmp.cluster], (err, row) => {
        if (err) { return console.log(err.message); }
        if (row === undefined) {
            response.json({
                h: 0,
                m: 0,
                s: 0
            })
        } else {
            const msg = {
                h: Math.floor(row.avg / 3600),
                m: Math.floor( (row.avg / 60) % 60 ),
                s: Math.floor(row.avg % 60),
            }
            response.json(msg);
        }
    })
})


