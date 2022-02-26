import { useState, useEffect, React } from 'react'
import { useNavigate } from 'react-router-dom';

import PromptLogin from './PromptLogin.js';

function ReportStolen({getToken, setReturn}) {
    const navigate = useNavigate();

    const usrname = getToken();
    // or non-users can also report?
    if (usrname === null) {   
        setReturn('/reportstolen');
    }

    const [data, setData] = useState({
        PostCode: '',
        Cluster: null,
        ID: null,
    });
    const [emailFlag, setEmailFlag] = useState(null);

    const [falseAlarm, setFalseAlarm] = useState(false);

    const RealStolen = () => {
        if (data.PostCode === '') {
            alert("We are sorry your bike has been stolen. We have automatically notified the relevant authorities.")
            navigate('/')
        }

        const msg = {
            user: usrname,
            state: 2,
            postcode: data.PostCode,
            cluster: data.Cluster,  
            id: data.ID
        }

        fetch('http://'+process.env.REACT_APP_IP+':5000/stolenstate',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then( () => {
            alert("We are sorry your bike has been stolen. We have automatically notified the relevant authorities.")
            navigate('/')
        })
    }

    const FalseStolen = (x) => {
        if (data.PostCode === '') {
            alert("Thank you for confirming");
            navigate('/');
        }

        const msg = {
            user: usrname,
            state: x ? 1 : 0, // TRUE if bike has removed
            postcode: data.PostCode,
            cluster: data.Cluster,
            id: data.ID
        }

        fetch('http://'+process.env.REACT_APP_IP+':5000/stolenstate',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then( () => {
            alert("Thank you for confirming");
            navigate('/');
        })

        console.log(msg);
    }

    const FalseAlaramStolen = () => {
        if (data.PostCode === '') {
            alert("Thank you for confirming");
            navigate('/');
        }
        setFalseAlarm(true);
    }

    
    const [tmpSerialKeyPostCode, setTmpSerialKeyPostCode] = useState('')
    const [tmpSerialKeyCluster, setTmpSerialKeyCluster] = useState('')
    const [tmpSerialKeyID, setTmpSerialKeyID] = useState('')
    
    const InputOnChangePostCode = (event) => {
        setTmpSerialKeyPostCode(event.target.value);
    };
    const InputOnChangeCluster = (event) => {
        setTmpSerialKeyCluster(event.target.value);
    };
    const InputOnChangeID = (event) => {
        setTmpSerialKeyID(event.target.value);
    };
    
    const onSubmit = (e) => {
        e.preventDefault();
        if (tmpSerialKeyPostCode === '' || tmpSerialKeyCluster === '' || tmpSerialKeyID === '') return;

        const msg = {
            user: '',
            state: 2,
            postcode: tmpSerialKeyPostCode,
            cluster: tmpSerialKeyCluster,
            id: tmpSerialKeyID
        }

        fetch('http://'+process.env.REACT_APP_IP+':5000/stolenstate',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then( () => {
            alert("Thank you for reporting!");
            navigate('/');
        })
    }

    const initial_fetch = () => {
        const msg = {
            username: usrname
        };

        fetch('http://'+process.env.REACT_APP_IP+':5000/usrinfo',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => response.json())
        .then(response => {
            if (response.checked) {
                setData({
                    PostCode: response.postcode,
                    Cluster: response.cluster,
                    ID: response.id,
                });
                setTmpSerialKeyPostCode(response.postcode);
                setTmpSerialKeyCluster(response.cluster);
                setTmpSerialKeyID(response.id);
            } 
            console.log(response)
        })

        fetch('http://'+process.env.REACT_APP_IP+':5000/emailflag',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => response.json())
        .then(response => {
            // TODO: check if not checked in, ignore
            setEmailFlag(response.email_flag)
        })
    }

    useEffect(() => {
        initial_fetch();
    },[])

    return (usrname !== null) ? ( emailFlag ? ( falseAlarm ?
        // when user has claimed to be false alarm 
        // check out for user if needed
        <div className='CenterText ReportStolen'>
            <div className='ReportStolenHeader'>
                <b>Critical Security Alert</b>
            </div>
            <div className='ReportStolenBody'>
                {emailFlag} <br/><br/>
                Please confirm whether you have removed your bike from<br/>
                Lock number: {data.PostCode}-{data.Cluster}-{data.ID} <br/>
                <br/>
            </div>
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    margin: '7px',
                    marginTop: '10px'
                }}
            >
                <button className='ReportStolenBtn'
                    onClick={() => FalseStolen(true)}
                >
                    Yes
                </button>
                <button className='ReportStolenBtn'
                    onClick={() => FalseStolen(false) }
                >
                    No
                </button>
            </div>
        </div> 
        :
        // "home" page user visit when directed by email
        <div className='CenterText ReportStolen'>
            <div className='ReportStolenHeader'>
                <b>Critical Security Alert</b>
            </div>
            <div className='ReportStolenBody'>
                {emailFlag} <br/><br/>
                Unusual behaviour has been detected at the lock you have checked in :<br/>
                Lock number: {data.PostCode}-{data.Cluster}-{data.ID} <br/>
                <br/>
                Did you recently remove your bike from the lock? <br/> <br/>
            </div>

            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    margin: '7px',
                    marginTop: '10px'
                }}
            >
                <button className='ReportStolenBtn'
                    onClick={RealStolen}
                >
                    No, report stolen bicycle
                </button>
                <button className='ReportStolenBtn'
                    onClick={FalseAlaramStolen}
                >
                    Yes, it was me
                </button>
            </div>
        </div>
    ) : (
        // when user does not received an email
        <div className='CenterText ReportStolen'>
            <form className='CenterText ReportStolenBody'>
                <label>
                    Report irregularity at lock: <br/> <br/>
                    Serial Key: <br/>

                    <div
                        style={{display: 'flex'}}
                    >
                        <input 
                            className='ReportStolenInput'
                            type='text' onChange={InputOnChangePostCode}
                            value={tmpSerialKeyPostCode}
                            placeholder={'Postcode'}
                            style={{
                                textTransform: tmpSerialKeyPostCode==='' ? 'none' :  'uppercase'
                            }}
                        />
                        -
                        <input 
                            className='ReportStolenInput'
                            type='text' onChange={InputOnChangeCluster}
                            value={tmpSerialKeyCluster}
                            placeholder={'Cluster ID'}
                        />
                        -
                        <input 
                            className='ReportStolenInput'
                            type='text' onChange={InputOnChangeID}
                            value={tmpSerialKeyID}
                            placeholder={'ID'}
                        />
                    </div>

                    <button className='CenterText'
                        style={{marginTop: '10px'}}
                        onClick={onSubmit}
                    >
                        Report
                    </button>
                </label>
            </form>
        </div>
    )): <PromptLogin />
}

export default ReportStolen