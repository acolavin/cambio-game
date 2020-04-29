import React from "react";
import {SocketContext} from "./common";
import {PlayerBox} from './OtherPlayers';
import {Card} from './Cards';


class SelfPlayer extends React.Component {
    constructor(props) {
        super(props)
        let self_user = props.user
        if(!self_user) {
            self_user = {
                name: '<username>',
                cards: [],
                active: false,
                active_card: [],
                room_and_token: '',
                last_discarded_card: {'suit': 'DISCARD', 'value': 'DISCARD'}
            }
        }

        this.state = self_user
    }


    render() {
        return <div className="self_view">
            <div>
                <PlayerBox name={this.props.user.name}
                           cards={this.props.user.cards}
                           active={this.props.user.active_user}
                           token={this.props.user.room_and_token}/>
            </div>
            <ActiveCard card={this.props.user.active_card}
                        token={this.props.user.room_and_token}/>
            <Deck token={this.state.room_and_token}/>
            <Discard card={this.state.last_discarded_card}/>

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
                        }}>{card.action_string}</button>
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

export { SelfPlayer }