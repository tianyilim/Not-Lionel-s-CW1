import { useState, useEffect, React } from 'react'

import PromptLogin from './PromptLogin.js';
import BikeInfo from './BikeInfo.js';

function Profile({getToken, setReturn}) {
    const usrname = getToken();
    if (usrname === null) {
        setReturn('/profile');
    }

    const [info, setInfo] = useState({
        name: 'name',
        username: 'username',
        email: 'email address'
    })
    const [bicycle, setBicycle] = useState([]);

    const initial_fetch = () => {
        const msg = {
            username: usrname
        };
        fetch('http://'+process.env.REACT_APP_IP+':5000/usrbike',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg)
        }).then(response => response.json())
        .then(response => {
            setBicycle(response);
            // console.log(response)
        })
    }

    useEffect(() => {
        initial_fetch();
    },[])

    return (usrname !== null) ? (
        <div>
            <BikeInfo items={bicycle} usrname={usrname} />
        </div>
    ) : <PromptLogin />
}

export default Profile