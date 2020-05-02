import React from "react";
import {SocketContext} from "./common";
import {PlayerBox} from './OtherPlayers';
import {Card} from './Cards';


class SelfPlayer extends React.Component {
    static contextType = SocketContext;

    constructor(props) {
        super(props)
        let self_user = props.user
        if(!self_user) {
            self_user = {
                name: '<username>',
                cards: [],
                active: false,
                active_card: [],
                last_discarded_card: {'suit': 'DISCARD', 'value': 'DISCARD'}
            }
        }

        this.state = self_user
    }

    componentDidMount() {
        this.context.on("update_active_card", (data) => this.setState({...this.state, active_card: data}))
    }


    render() {
        return <div className="self_view">
            <div>
                <PlayerBox name={this.props.user.name}
                           cards={this.props.user.cards}
                           active={this.props.user.active_user}
                           token={this.props.token}/>
            </div>
            <ActiveCard card={this.state.active_card}
                        token={this.props.token}/>
                        <div>
                            <Deck token={this.props.token}/>
                        </div>
                        <div>
                            <Discard card={this.props.last_discarded_card} token={this.props.token}/>
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
                        <Card suit={card.suit} value={card.value} id={card.id}/>
                        <button onClick={() => {
                            socket.emit(card.action, card.token)
                        }} disabled={card.action_string === ""}>{card.action_string}</button>
                    </div>
                    :
                    <div>
                        <Card suit='' value='' id=''/>
                        <button disabled={true}>[Disabled]</button>
                    </div>
            }
        </div>
    }

}

class Deck extends React.Component {
    static contextType = SocketContext;

    render() {
        return <Card suit='Deck' value='' id="deck"
        func={() => {this.context.emit('draw', this.props.token)}}/>

    }

}

class Discard extends React.Component {
    static contextType = SocketContext;

    render() { return <div>
        {
            this.props.card
                ?
                    <Card suit={this.props.card.suit} value={this.props.card.value}
                    func={() => {this.context.emit('discard_card', this.props.token)}}/>
                :
                    <Card suit='DISCARD' value='DISCARD'
                          func={() => { this.context.emit('discard_card', this.props.token)}}/>
        }
    </div> }


}

export { SelfPlayer }