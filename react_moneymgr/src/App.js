import React from 'react';
import Navbar from "./component/Navbar";
import Sidebar from "./component/Sidebar";
import AkunList from "./keuangan_cmp/AkunList";

class App extends React.Component{

    render(){
  return <div >
      {/*<Sidebar/>*/}
      <AkunList/>
      <Navbar/>

    </div>
  ;
    }
}


export default App;
