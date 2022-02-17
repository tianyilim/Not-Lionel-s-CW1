import { useState, useEffect, React } from 'react'

function CheckInOut() {
    const [checked, setChecked] = useState(false);

    const CheckIn = () => {
        // hardcoded lock info rn
        const msg = {
            lock_postcode: 'SW72AZ',
            lock_cluster_id: 1, 
            lock_id: 1,
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
        // hardcoded lock info rn
        const msg = {
            user: 'token'
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
        // if (checked) CheckOut();
        //     else CheckIn();
        if (!checked) CheckIn();
        else if (auth) {
            CheckOut();
            setAuth(false);
        }

        setChecked(!checked);
        setSerialKey(tmpSerialKey);
    }

    const InputSubmit = () => {};
    const InputOnChange = (event) => {
        // check if event.target.value meets the serial key format
        setTmpSerialKey(event.target.value);
    };
    const [serialKey, setSerialKey] = useState('');
    const [tmpSerialKey, setTmpSerialKey] = useState('')

    // keep checking for udpates to see is user authentication needed
    const [auth,setAuth] = useState(false);
    const update = async() => {
        const msg = {
            user: 'token'
        }
        fetch('http://localhost:5000/usrauthen',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => response.json())
        .then(response => {
            setAuth(response.state);
            console.log(response.state);
        })
    }

    useEffect(() => {
        update();
        setInterval(update,1000)
    },[])


    return (
        <div>
            <form onSubmit={InputSubmit} className='CenterText SerialKeyText'>
                <label>
                    Serial Key:
                    <input 
                        type='text' onChange={InputOnChange}
                        placeholder={checked ? serialKey : ''}
                        disabled={checked ? true : false }
                        style={{fontSize:'20px'}}
                    />
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