const fetch = require('node-fetch');

const msg = {
    lock_postcode: 'SW72AZ',
    lock_cluster_id: 1, 
    lock_id: 1,
}


fetch('http://localhost:5000/checkin',{
    method: 'POST',
    headers: {
        'Content-type': 'application/json',
    },
    body: JSON.stringify(msg),
}).then(response => console.log(response));