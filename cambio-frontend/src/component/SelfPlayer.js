import React from "react";
import {SocketContext} from "./common";
import {PlayerBox} from './OtherPlayers';

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
            }
        }

        this.state = self_user
    }

    render() {
        return <div>
            <div>
                <PlayerBox name={this.props.user.name}
                           cards={this.props.user.cards}
                           active={this.props.user.active_user}
                           token={this.props.token}/>
            </div>
        </div>
    }


}

export { SelfPlayer }