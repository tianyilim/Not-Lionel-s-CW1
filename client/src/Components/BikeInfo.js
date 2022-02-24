import { useState, useEffect, React } from 'react';
import Popup from 'reactjs-popup';
import { FiEdit, FiPlusSquare } from 'react-icons/fi';
import { IconContext } from 'react-icons';

function SingleInfo({ item, usrname}) {

    const [data,setData] = useState({
        bike_name: item.bike_name,
        bike_sn: item.bike_sn,
    })

    const onSubmit = (close) => {
        if (item === data) {
            close();
            return;
        }
        if (data.bike_sn === '' || data.bike_name==='') return;

        const msg = {
            user: usrname,
            state: item.bike_sn==='' ? 'insert' : 'update',
            original: item,
            new: data,
        }
        fetch('http://'+process.env.REACT_APP_IP+':5000/bikeupdate',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg)
        }).then( () => { 
            close(); 
            window.location.reload(false);
        })
    }

    const onDelete = (close) => {
        if (!window.confirm("Confirm deleting the bike entry? Changes cannot be reversed.")) return;

        const msg = {
            user: usrname,
            state: 'delete',
            original: item,
            new: {},
        }
        fetch('http://' + process.env.REACT_APP_IP + ':5000/bikeupdate',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg)
        }).then( () => { 
            close(); 
            window.location.reload(false);
        })
    } 

    return data !== null ? (
        <div className='SingleInfo'>
            { (item.bike_sn !== '') ?
                <div>
                    <b>Name</b>: {item.bike_name} <br/>
                    <b>Serial Number</b>: {item.bike_sn} 
                </div> :
                <div> Add New Bicycle </div>
            }
            
            <Popup trigger={
                    <div
                        style={{
                            alignSelf: 'flex-end', 
                            marginRight: '7px',
                            marginTop: 'auto',
                            marginBottom: 'auto'
                        }}
                        >
                        <IconContext.Provider
                            value={{size: '1.5em', color: 'black'}}
                            >
                            { (item.bike_sn !== '') ?
                                <FiEdit />:
                                <FiPlusSquare />
                            }
                            
                        </IconContext.Provider>
                    </div>
                }
                modal
                nested 
            >
                { close => (
                    <div className='Popup'
                        style={{width: '80vw'}}
                    >
                        <button className="close" onClick={close}>
                            &times;
                        </button>
                        <div className='header'>Edit Bicycle Info</div>
                        <div className='content'>
                            <label>
                                Name: <br/>
                                <input 
                                    className='PopupInput'
                                    type='text'
                                    value={data.bike_name}
                                    onChange = { (event) => setData({...data, bike_name: event.target.value})}
                                />
                                <br/>

                                Serial Number: <br/>
                                <input 
                                    className='PopupInput'
                                    type='text'
                                    value={data.bike_sn}
                                    onChange = { (event) => setData({...data, bike_sn: event.target.value})}
                                />
                                <br/> <br/>

                                <div
                                    style={{display: 'flex'}}
                                >
                                    <button className='CenterText'
                                        onClick={() => {onSubmit(close)}}
                                    >
                                        Save
                                    </button>
                                    <button className='CenterText'
                                        onClick={() => {onDelete(close)}}
                                    >
                                        Delete
                                    </button>
                                </div>
                            </label>
                        </div>
                    </div>
                )}
            
            </Popup>
        </div>
    ) : <div></div>
}

function BikeInfo({items, usrname}) {
    return(
        <div className=''
            style={{marginTop: '30px'}}
        >
            {items.map((item,index) => {
                return (
                    <SingleInfo key={index} item={item} usrname={usrname} />
                )
            })}
            <SingleInfo item={{bike_name: '', bike_sn: ''}} usrname={usrname} />
        </div>
    )
}

export default BikeInfo