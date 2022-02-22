import { useState, React } from 'react'

function LoginPage({setToken}) {
    const [data,setData] = useState({
        username: "",
        pw: "",
    })

    const [showPw, setShowPw] = useState(false);
    const [wrongPw, setWrongPw] = useState(false);

    const Login = (e) => {
        // prevent reloading the page
        e.preventDefault();

        // check password
        // TODO encrypt pw
        const msg = data;
        fetch('http://localhost:5000/login',{
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify(msg),
        }).then(response => response.json())
        .then(response => {
            if (response.state) {
                setToken(msg.username);
                setWrongPw(false);
            } else {
                setWrongPw(true);
                setData({...data, username: ''});
            }
        })
    }

    return (
        <div>
            <div className='RegisterForm'>
                <form className='CenterText'>
                    <label>
                        <br/>
                        Username: <br/>
                        <input
                            className='RegisterInput' type='text'
                            onChange={ (event) => {setData({...data, username: event.target.value})} }
                        />
                        <br/>

                        <br/>
                        Password: <br/>
                        <input
                            className='RegisterInput' type={showPw ? 'text' : 'password'}
                            onChange={ (event) => {setData({...data, pw: event.target.value})} }
                        />

                        <div>
                            <input
                                type='checkbox'
                                onChange={() => {setShowPw(!showPw)}}
                            />
                            Show Passward
                        </div>

                        <div className='CenterText'
                            style={{color:'red'}}
                        >
                            {wrongPw ? "Incorrect password or username." : ""}
                        </div>

                        <button className='CenterText' 
                            onClick={Login}
                            style={{marginTop: '30px',}}
                        >
                            Login
                        </button>

                        <br/>

                    </label>
                </form>
            </div>
        </div>
    )
}

export default LoginPage