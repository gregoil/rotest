import React from "react";
import ReactDOM from "react-dom";
import {Provider} from "react-redux";

import { TextField } from "./components/fields/text_field";
import store from "./store";

import "./index.css";

export class App extends React.Component {
    constructor(props) {
        super(props);
    }
    render() {
        return (
        <div className="App">
            <TextField name="Field 1" value="LOL"/>
        </div>);
    }
}

ReactDOM.render(
        <Provider store={store}>
            <App/>
        </Provider>
    , document.getElementById("App"));
