import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './component/App';
import { SocketContext } from './component/common'
import * as serviceWorker from './serviceWorker';
import openSocket from 'socket.io-client';

ReactDOM.render(
  <React.StrictMode>
            <SocketContext.Provider value={ openSocket('localhost:5000') }>
                <App />
            </SocketContext.Provider>
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();