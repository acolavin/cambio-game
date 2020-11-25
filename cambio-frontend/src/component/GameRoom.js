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

import {Card} from "./Cards";

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
            last_discarded_card: undefined,
            active_card: [],
            action: {target: 'ready',
                     text: 'Ready to Start',
                     disabled: false},
            room_and_token: {room: undefined,
                token: undefined
            }

        };
    }

    componentDidMount() {
        this.context.emit('joined_room', {'user_token': this.props.token, 'roomid': this.props.roomid})
        this.context.on("token2username", (data) => this.setState({...this.state, username: data}))
        this.context.on("update_button", (data) => this.setState({...this.state, action: data}))
        this.context.on("update_active_card", (data) => this.setState({...this.state, active_card: data}))
        this.context.on("game_state", (json) => {
            console.log(json)
            this.setState({...this.state, ...json})
        });
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
                        <SelfPlayer user={self_user} token={this.state.room_and_token}/>
                    </div>

                </div>
                <div className="column_right">

                    <ActionButton action={this.state.action} token={this.state.room_and_token}/>
                    <div className="decks">
                        <Deck token={this.state.room_and_token}/>
                        <Discard card={this.state.last_discarded_card ?
                            this.state.last_discarded_card : {suit: '', value:'', highlight: false}}
                                 token={this.state.room_and_token}/>
                    </div>
                    <div className="activeCard">
                        <ActiveCard card={this.state.active_card}
                                    token={this.props.token}/>
                    </div>

                    <Napkin />
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


class Deck extends React.Component {
    static contextType = SocketContext;
    constructor(props) {
        super(props);
        this.handleClick = this.handleClick.bind(this);

    }

    handleClick(e) {
        this.context.emit('draw', this.props.token)
    }

    render() {

        return (
            <Card suit='Deck' value='' id="deck" highlight={false}
                  onClick={this.handleClick} />
        )

    }

}

class Discard extends React.Component {
    static contextType = SocketContext;
    constructor(props) {
        super(props);
        this.handleClick = this.handleClick.bind(this);

    }

    handleClick(e) {
        this.context.emit('discard_card', this.props.token)
    }

    render() {

        return <div>
        {
            this.props.card.suit !== ''
                ?

                    <Card suit={this.props.card.suit}
                          value={this.props.card.value}
                          highlight={this.props.card.highlight}
                          id={this.props.card.id}
                          onClick={this.handleClick}
                    />
                :
                    <Card suit='DISCARD' value='DISCARD' highlight={false} onClick={this.handleClick}/>

        }
        </div> }



}

class ActiveCard extends React.Component {
    static contextType = SocketContext;
    render() {
        let card = this.props.card
        let socket = this.context
        return <div className="selfPlayer">
            {
                card
                    ?
                    <div className="actionCard">
                        <Card suit={card.suit} value={card.value}
                              id={card.id} highlight={true} func={() => true}/>
                        <button className="cardButton" onClick={() => {
                            socket.emit(card.action, card.token)
                        }} disabled={card.action_string === ""}>{card.action_string}</button>
                    </div>
                    :
                    <div className="actionCard">
                        <Card suit='' value='' id=''
                              highlight={false} func={() => true}/>
                        <button className="cardButton" disabled={true}>[Disabled]</button>
                    </div>
            }
        </div>
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
    return <div className="PageTitle">Welcome to room {props.roomid}.</div>
}


export default GameRoom;
