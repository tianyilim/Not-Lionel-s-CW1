import React from 'react'
import { GoogleMap, useJsApiLoader } from '@react-google-maps/api';

const containerStyle = {
  height: '100vh'
};

const center = {
  lat: 51.49918363237076,
  lng: -0.17634013995995976
};

function Map() {
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: "AIzaSyDRNQB3_vgwOBfziEHzuLl9fhE4tbbCCEo"
  })

  const [map, setMap] = React.useState(null)

  const onLoad = React.useCallback(function callback(map) {
    const bounds = new window.google.maps.LatLngBounds();
    map.fitBounds(bounds);
    setMap(map)
  }, [])

  const onUnmount = React.useCallback(function callback(map) {
    setMap(null)
  }, [])

  return isLoaded ? (
    <GoogleMap
        mapContainerStyle={containerStyle}
        center={center}
        zoom={250}
        onLoad={onLoad}
        onUnmount={onUnmount}
    >
        { /* Child components, such as markers, info windows, etc. */ }
        <></>
    </GoogleMap>
  ) : <></>
}

export default Map