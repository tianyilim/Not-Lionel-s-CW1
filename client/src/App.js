import './App.css';

import { BrowserRouter, Route, Routes , Link } from 'react-router-dom'
import { BsFillHouseDoorFill,BsFillPersonFill,BsFillLockFill } from 'react-icons/bs'
import { IconContext } from 'react-icons';

import Map from './Components/Map.js'
import CheckInOut from './Components/CheckInOut.js';
import RegisterPage from './Components/RegisterPage.js';
import LoginPage from './Components/LoginPage.js';
import Profile from './Components/Profile.js';
import ReportStolen from './Components/ReportStolen.js';

function App() {
  const setToken = (username) => {
    sessionStorage.setItem('username', JSON.stringify(username));
  }

  // return null if username not set / not yet login
  const getToken = () => {
    const token = JSON.parse(sessionStorage.getItem('username'));
    return token;
  }

  const removeToken = () => {
    sessionStorage.removeItem('username');
  }
  const setReturn = (url) => {
    sessionStorage.setItem('returnURL', JSON.stringify(url));
  }

  const getReturn = () => {
    const token = JSON.parse(sessionStorage.getItem('returnURL'));
    sessionStorage.removeItem('returnURL');
    return token;
  }


  const MenuBar = [{
    name: 'CheckInOut',
    link: '/checkin',
    icon: <BsFillLockFill />
  },{
    name: 'Home',
    link: '/',
    icon: <BsFillHouseDoorFill />
  },{
    name: 'Profile',
    link: '/profile',
    icon: <BsFillPersonFill />
  }]


  return (
    <BrowserRouter>
      <div
        style={{display:'block', height:'100%'}}
      >

        <div>
          <Routes >
            <Route exact path="/" element={<Map/>} />
            <Route exact path="/checkin" element={<CheckInOut getToken={getToken} setReturn={setReturn} />} />
            <Route exact path="/register" element={<RegisterPage/>} />
            <Route exact path="/profile" element={<Profile getToken={getToken} setReturn={setReturn} removeToken={removeToken} />} />
            <Route exact path="/login" element={<LoginPage setToken={setToken} getReturn={getReturn} />} />
            <Route exact path="/reportstolen" element={<ReportStolen getToken={getToken} setReturn={setReturn} />} />
          </Routes >
        </div>
        
        <div className='MenuBar'>
          {MenuBar.map((item,index) => {
            return(
              <div>
                <div key={index} className='CenterText MenuBarIcon'>
                  <Link to={item.link}>
                    <IconContext.Provider
                      value={{size: '2em', color: 'black'}}
                    >
                      {item.icon}
                    </IconContext.Provider>
                  </Link>
                </div>
              </div>
            )
          })}
        </div>

      </div>
    </BrowserRouter>
  );
}

export default App;
