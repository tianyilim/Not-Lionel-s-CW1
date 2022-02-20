# Webpage
This is the webpage app for Imperial College's Embedded System CW1. 

## Usage
Node.js is required to be installed for running the script. (https://nodejs.org/en/download/). Dependencies of the script can installed by `npm install` <br>

Running the script: <br>
```
npm start
```
A webpage would be hosted on `http://localhost:3000/`. This is currently still in development mode. In the final product, separately starting up of the React dev Server would not be needed. 

## Features 

### Map / Home Page
The webpage would show a map of the surrounding of the user's location with markers on bicycle lock clusters. A green pin indicates availability while a red pin indicates that all locks are used. <br/>
![image](img/map_markers.PNG)
<br/>
Upon clicking onto the pin, details about the lock would be shown, including name, total locks and available locks. <br/>
![image](img/map_w_details.PNG)
<br/>

Positions of the locks/pins are fetched upon loading the webpage (TODO)

### Check In / Check Out Page
The check in page has 3 text boxes for user to fill in the Serial Key number (Postcode-Cluster ID-ID) and a button to submit check in request. Upon checking in, information on the Lock Serial Key will be send across HTTP to the server on `http://localhost:5000/checkin` <br/>
![image](img/check_in_out.PNG) <br/>

A greyed out "Checked" button indicates that the user has successfully check in into the lock <br/>
![image](img/checked_in.PNG) <br/>

When the lock detects the bicycle is removed, via the server, it would prompt the user to check out on the web app. This is indicated by the red "Check Out" button. The web-app asks for updates every second from the server on `http://localhost:5000/usrauthen` to know the status of the lock. <br/>
![image](img/check_out.PNG) <br/>

The state of whether the user has checked into a lock is fetched on load of the page.

<br/>

### Register Page
Allow users to register into the system by filling in information such as full name, username, email address and passward.
![image](img/register.PNG)
<br/>

### Menu Bar
The footer is a menu bar that allows user to jump to different page. The lock icon refers to the Check In Page, the home icon refers to the home page and the person icon refers to the register page.

## TODO
1. User authentication (log in) 
    - send username when check in/check out
    - add bike serial number (and send accross HTTP)
2. Check in info stored on server instead of local
3. Lock database

## Change Log
27-Jan-2022 : initial commit <br/>
08-Feb-2022 : added map page <br/>
12-Feb-2022 : added check in out + register page. added router. <br/>
17-Feb-2022 : added HTTP communication with server on check in out page. <br/>