import React from "react";
import {SocketContext} from './common';
import './App.css';
import rules from './rules.jpeg'
import {OtherPlayers} from './OtherPlayers';
import {SelfPlayer} from './SelfPlayer';


import {
  PopupboxManager,
  PopupboxContainer
} from 'react-popupbox';
import "react-popupbox/dist/react-popupbox.css"

class GameRoom extends React.Component {
    static contextType = SocketContext;

    constructor(props) {
        super(props);
        this.state = {
            game_state: [{
                name: '<username>',
                cards: [],
                is_self: true,
                active_user: false}],
            username: '<username>',
            last_discarded_card: {'suit': 'DISCARD', 'value': 'DISCARD'},
            action: {target: 'ready',
                     text: 'Ready to Start',
                     disabled: false},
            room_and_token: undefined

        };
    }

    componentDidMount() {
        this.context.emit('joined_room', {'user_token': this.props.token, 'roomid': this.props.roomid})
        this.context.on("token2username", (data) => this.setState({username: data}))
        this.context.on("update_button", (data) => this.setState({action: data}))
        this.context.on("game_state", (json) => {
            console.log(json);
            this.setState(json)});
    }

    render() {

        const non_self_users = []
        var self_user = false

        for (const user of this.state.game_state) {
            if (user.is_self) {
                self_user = user
            } else {
                non_self_users.push(user)
            }
        }

        return <div className="game">
            <Header roomid={this.props.roomid}/>
            <div className="row">
                <div className="column_left">
                    <div className="OtherPlayers">
                        <OtherPlayers users={non_self_users} token={this.state.room_and_token}/>
                    </div>
                    <div className="SelfPlayer">
                        <SelfPlayer user={self_user}/>
                    </div>

                </div>
                <div className="column_right">
                    <Napkin />
                    <ActionButton action={this.state.action} token={this.state.room_and_token}/>

                </div>
            </div>
        </div>
    }
}

class Napkin extends React.Component {
    openPopupbox() {
      const content = <img src={rules} alt="Rules" width="300px"/>
      PopupboxManager.open({
        content,
        config: {
          titleBar: {
            enable: true,
            text: 'Courtesy of Sarah!'
          },
          fadeIn: true,
          fadeInSpeed: 500
        }
      })
    }

    render() {
      return (
        <div className="Napkin" onClick={this.openPopupbox}>
            Click here for Rules
          <PopupboxContainer />
        </div>
      )
    }

}


class ActionButton extends React.Component {
    static contextType = SocketContext;
    render() {
        return <div className="ActionButton"><button onClick={() => {
            this.context.emit(this.props.action.target, this.props.token)
        }} disabled={this.props.action.disabled}>
            {this.props.action.text} </button></div>
    }
}


function Header(props) {
    return <div>Welcome to room {props.roomid}.</div>
}


export default GameRoom;
