import { useState, useEffect, React } from 'react'

function CheckInOut() {
    // TODO
    const [usrname, setUsrname] = useState('token');

    const [checked, setChecked] = useState(false);

    const CheckIn = () => {
        // should also send usrname
        const msg = {
            lock_postcode: tmpSerialKeyPostCode,
            lock_cluster_id: tmpSerialKeyCluster, 
            lock_id: tmpSerialKeyID,
            user: usrname,
        }

        fetch('http://localhost:5000/checkin',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => console.log(response));
    }

    const CheckOut = () => {
        // shoudln't need user: 
        const msg = {
            lock_postcode: serialKey.PostCode,
            lock_cluster_id: serialKey.Cluster, 
            lock_id: serialKey.ID,
            user: usrname,
        }

        fetch('http://localhost:5000/checkout',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => console.log(response));
    }

    const ButtonOnClick = () => {
        if (!checked) {
            if (tmpSerialKeyPostCode === '' || tmpSerialKeyCluster === '' || tmpSerialKeyID === '') return;

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

        else if (auth) {
            CheckOut();
            setAuth(false);
            setSerialKey({
                PostCode: '',
                Cluster: '',
                ID: ''
            });
        }

        setChecked(!checked);
        
    }

    // Serial Key should be stored in the server
    const [serialKey, setSerialKey] = useState({
        PostCode: '',
        Cluster: '',
        ID: ''
    });
    const [tmpSerialKeyPostCode, setTmpSerialKeyPostCode] = useState('')
    const [tmpSerialKeyCluster, setTmpSerialKeyCluster] = useState('')
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
    const [auth,setAuth] = useState(false);
    const update = async() => {
        const msg = {
            user: usrname
        };
        fetch('http://localhost:5000/usrauthen',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => response.json())
        .then(response => {
            setAuth(response.state);
        })
    }

    const intial_fetch = () => {
        console.log("initial fetch")

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
            }
        })
    }

    useEffect(() => {
        update();
        intial_fetch();
        setInterval(update,1000)
    },[])


    return (
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
                            placeholder={checked ? serialKey.PostCode : 'Postcode'}
                            disabled={checked ? true : false }
                            style={{fontSize:'20px'}}
                        />
                        -
                        <input 
                            className='SerialKey'
                            type='text' onChange={InputOnChangeCluster}
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

            <button 
                className={'CheckInOut ' + 
                    (checked ? (auth ? 'CheckOutButton' : 'CheckedButton') : 'CheckInButton')
                }
                onClick={ButtonOnClick}
                disabled={(checked&&!auth) ? true : false }
            >
                {checked ? (auth ? 'Check Out' : 'Checked') : 'Check In'}
            </button>

            <div className='CenterText'
                style={{marginTop: '20px'}}
            >
                {checked ? 'Report Stolen' : ''}
            </div>
        </div>
    )
}

export default CheckInOut