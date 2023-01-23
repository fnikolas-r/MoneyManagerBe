import React from 'react';
import axios from "axios";
const trc = axios.create({
    baseURL:"http://localhost:8000/api/akun-duit/",
})

class AkunList extends React.Component{
    state = {
        myAccount : []
    }
    constructor() {
        super();
        trc.get('').then(res=>this.setState({myAccount:res.data})).catch(
            err=>console.log(err)
        )
    }
    render(){
       return <div>
           {this.state.myAccount.map(acc=><div key={acc.id}>{acc.id}</div>)}
       </div>;
    }
}

export default AkunList;