import { useState, React } from 'react'
import { GoogleMap, Marker, useJsApiLoader } from '@react-google-maps/api';
import { AiOutlineClose } from 'react-icons/ai';

const center = {
  lat: 51.49918363237076,
  lng: -0.17634013995995976
};

function Map() {
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: "AIzaSyDRNQB3_vgwOBfziEHzuLl9fhE4tbbCCEo"
  })

  const [details, setDetails] = useState(false)
  const [currentMarker, setCurrentMarker] = useState(null)
  const [markers, setMarkers] = useState([{
      id: 0,
      location: {lat: 51.49918363237076, lng: -0.17634013995995976},
      total: 20,
      free: 0,
      available: false
    },{
      id: 1,
      location: {lat: 51.5, lng: -0.169},
      total: 30,
      free: 15,
      available: true
  }])

  const containerStyle = {
    height: details ? '70vh' : '100vh'
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
            return (
              <Marker key={index} position={item.location} 
                icon={item.available ? "https://maps.google.com/mapfiles/ms/icons/green-dot.png" : "https://maps.google.com/mapfiles/ms/icons/red-dot.png"}
                onClick={ () => {setDetails(true); setCurrentMarker(item);} }
              />
            )
          })}
          
      </GoogleMap>

      <div>
        <AiOutlineClose className='CloseButton' onClick={ () => setDetails(false) } />
        {(currentMarker != null) ? 
          <div className='Details'>
            <br/>
            Name: <br/>
            Total locks: {currentMarker.total} <br/>
            Available locks: {currentMarker.free} <br/>
          </div>
        : <></>
        }
      </div>

    </div>

  ) : <></>
}

export default Map