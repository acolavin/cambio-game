import React from "react";
import {SocketContext} from './common';
import './App.css';
import rules from './rules.jpeg'

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
                    <div className="UserBoxes">
                        <UserBoxes users={non_self_users} token={this.state.room_and_token}/>
                    </div>
                    {
                        self_user ?
                            <div className="self_view">
                            <div>
                                <UserBox name={self_user.name}
                                         cards={self_user.cards}
                                         active={self_user.active_user}
                                         token={this.state.room_and_token}/>
                            </div>
                                <ActiveCard card={self_user.active_card}
                                            token={this.state.room_and_token}/>
                                <Deck token={this.state.room_and_token} />
                                <Discard card={this.state.last_discarded_card}/>

                            </div>
                            :
                            <div>
                            <div className="self_view">
                                <UserBox name={this.state.username}
                                         cards={[]}
                                         token={this.state.room_and_token}
                                         active={false}/>
                            </div>
                                <ActiveCard card={[]} token={this.state.room_and_token}/>
                                <Deck token={this.state.room_and_token} />
                                <Discard card={this.state.last_discarded_card}/>

                            </div>
                    }


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
    constructor(props) {
        super(props);
        this.state = props
    }
    static contextType = SocketContext;
    componentDidMount() {
        this.context.on("update_button", (data) => this.setState({action: data}));
    }
    render() {
        return <div className="ActionButton"><button onClick={() => {
            this.context.emit(this.state.action.target, this.props.token)
        }} disabled={this.state.action.disabled}>
            {this.state.action.text} </button></div>
    }
}


function Header(props) {
    return <div>Welcome to room {props.roomid}.</div>
}


class UserBoxes extends React.Component {
    render() {
        return this.props.users.map((user) =>
            <div key={user.name}>
                <UserBox name={user.name}
                         cards={user.cards}
                         active={user.active_user}
                         token={this.props.token}
                />
            </div>)
    }
}

class UserBox extends React.Component {
    render() {
        let userbox_style = "UserBox"
        if(this.props.active) {
            userbox_style += " ActiveUser"
        }
        return (
            <div className={userbox_style}>
                <div className="UserBoxLabel"><h3><b> {this.props.name} .</b></h3></div>
                <div className="CardBox">
                    <Cards cards={this.props.cards}/>
                </div>
            </div>
        );
    }
}

class Cards extends React.Component {
    render() {
        return this.props.cards.map((card) =>
            <div key={card.id}>
                <Card suit={card.suit} value={card.value} id={card.id}/>
            </div>
        )
    }

}


class Card extends React.Component {
    static contextType = SocketContext;
    getClass(suit) {
        switch (suit) {
            case "Spade":
                return "card-black"
            case "Club":
                return "card-black"
            case "Heart":
                return "card-red"
            case "Diamond":
                return "card-red"
            default:
                return "card-black"
        }
    }

    getValue(value) {
        switch (value) {
            case "King":
                return "K"
            case "Queen":
                return "Q"
            case "Jack":
                return "J"
            case "Ace":
                return "A"
            case "HIDDEN":
                return "?";
            case "DISCARD":
                return "Discard"
            default:
                return value
        }
    }

    getSuit(value) {
        switch (value) {
            case "Club":
                return "♣"
            case "Spade":
                return "♠"
            case "Diamond":
                return "♦"
            case "Heart":
                return "♥"
            case "DISCARD":
                return ""
            case "HIDDEN":
                return "?";
            default:
                return value
        }
    }


    handleClick(e) {
        e.preventDefault();
        console.log('The card ' + this.props.id  + ' was clicked.');
    }


    render() {
        return <div className={"Card " + this.getClass(this.props.suit)} onClick={this.handleClick}>
            <div className="CardLabel CardLabel-topLeft">
                {this.getValue(this.props.value)}{this.getSuit(this.props.suit)}
            </div>
            <div className="CardLabel CardLabel-bottomRight">
                {this.getValue(this.props.value)}{this.getSuit(this.props.suit)}
            </div>
        </div>
    }
}


class ActiveCard extends React.Component {
    static contextType = SocketContext;
    render() {
        let card = this.props.card
        let socket = this.context
        return <div>
            {
            this.props.card
                ?
                <div>
                    <Card suit={card.suit} value={card.value}/>
                    <button onClick={() => {
                        socket.emit(card.action, card.token)
                    }}>{ card.action_string }</button>
                </div>
                :
                <div>
                    <Card suit='' value=''/>
                    <button disabled={true}>[Disabled]</button>
                </div>
            }
        </div>
    }

}

class Deck extends React.Component {
    static contextType = SocketContext;
    render() {
        let socket = this.context
        return <div onClick={() => {
                    socket.emit('draw_card', this.props.token)

        }}><Card suit='Deck' value='' id="deck"/></div>


    }

}

function Discard(props) {
    return <div>
            {
            props.card
                ?
                <div>
                    <Card suit={props.card.suit} value={props.card.value}/>
                </div>
                :
                <div>
                    <Card suit='DISCARD' value='DISCARD'/>
                </div>
            }
        </div>


}

export default GameRoom;