const mqtt = require('mqtt');
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

const check_curr_usage = async(lock_postcode, lock_cluster_id, lock_id) => {
  const sql = `SELECT occupied, username, lock_time FROM current_usage
  WHERE lock_postcode=\'${lock_postcode}\'
  AND lock_cluster_id=${lock_cluster_id}
  AND lock_id=${lock_id};`;

  console.log("Checking if corresponding entry exists with query:\n", sql);

  // ret = {
  //         'username': false,
  //         'lock_time': false,
  //         'occupied': false
  //       };

  const rtn = await db.get(sql, [], (err, row) => {
    if (err) { throw err; }
    console.log(row)

    ret = {
      'username': false,
      'lock_time': false,
      'occupied': false
    };

    ret.username = row.username != null;
    ret.lock_time = row.lock_time != null;
    ret.occupied = row.occupied;

    return ret;

  });

  console.log(rtn);
  return rtn;

  // console.log(ret);
  // return ret;
}

const parse_mqtt_response = async(lock_postcode, lock_cluster_id, lock_id, ) => {
  const sql = `SELECT occupied, username, lock_time FROM current_usage
  WHERE lock_postcode=\'${lock_postcode}\'
  AND lock_cluster_id=${lock_cluster_id}
  AND lock_id=${lock_id};`;

  console.log("Checking if corresponding entry exists with query:\n", sql);

  const state = await db.get(sql, [], (err, row) => {
    if (err) { throw err; }
    console.log(row)

    ret = {
      'username': false,
      'lock_time': false,
      'occupied': false
    };

    ret.username = row.username != null;
    ret.lock_time = row.lock_time != null;
    ret.occupied = row.occupied;

    return ret;

  });
}

// On connecting to server
// '#' is a multi-level wildcard (we want to subscribe to all nodes downstream)
const client  = mqtt.connect('mqtt://localhost:1883', mqtt_options)
client.on('connect', function () {
  console.log('JS Server connecting to MQTT Broker')
  client.subscribe('ic_embedded_group_4/#', function (err) {
    if (!err) { console.log("JS Server connected to MQTT Broker") }
  })
})

client.on('message', function (topic, message) {
  // see what kind of message:
  const subtopics = topic.split('/');
  console.log(subtopics)

  // check that there are 5 subtopics:
  // ic_embedded_group_4/lock_postcode/lock_cluster_id/lock_id/TOPIC
  console.assert(subtopics.length==5, `Incorrect subtopic format, got ${topic}`)

  let payload = JSON.parse(message.toString());
  // let payload = message.toJSON()
  console.log("Payload:", JSON.stringify(payload))

  // query current_usage as a measure of the current state.
  // let state = check_curr_usage(subtopics[1], subtopics[2], subtopics[3]);
  // console.log(state);

  let sql_update_curr_usage_param = {
    'occupied': false,
    'lock_time': 'NULL',
    'expected_departure_time': 'NULL'
  };

  let to_update_curr_usage = false;
  let to_update_overall_usage = false;



  if (subtopics[4]=='in') {
    // Rpi sends that a bicycle has entered the lock (event 1)
    sql_update_curr_usage_param.occupied = true;
    sql_update_curr_usage_param.lock_time = payload.timestamp;
    to_update_curr_usage = true;
    
    // Check the state
    if (!state.username && !state.lock_time && !state.occupied) {
      // State A, the start state
      console.log(subtopics[1], subtopics[2], subtopics[3], "State A->C at time", payload.timestamp)
      sql_update_curr_usage_param.lock_time = payload.timestamp;
    } else if (!state.username && state.lock_time && state.occupied) {
      // State C, something enters the lock even after the lock is already occupied
      // update the current usage table with the most recent time
      sql_update_curr_usage_param.lock_time = payload.timestamp;
      console.log(subtopics[1], subtopics[2], subtopics[3], "State C->C at time", payload.timestamp)
      console.warn(subtopics[1], subtopics[2], subtopics[3], 
        "In message received while lock still occupied. Updated lock_time.")
    } else if (state.username && state.lock_time && !state.occupied) {
      // State B, after user has manually checked in
      console.log(subtopics[1], subtopics[2], subtopics[3], "State B->D at time", payload.timestamp)
    } else {
      // Throw an error
      console.error(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload.timestamp)
      assert(false, 'RPi In response in error state');
      to_update_curr_usage = false;
    }

  } else if (subtopics[4]=='out') {
    // Rpi sends that a bicycle has left the lock (event 3)
    sql_update_curr_usage_param.occupied = false;
    sql_update_curr_usage_param.lock_time = 'null';
    to_update_curr_usage = true;
    to_update_overall_usage = true;

    // Check the state
    if (!state.username && state.lock_time && state.occupied) {
      // State C, anonymous user removes bike
      console.log(subtopics[1], subtopics[2], subtopics[3], "State C->A at time", payload.timestamp)

    } else if (state.username && state.lock_time && state.occupied) {
      // State D, bike removed with named user
      // TODO trigger User Authentication event
      console.log(subtopics[1], subtopics[2], subtopics[3], "State D->E at time", payload.timestamp)

    } else {
      // Throw an error
      console.error(subtopics[1], subtopics[2], subtopics[3], "Unexpected state detected", payload.timestamp)
      assert(false, 'RPi Out response in error state');
      to_update_curr_usage = false;
    }

  } else if (subtopics[4]=='stolen') {
    // TODO Extension
    console.log(`Lock ${subtopics[1]} ${subtopics[2]} ${subtopics[3]} detected stolen at time ${payload['timestamp']}`)
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
    console.log(subtopics[1], subtopics[2], subtopics[3], 'Received telemetry at time', payload.timestamp);
    // TODO Extension

  } else {
    // exception here - unknown topic
    console.assert(false, `Unknown topic ${topic}`)
  }

  if (to_update_overall_usage) {
    // TODO 
    // notably when a bike is removed
  }

  if (to_update_curr_usage) {
    // SQL command template to update current_usage table
    // We *should* update the expected_departure_time in response to RPi MQTT messages, but it's a TODO for now.
    const sql = `
          UPDATE current_usage SET
          occupied = ${sql_update_curr_usage_param.occupied},
          lock_time = \'${sql_update_curr_usage_param.lock_time}\',
          expected_departure_time = NULL
          WHERE lock_postcode=\'${subtopics[1]}\'
          AND lock_cluster_id=${subtopics[2]}
          AND lock_id=${subtopics[3]};`

    console.log("Updating current_usage table with query:\n", sql);

    db.run(sql, [], function(err) {
      if (err) { return console.error(err.message); }
    });
  }

  console.log('\n\n\n');

})