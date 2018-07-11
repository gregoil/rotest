import React from "react";
import {connect} from "react-redux";

import {Data} from "../data";
import Lock from "../fields/lock";
import TextField from "../fields/text_field";
//import "./index.css";

//const FIELD_FILTER_LIST = ["group"];
//const DEFAULT_TITLE_COLOR = "#96ff77";

export class Resource extends Data {
    constructor(props) {
        super(props);

        this.title_expension = this.title_expension.concat([
            <Lock key="Lock"/>
        ]);
        this.fields = this.fields.concat([
            <TextField name="User" key="User"
                       getFieldValue={this.getUser.bind(this)}/>
        ]);
    }

    getUser() {
        const reserved =
            this.props.resources_cache
                [this.props.cache_type][this.props.id].reserved;
        const owner =
            this.props.resources_cache
                [this.props.cache_type][this.props.id].owner;
        let user = "";
        if (owner) {
            user = owner;
        } else if (reserved) {
            user = reserved;
        }
        return user;
    }
}

const mapStateToProps = (state) => {
    return {
        resources_cache: state.cache.resources,
        display_fields_cache: state.cache.display_list
    };
};

export default connect(mapStateToProps)(Resource);