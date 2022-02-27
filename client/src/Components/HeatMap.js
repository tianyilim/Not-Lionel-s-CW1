import { useState, React, useEffect } from 'react'
import { GoogleMap, HeatmapLayer, useJsApiLoader } from '@react-google-maps/api'
import PropTypes from 'prop-types'

function HeatMap() {
    const { isLoaded } = useJsApiLoader({
        id: 'google-map-script',
        googleMapsApiKey: "AIzaSyDRNQB3_vgwOBfziEHzuLl9fhE4tbbCCEo"
    })
    const containerStyle = {
        height: '100vh'
    };
    const [currentLoc, setCurrentLoc] = useState({ lat: 51.49918363237076, lng: -0.17634013995995976 })

    return isLoaded ? (
        <div>
            <GoogleMap
                id = "map"
                mapContainerStyle={containerStyle}
                center={currentLoc}
                zoom={15}
            >

                <HeatmapLayer 
                    positions={currentLoc}
                />
                
            </GoogleMap>
        </div>
    ) : <></>
}

export default HeatMap