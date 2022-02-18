# HTTP_SIM

This directory provides files to simulate HTTP requests sent from the client web-app. Starting up the React Dev App is not needed for testing.

## Usage
All dependencies should already be installed. But if encounter any `Module not found` error, packages can be installed as following:

```
server> npm install
```

## Files
The files are to be used with `../mqtt_index.js`

### Event 2
`http_checkin` sends a request to the http port 5000, which declares a checkin on the web. This prompts `mqtt_index.js` to send a message in topic `ic_embedded_group_4/+/+/+/checkin`

### Event 4
`http_checkout` sends a request to the http port 5000, which declares a checkout on the web (Event 4). This prompts `mqtt_index.js` to send a message in topic `ic_embedded_group_4/+/+/+/checkout`. This event should only happen after Event 3 (`ic_embedded_group_4/+/+/+/out`)