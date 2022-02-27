import { useState, React, useEffect } from 'react'
import { GoogleMap, Marker, useJsApiLoader } from '@react-google-maps/api';
import { AiOutlineClose } from 'react-icons/ai';

import ReactApexChart from "react-apexcharts"

function Map() {
  // info for google map
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: "AIzaSyDRNQB3_vgwOBfziEHzuLl9fhE4tbbCCEo"
  })
  const [details, setDetails] = useState(false)
  const containerStyle = {
    height: details ? '45vh' : '100vh'
  };
  const [currentLoc, setCurrentLoc] = useState({ lat: 51.49918363237076, lng: -0.17634013995995976 })

  if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(function(position) {
      setCurrentLoc({lat:position.coords.latitude, lng:position.coords.longitude})
    });
  } else {
    // might need some error handling
    console.log("Not Available");
  }

  const [currentMarker, setCurrentMarker] = useState(null)
  // lat, lon, lock_postcode, lock_cluster_id, num_lock
  const [markers, setMarkers] = useState([]);
  const [markerAvail, setMarkerAvail] = useState([]);

  const today = new Date();
  // Sunday = 0, Monday = 1, Tuesday = 2, ...
  const [currentDay, setCurrentDay] = useState(today.getDay());
  const [allDay, setAllDay] = useState([])

  const [histogram, setHistogram] = useState({
    options: {
      chart: {
        type: 'histogram'
      },
      xaxis: {
        categories: ['00:00','03:00','06:00','09:00','12:00','15:00','18:00','21:00']
      },
      yaxis: {
        max: 100,
      },
      tooltip: {
        enabled: false
      }
    },
    series: [{
      data: allDay[currentDay]
    }]
  })

  const onClickMarker = (item) => {
    setDetails(true); 
    let avail = markerAvail.find(element => {
      return element.lock_postcode === item.lock_postcode && 
      element.lock_cluster_id === item.lock_cluster_id
    })
    setCurrentMarker({...item, count: avail ? avail.count : 0});
  }

  // fetch markers position + name
  const initial_fetch = () => {
    fetch('http://'+process.env.REACT_APP_IP+':5000/locks',{
      method: 'GET',
      headers: {
        'Content-type': 'application/json',
      },
    })
    .then(response => response.json())
    .then(response => {
      setMarkers(response);
    })

    fetch('http://'+process.env.REACT_APP_IP+':5000/lockavail', {
      method: 'GET',
      headers: {
        'Content-type': 'application/json',
      },
    })
    .then(response => response.json())
    .then(response => {
      setMarkerAvail(response);
    })

    fetch('http://'+process.env.REACT_APP_IP+':5000/lockstat', {
      method: 'GET',
      headers: {
        'Content-type': 'application/json',
      },
    })
    .then(response => response.json())
    .then(response => {
      setAllDay(response.data);
    })
  }
  
  useEffect(() => {
    initial_fetch();
  },[])

  return isLoaded ? (
    <div>
      <GoogleMap
          id = "map"
          mapContainerStyle={containerStyle}
          center={currentLoc}
          zoom={15}
      >
          {markers.map((item,index) => {
            let location = {lat: Number(item.lat), lng: Number(item.lon)};
            let avail = markerAvail.find(element => {
              return element.lock_postcode === item.lock_postcode && 
              element.lock_cluster_id === item.lock_cluster_id
            })
            return (
              <Marker key={index} position={location} 
                icon={avail ? "https://maps.google.com/mapfiles/ms/icons/green-dot.png" : "https://maps.google.com/mapfiles/ms/icons/red-dot.png"}
                onClick={ () => onClickMarker(item) }
              />
            )
          })}
          
      </GoogleMap>

      {details ? 

      <div
        style={{height: '40vh'}}
      >
        <AiOutlineClose className='CloseButton' 
          onClick={ () => {
            setDetails(false);
            setCurrentDay(today.getDay());
        } } />

        {(currentMarker != null) ? 
        <div className='DetailsBox'>
          <div className='Details'>
            Name: {currentMarker.lock_postcode}-{currentMarker.lock_cluster_id}<br/>
            Total locks: {currentMarker.num_lock} <br/>
            Available locks: {currentMarker.count} <br/> 
          </div>

          <br/>

          <button className='Details'>
            <a style={{textDecoration: 'none', color: 'black'}}
              href={"/checkin?serialKey=" + currentMarker.lock_postcode + "+" + currentMarker.lock_cluster_id} 
            >
              Check In
            </a>
          </button>

          <br/>
          
          <div className='Details'>
            Popular times: 

            <div>
              <select
                style={{
                  fontSize: '15px',
                  paddingLeft: '5px',
                  color: '#707070',
                  marginLeft: '10px',
                }}
                value={currentDay}
                onChange={(event) => {
                  setCurrentDay(event.target.value);
                  setHistogram({...histogram, series: [{data: allDay[event.target.value]}]})
                }}
              >
                <option value={0}> Sunday </option>
                <option value={1}> Monday </option>
                <option value={2}> Tuesday </option>
                <option value={3}> Wednesday </option>
                <option value={4}> Thursday </option>
                <option value={5}> Friday </option>
                <option value={6}> Saturday </option>
                </select>
            </div>
          </div>
          
          <div className='DetailsGraph'>
            <ReactApexChart  
              options={histogram.options} 
              series={histogram.series} 
              type='histogram' 
            />
          </div>
        </div>
        : <></>
        }

      </div> : <></> }

    </div>

  ) : <></>
}

export default Map