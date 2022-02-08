import './App.css';

import { useState } from 'react';

import Header from './Components/Header.js'
import Map from './Components/Map.js'

function App() {
  const [showSidebar, setSidebar] = useState(false);
  const Sidebar = () => setSidebar(!showSidebar);


  return (
    <div>
      {/* <Header onClick={Sidebar} showSidebar={showSidebar}/>
      <nav className={showSidebar ? 'SidebarActive' : 'Sidebar'}>
      </nav> */}

      <Map/>
    </div>

    
  );
}

export default App;
