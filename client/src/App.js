import './App.css';

import { useState } from 'react';
import { BrowserRouter, Route, Routes , Link } from 'react-router-dom'
import { BsFillHouseDoorFill,BsFillPersonFill,BsFillLockFill } from 'react-icons/bs'
import { IconContext } from 'react-icons';

import Map from './Components/Map.js'
import CheckInOut from './Components/CheckInOut.js';
import RegisterPage from './Components/RegisterPage.js';;

function App() {
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
    link: 'profile',
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
            <Route exact path="/checkin" element={<CheckInOut/>} />
            <Route exact path="/profile" element={<RegisterPage/>} />
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
