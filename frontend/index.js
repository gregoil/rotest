import React from "react";
import ReactDOM from "react-dom";
import {Provider, connect} from "react-redux";

import Data from "./components/resource";
import store from "./store";
import {updateResourcesData, updateDisplayList} from "./store/actions/data_actions";
import { CallbackWebSocket } from "./websocket";

import "./index.css";

class App extends React.Component {
    constructor(props) {
        super(props);
        new CallbackWebSocket((data)=>{
            console.log(data);
            switch (data.event_type) {
                case "resource_updated":
                case "initialize-cache":
                    this.props.updateResourcesData(data.content);
                    break;

                case "initialize-display-list":
                    this.props.updateDisplayList(data.content);
                    break;

                default:
                    console.log(`can't route the event: ${data.event_type}`)
                    break;
            }

        });
    }

    render() {
        const datas = [];
        if (this.props.cache.resources["TestClassData"]) {
            for (let data of Object.values(this.props.cache.resources["TestClassData"])) {
                datas.push(<Data key={data.id} id={data.id} cache_type="TestClassData"/>)
            }
        }

        return (
        <div className="App">
            <div className="DatasContainer">
                {datas}
            </div>
        </div>);
    }
}

const mapStateToProps = (state) => ({
    cache: state.cache
});
const mapDispatchToProps = dispatch => ({
    updateResourcesData: (data) => dispatch(updateResourcesData(data)),
    updateDisplayList: (data) => dispatch(updateDisplayList(data))
});
const AppRenderer = connect(mapStateToProps, mapDispatchToProps)(App);
ReactDOM.render(
        <Provider store={store}>
            <AppRenderer/>
        </Provider>
    , document.getElementById("App"));
