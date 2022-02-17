// HTTP socket to display React App
// currently not used
const express = require("express");
const react = express();
react.use(express.json());
react.listen(3001, () => console.log("listening at port 3000"));
// react.use(express.static("../client"));

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
    
        // socket.write("received");
    })
    socket.write("received");
})
TCP_server.listen(2000);


const mqtt = require('mqtt');
const e = require("express");
const { assert } = require("console");
// Sample code for MQTT with database implementation
const sqlite3 = require('sqlite3').verbose();
// Docs: https://www.sqlitetutorial.net/sqlite-nodejs/connect/

// Qn: When do we need to close the database? is it on a per-query basis or can we avoid closing it?
let db = new sqlite3.Database("../db/es_cw1.db", sqlite3.OPEN_READWRITE, (err) => {
  if (err) { console.error(err.message); }
  console.log('JS Server connected to database.');
});

const mqtt_options = {
  // Clean session
  clean: true,
  connectTimeout: 4000,
  // Auth
  clientId: 'js_server',
}

// On connecting to server
// '#' is a multi-level wildcard (we want to subscribe to all nodes downstream)
const client  = mqtt.connect('mqtt://localhost:1883', mqtt_options)
client.on('connect', function () {
  console.log('JS Server connecting to MQTT Broker')
  client.subscribe('ic_embedded_group_4/#', function (err) {
    if (!err) {
      // let msg = JSON.stringify({'msg':"hello"})
      // // let msg = Buffer.from(JSON.stringify({'msg':"hello"}), 'utf-8')
      // client.publish('ic_embedded_group_4/test', msg)
      console.log("JS Server connected to MQTT Broker")
    }
  })
})

client.on('message', function (topic, message) {
  // see what kind of message:
  const subtopics = topic.split('/');

  // check that there are 5 subtopics:
  // ic_embedded_group_4/lock_postcode/lock_cluster_id/lock_id/TOPIC
  console.assert(subtopics.length==5, `Incorrect subtopic format, got ${topic}`)

  let payload = message.toJSON()
  if (subtopics[4]=='stolen') {
    console.log(`Lock ${subtopics[1]} ${subtopics[2]} ${subtopics[3]} reported stolen at time ${payload['timestamp']}`)
    // TODO make this into a function, so that it can be reused in the Bicycle Reported Stolen from App case
    
    // insert into overall usage if a corresponding entry does not exist.
    // if it exists, then simply update it.
    // TODO how will the username, bike_sn, and in_time be known from a MQTT message?
    let sql = `INSERT INTO overall_usage
              (lock_postcode, lock_cluster_id, lock_id, username, bike_sn, in_time, stay_duration, remark)
              VALUES
              (${subtopics[1]}, ${subtopics[2]}, ${subtopics[3]},
                "johndoe", 1234, ${in_time}, ${duration}, 1)
              ON CONFLICT (
                lock_postcode, lock_cluster_id, lock_id, in_time
              ) DO UPDATE SET remark=1;`
    db.run(sql, function(err) { if (err) { return console.log(err.message); } })
    console.log("Upserted overall_usage table")

    // update current usage table
    sql = `UPDATE current_usage SET 
          username = NULL,
          bike_sn = NULL,
          lock_time = NULL,
          expected_departure_time = NULL,
          WHERE lock_postcode=${subtopics[1]}
          AND lock_cluster_id=${subtopics[2]}
          AND lock_id=${subtopics[3]}`
    db.run(sql, function(err) { if (err) { return console.log(err.message); } })
    console.log("Updated current_usage table")   

    // TODO alert user

  } else if (subtopics[4]=='telemetry') {
    console.log(`Received telemetry at time ${payload['timestamp']}`)
    // TODO Extension

  } else {
    // exception here - unknown topic
    console.assert(false, `Unknown topic ${topic}`)
  }
})

function updateCachedData(){
  // update average departure time for each lock 
  // - query overall_usage in the previous (time) and get a rolling average
  // TODO insert other periodically-called calculations here as well

}

// periodically calls function (to update cached average time and stuff)
// refresh every hour
var intervalId = setInterval(updateCachedData, 3.6e+6)

// const sha256 = require('crypto-js/sha256');
// const hmacSHA512 = require('crypto-js/hmac-sha512');
// const Base64 = require('crypto-js/enc-base64');

// const message = sha256("123" + "Message")
// console.log(Base64.stringify(hmacSHA512(message,"Key")))

// ~ SQL code dump

// ~ The following are SQL inserts, so they are run with `db.run`
// to be wrapped in a function providing the correct details
// when a bike checks in, set the variables to the appropriate values
// when a bike checks out, set the variables to NULL
let update_current_usage = `UPDATE current_usage 
                            SET username = ${username}
                            bike_sn = ${bike_sn}
                            lock_time = ${lock_time}
                            expected_departure_time = ${expected_departure_time}
                            WHERE lock_postcode=${lock_postcode}
                            AND lock_cluster_id=${lock_cluster_id}
                            AND lock_id=${lock_id};`

// self explanatory functions
let checkin_overall_usage = `INSERT INTO overall_usage
                            (lock_postcode, lock_cluster_id, lock_id, 
                              username, bike_sn, in_time, remark)
                            VALUES
                            (${lock_postcode}, ${lock_cluster_id}, ${lock_id},
                              ${username}, ${bike_sn}, ${in_time}, 0);`

let checkout_overall_usage = `UPDATE overall_usage
                              SET stay_duration=${stay_duration}
                              WHERE lock_postcode=${lock_postcode}
                              AND lock_cluster_id=${lock_cluster_id}
                              AND lock_id=${lock_id}
                              AND in_time=${in_time};`

// to insert a new user
let new_user = `INSERT INTO users
                (username, email, password_hashed)
                VALUES
                (${username}, ${email}, ${password_hashed});`

// to insert a new bicycle
let new_bicycle = `INSERT INTO bicycles
                  (bike_sn, bike_name, username)
                  VALUES
                  (${bike_sn}, ${bike_name}, ${username});`

// to remove a bicycle
let remove_bicycle = `DELETE FROM bicycles WHERE bike_sn=${bike_sn};`

// to remove a user. Remember to remove the user's bicycles too (below)
let remove_user = `DELETE FROM users WHERE username=${username};`
// remove all a users's bicycles
let remove_user_bicycles = `DELETE FROM bicycles WHERE username=${username};`

// ~ The following are SQL queries, so they are run with `db.all()` or `db.get()`

/*
// check if a corresponding entry has been made on the Overall Usage Table.
let sql = `SELECT username, remark FROM overall_usage
WHERE overall_usage.in_time=${payload['timestamp']}
AND overall_usage.lock_postcode=${subtopics[1]}
AND overall_usage.lock_cluster_id=${subtopics[2]}
AND overall_usage.lock_id=${subtopics[3]}`;
console.log("Checking if corresponding entry exists with query:", sql);

// we know we will only get one response (if we don't screw up...)
let does_row_exist = false;
db.get(sql, [], (err, row) => {
  if (err) { throw err; }
  return row
  // if a current entry exists with remark=0, set remark=1
  ? db.run(`UPDATE overall_usage
  SET overall_usage.remark=1
  WHERE overall_usage.in_time=${payload['timestamp']}
  AND overall_usage.lock_postcode=${subtopics[1]}
    AND overall_usage.lock_cluster_id=${subtopics[2]}
    AND overall_usage.lock_id=${subtopics[3]}
    `)
    // if not, create a corresponding table
    : db.run(`INSERT INTO overall_usage
    VALUES();
    `)
  });

  */