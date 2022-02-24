import { useState, React, useEffect } from 'react'
import { GoogleMap, Marker, useJsApiLoader } from '@react-google-maps/api';
import { AiOutlineClose } from 'react-icons/ai';

function Map() {
  // info for google map
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: "AIzaSyDRNQB3_vgwOBfziEHzuLl9fhE4tbbCCEo"
  })
  const [details, setDetails] = useState(false)
  const containerStyle = {
    height: details ? '65vh' : '100vh'
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
          { /* Child components, such as markers, info windows, etc. */ }
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

      <div>
        <AiOutlineClose className='CloseButton' onClick={ () => setDetails(false) } />
        {(currentMarker != null) ? 
        <div>
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
        </div>
        : <></>
        }

      </div>

    </div>

  ) : <></>
}

export default Map