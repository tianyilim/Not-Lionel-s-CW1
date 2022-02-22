import { useState, useEffect, React } from 'react'

function SingleInfo({item}) {
    return(
        <div className='SingleInfo'>
            Name: {item.bike_name} <br/>
            Serial Number: {item.bike_sn}
        </div>
    )
}

function BikeInfo({items}) {
    console.log(items);
    return(
        <div className=''>
            {items.map((item,index) => {
                // console.log(item)
                return (
                    <SingleInfo key={index} item={item} />
                )
            })}
        </div>
    )
}

export default BikeInfo