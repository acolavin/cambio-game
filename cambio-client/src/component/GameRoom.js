import React from "react";
import {SocketContext} from './common';


class GameRoom extends React.Component {
    static contextType = SocketContext;

    constructor(props) {
        super(props);
        this.state = {
            game_state: [{'name':'default', 'cards':[{'suite':'X','value':'Y'}]}],
            username: '<username>',
            action: 'start_game',
        };

    }

    componentDidMount() {
        this.context.emit('joined_room', {'user_token': this.props.token, 'roomid': this.props.roomid})
        this.context.on("token2username", (data) => this.setState({username: data} ));
        this.context.on("game_state", (data) => this.setState({game_state: data } ));
    }


    render() {
        return <div>
            Welcome to room {this.props.roomid}, {this.state.username}.
            <UserBoxes users={this.state.game_state}/>
            <ActionButton active={true} socket={this.context}
                          payload={{'roomid': this.props.roomid}}
                          value={this.state.action} target={this.state.action}/>

        </div>
    }
}

function ActionButton(props) {
    return 	<button onClick={() => {props.socket.emit(props.target, props.payload)}}>
        {props.value}</button>
}


class UserBoxes extends React.Component {
    render() {
        return this.props.users.map((user) =>
            <UserBox name={user.name} key={user.name} cards={user.cards}/>
        )
    }
}

class UserBox extends React.Component {
    constructor(props) {
        super(props);
        this.state = {active: false};
    }

    render() {
        return (
            <div>
                <h3><b> {this.props.name} .</b></h3>
                <Cards cards={this.props.cards}/>
            </div>
        );
    }
}

class Cards extends React.Component {
    render() {
        return this.props.cards.map((card) =>
            <Card key={card.suite + card.value} suite={card.suite} value={card.value}/>
        )
    }
}


function Card(props) {
    return <div>Card {props.index}:<b>{props.value} of {props.suite}s</b></div>
}


export default GameRoom;