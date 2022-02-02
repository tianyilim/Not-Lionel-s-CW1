import { BiMenu } from 'react-icons/bi';
import { IconContext } from 'react-icons';

function Header({onClick, showSidebar}) {
    return (
        <div className= {showSidebar ? 'Header' : 'Null'}>
            <div className='MenuIcon'>
            <IconContext.Provider value={{size: '2em'}}>
                <div style={{marginLeft: 'auto', marginRight: 'auto', marginTop: 'auto', marginBottom: 'auto'}}>
                    <BiMenu onClick={onClick}/>
                </div>
            </IconContext.Provider>
            </div>
        </div>
    )
}

export default Header