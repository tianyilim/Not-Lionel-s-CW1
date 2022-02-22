import { useState, useEffect, React } from 'react'
import { useSearchParams } from "react-router-dom";

import PromptLogin from './PromptLogin.js';

function CheckInOut({getToken, setReturn}) {
    let [searchParams, setSearchParams] = useSearchParams();
    let params = searchParams.get("serialKey") === null ? [] : searchParams.get("serialKey").split(' ');

    const usrname = getToken();
    if (usrname === null) {
        let query = params.length ? "?serialKey=" + params[0] + "+" + params[1] : '';
        setReturn('/checkin'+query)
    }

    const [checked, setChecked] = useState(false);
    const [awaiting, setAwait] = useState(false);

    const [bicycle, setBicycle] = useState([])

    const [bicycleSN, setBicycleSN] = useState('');

    const CheckIn = () => {
        setAwait(true);

        const msg = {
            lock_postcode: tmpSerialKeyPostCode.toUpperCase(),
            lock_cluster_id: tmpSerialKeyCluster, 
            lock_id: tmpSerialKeyID,
            user: usrname,
            bike_sn: bicycleSN,
        }

        fetch('http://localhost:5000/checkin',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => response.json())
        .then(response => {
            if (response.state) setChecked(true);
            // TODO: warn unsuccessful
            else {
                alert("Unsuccessfuly Login")
            }
            setAwait(false);
        })
    }

    const CheckOut = () => {
        const msg = {
            lock_postcode: serialKey.PostCode,
            lock_cluster_id: serialKey.Cluster, 
            lock_id: serialKey.ID,
            user: usrname, // not needed
        }

        fetch('http://localhost:5000/checkout',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        })

        // any confirmation needed?
        setChecked(false);
    }

    const ButtonOnClick = () => {
        if (!checked) {
            if (tmpSerialKeyPostCode === '' || tmpSerialKeyCluster === '' || tmpSerialKeyID === '') {
                alert("Please enter all details");
                return;
            }

            if (tmpSerialKeyPostCode.split(' ').length !== 1) {
                alert("Please remove whitespaces in Postcode");
                return;
            }

            CheckIn();
            setSerialKey({
                PostCode: tmpSerialKeyPostCode,
                Cluster: tmpSerialKeyCluster,
                ID: tmpSerialKeyID
            });
        }

        else {
            CheckOut();
            setSerialKey({
                PostCode: '',
                Cluster: '',
                ID: ''
            });
        }
        
    }

    const [serialKey, setSerialKey] = useState({
        PostCode: '',
        Cluster: '',
        ID: ''
    });
    const [tmpSerialKeyPostCode, setTmpSerialKeyPostCode] = useState(params.length ? params[0] : '')
    const [tmpSerialKeyCluster, setTmpSerialKeyCluster] = useState(params.length ? params[1] : '')
    const [tmpSerialKeyID, setTmpSerialKeyID] = useState('')

    const InputSubmit = () => {};
    const InputOnChangePostCode = (event) => {
        // check if event.target.value meets the serial key format
        setTmpSerialKeyPostCode(event.target.value);
    };
    const InputOnChangeCluster = (event) => {
        // check if event.target.value meets the serial key format
        setTmpSerialKeyCluster(event.target.value);
    };
    const InputOnChangeID = (event) => {
        // check if event.target.value meets the serial key format
        setTmpSerialKeyID(event.target.value);
    };
    
    // keep checking for udpates to see is user authentication needed
    // const [auth,setAuth] = useState(false);
    // const update = async() => {
    //     const msg = {
    //         user: usrname
    //     };
    //     fetch('http://localhost:5000/usrauthen',{
    //         method: 'POST',
    //         headers: {
    //             'Content-type': 'application/json',
    //         },
    //         body: JSON.stringify(msg),
    //     }).then(response => response.json())
    //     .then(response => {
    //         setAuth(response.state);
    //     })
    // }

    const intial_fetch = () => {
        // console.log("initial fetch")

        const msg = {
            username: usrname
        };
        fetch('http://localhost:5000/usrinfo',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => response.json())
        .then(response => {
            setChecked(response.checked);
            if (response.checked) {
                setSerialKey({
                    PostCode: response.postcode,
                    Cluster: response.cluster,
                    ID: response.id,
                });
                setBicycleSN(response.bike_sn)
            }
        })

        fetch('http://localhost:5000/usrbike',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg)
        }).then(response => response.json())
        .then(response => {
            setBicycle(response);
        })
    }

    useEffect(() => {
        // update();
        intial_fetch();
        // setInterval(update,1000)
    },[])


    return (usrname !== null) ? ( 
        <div>
            <form onSubmit={InputSubmit} className='CenterText SerialKeyText'>
                <label>
                    Serial Key: <br/>
                    <div
                        style={{display: 'flex'}}
                    >
                        <input 
                            className='SerialKey'
                            type='text' onChange={InputOnChangePostCode}
                            value={tmpSerialKeyPostCode}
                            placeholder={checked ? serialKey.PostCode : 'Postcode'}
                            disabled={checked ? true : false }
                            style={{fontSize:'20px', 
                                textTransform: tmpSerialKeyPostCode==='' ? 'none' :  'uppercase'
                            }}
                        />
                        -
                        <input 
                            className='SerialKey'
                            type='text' onChange={InputOnChangeCluster}
                            value={tmpSerialKeyCluster}
                            placeholder={checked ? serialKey.Cluster : 'Cluster ID'}
                            disabled={checked ? true : false }
                            style={{fontSize:'20px'}}
                        />
                        -
                        <input 
                            className='SerialKey'
                            type='text' onChange={InputOnChangeID}
                            placeholder={checked ? serialKey.ID : 'ID'}
                            disabled={checked ? true : false }
                            style={{fontSize:'20px'}}
                        />
                    </div>
                </label>
            </form>
            <br/>

            <div className='CenterText'>
                <select
                    style={{width: '80vw',
                        fontSize: '20px',
                        paddingLeft: '5px',
                        color: '#707070'
                    }}
                    defaultValue={bicycleSN}
                    onChange={ (event) => setBicycleSN(event.target.value) }
                    disabled={checked}
                >
                    <option value=''  disabled hidden>Bicycle</option>
                    {bicycle.map((item,index) => {
                        return(
                            <option key={index} value={item.bike_sn}>{item.bike_name}</option>
                        )
                    })}
                </select>
            </div>

            <button 
                className={'CheckInOut ' + 
                    (awaiting ? 'CheckedButton' : (checked ? 'CheckOutButton' : 'CheckInButton'))
                }
                onClick={ButtonOnClick}
                disabled={awaiting ? true : false }
            >
                {checked ? 'Check Out': 'Check In'}
            </button>

            <div className='CenterText'
                style={{marginTop: '20px'}}
            >
                {checked ? 'Report Stolen' : ''}
            </div>
        </div>
    ) : <PromptLogin />
}

export default CheckInOut