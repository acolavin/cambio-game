import React from "react";
import {SocketContext} from "./common";

class Cards extends React.Component {
    render() {
        return this.props.cards.map((card, index) =>
            <div key={index}>
                <Card suit={card.suit} value={card.value} id={card.id} highlight={card.highlight} token={this.props.token}/>
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

    constructor(props) {
        super(props);

        // This binding is necessary to make `this` work in the callback
        this.state = {highlight_done: this.props.highlight ? ' item-highlight' : ''}
        this.handleClick = this.handleClick.bind(this);
  }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (this.props.id !== prevProps.id) {
            this.setState({highlight_done: this.props.highlight ? ' item-highlight' : ''})
        }
    }

    handleClick(e) {
        e.preventDefault();
        console.log('The card ' + this.props.id  + ' was clicked.');
        if(this.props.func) {
            this.props.func(this.props)
        } else {
            console.log(this.props)
            this.context.emit("default_card_action", {...this.props.token, card_id: this.props.id})
        }

    }



    render() {
        if (this.state.highlight_done !== '') {
            setTimeout(() => {
                this.setState({highlight_done: ''})
            }, 500)

        }

        return <div className={"Card " + this.getClass(this.props.suit) + this.state.highlight_done}
                    onClick={this.handleClick}>
            <div className="CardLabel CardLabel-topLeft">
                {this.getValue(this.props.value)}{this.getSuit(this.props.suit)}
            </div>
            <div className="CardLabel CardLabel-bottomRight">
                {this.getValue(this.props.value)}{this.getSuit(this.props.suit)}
            </div>
        </div>
    }
}

export { Card, Cards }