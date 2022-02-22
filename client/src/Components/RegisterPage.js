import { useState, React } from 'react'
import sha256 from 'crypto-js/sha256';
import hmacSHA512 from 'crypto-js/hmac-sha512';
import Base64 from 'crypto-js/enc-base64';

function RegisterPage() {
    const [data,setData] = useState({
        "name": "",
        "username": "",
        "email":"",
        "pw":""
    })

    const [showPw, setShowPw] = useState(false);

    const [correctPw, setCorrectPw] = useState(true);
    const ConfirmPassward = (event) => {
        if (data.pw !== "" && event.target.value !== data.pw)
            setCorrectPw(false);
        else setCorrectPw(true);
    }

    const Register = () => {
        console.log(data);

        // check whether all data are input correctly
        if (data.name === "" || data.username === "" || data.email === "" || data.pw === "") {
            alert("WRONG!");
            return;
        } else if (!correctPw) {
            alert("WRONT PW!");
            return;
        }
    }

    // const message = sha256("123" + "Message")
    // console.log(Base64.stringify(hmacSHA512(message,"Key")))

    return(
        <div>
            <div className='RegisterForm'>
                <form className='CenterText'
                    style={{width: '100%'}}
                >
                    <label>
                        <br/>
                        Full Name: <br/>
                        <input 
                            className='RegisterInput' type='text' 
                            onChange={ (event) => {setData({...data, "name": event.target.value})} }
                        />
                        <br/>

                        <br/>
                        Username: <br/>
                        <input 
                            className='RegisterInput' type='text' 
                            onChange={ (event) => {setData({...data, "username": event.target.value})} } 
                        />
                        <br/>

                        <br/>
                        Email Address: <br/>
                        <input 
                            className='RegisterInput' type='text' 
                            onChange={ (event) => {setData({...data, "email": event.target.value})} } 
                        />
                        <br/>

                        <br/>
                        Password: <br/>
                        <input 
                            className='RegisterInput' type={showPw ? 'text' : 'password' }
                            onChange={ (event) => {setData({...data, "pw": event.target.value})} }
                        />
                        <br/>

                        <br/>
                        Confirm Password: <br/>
                        <input 
                            className='RegisterInput' type={showPw ? 'text' : 'password' } 
                            onChange={ConfirmPassward} 
                        />

                        <div>
                            <input 
                                type='checkbox'
                                onChange={() => {setShowPw(!showPw)}}
                            />
                            Show Passward
                        </div>

                    </label>
                </form>

                <div className='CenterText'
                    style={{color:'red'}}
                >
                    {correctPw ? "" : "Please confirm passward!"}
                </div>

                <div style={{display:'flex'}}>
                    <button className='CenterText'
                        style={{marginTop: '30px'}}
                    >
                        <a href="/login"
                            style={{textDecoration: 'none', color: 'black'}}
                        >
                            Log In
                        </a>
                    </button>
                    <button className='CenterText' 
                        onClick={Register}
                        style={{marginTop: '30px',}}
                    >
                        Register
                    </button>
                </div>

                <br/>
            </div>
        </div>
    )
}

export default RegisterPage