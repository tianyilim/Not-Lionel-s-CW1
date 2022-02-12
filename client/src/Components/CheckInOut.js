import { useState, React } from 'react'

function CheckInOut() {
    const [checked, setChecked] = useState(false);

    const ButtonOnClick = () => {
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
                className={'CheckInOut ' + (checked ? 'CheckOutButton' : 'CheckInButton')}
                onClick={ButtonOnClick}
            >
                {checked ? 'Check Out' : 'Check In'}
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