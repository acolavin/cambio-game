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
            <form onSubmit={this.handleSubmit}>
                <label>
                    Username:
                    <input type="text" name="username" value={this.state.username} onChange={this.handleChange}/>
                </label>
                <label>
                    Room:
                    <input type="text" name="roomid" value={this.state.roomid} onChange={this.handleChange}/>
                </label>
                <input type="submit" value="Submit"/>
            </form>


    );
    }
}


export default Login;