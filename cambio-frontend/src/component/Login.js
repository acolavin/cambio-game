import React from "react";
import {SocketContext} from './common';


class Login extends React.Component {
    static contextType = SocketContext;

    constructor(props) {
        super(props);
        this.state = {
            username: '',
            roomid: '',
        };

        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleChange(event) {
        this.setState({
            [event.target.name]: event.target.value
        });
    }

    handleSubmit(event) {
        let payload = {
                'username': this.state.username,
                'roomid': this.state.roomid
            }
        this.context.emit('propose_to_join', payload)
        event.preventDefault();
    }

    componentDidMount() {
        //this.context.on("connect", () => this.setState({connected: true}));
    }


    render() {
        return (
            <div><div className="PageTitle">Cambio</div>
            <form onSubmit={this.handleSubmit} className="loginForm">

                <label className="loginField">
                    <div className="loginText">Username:</div>
                    <input type="text" name="username" value={this.state.username} onChange={this.handleChange}/>
                </label>
                <label className="loginField">
                    <div className="loginText">Room:</div>
                    <input type="text" name="roomid" value={this.state.roomid} onChange={this.handleChange}/>
                </label>

                <input type="submit" value="Submit" className="loginButton"/>
            </form></div>


    );
    }
}


export default Login;