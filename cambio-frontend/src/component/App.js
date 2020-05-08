import React from 'react';
import './App.css';
import GameRoom from './GameRoom';
import { SocketContext } from './common';
import Login from './Login';


class App extends React.Component {
    static contextType = SocketContext

    constructor(props) {
        super(props);
        this.state = {page: 'login', connected: false, token: undefined};
    }

    componentDidMount() {
        this.context.on("enter_room", (json) => this.setState({page: 'game', ...json}));
        this.context.on("connect", () => this.setState({connected: true}));
    }

    render() {
        return (
            <div className="App">
                {
                    this.state.page === 'login' && <Login />
                }
                {
                    this.state.page === 'game' && <GameRoom token={this.state.token} roomid={this.state.roomid} />
                }
                <div className="Status">Connected ? {this.state.connected.toString()}</div>
                <div className="GameLog" ><GameLog logs={["This is the logs"]}/></div>
            </div>
        );
    }
}

class GameLog extends React.Component {
    static contextType = SocketContext;

    constructor(props) {
        super(props);
        this.state = {logs: props.logs};
    }

    componentDidMount() {
        this.context.on("game_log", (data) => this.setState((state) => {
            return {logs: state.logs.concat(data)}
        }))
    }

    render() {
        return <textarea className="logs" value={this.state.logs.reverse().join('\n')} readOnly={true}>

            </textarea>

    }
}
export default App;
