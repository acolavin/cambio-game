import React from "react";
import {Cards} from './Cards';


class OtherPlayers extends React.Component {
    render() {
        return this.props.users.map((user) =>
            <div key={user.name}>
                <PlayerBox name={user.name}
                         cards={user.cards}
                         active={user.active_user}
                         token={this.props.token}
                />
            </div>)
    }
}

class PlayerBox extends React.Component {
    render() {
        let userbox_style = "PlayerBox"
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

export {
    OtherPlayers, PlayerBox
}