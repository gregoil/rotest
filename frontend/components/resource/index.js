import React from "react";
import {connect} from "react-redux";

import {Data} from "../data";
import Lock from "../fields/lock";
import TextField from "../fields/text_field";
//import "./index.css";

//const FIELD_FILTER_LIST = ["group"];
const AVAILABLE_TITLE_COLOR = "#96ff77";
const RESERVED_TITLE_COLOR = "#ffd413";
const OWNER_TITLE_COLOR = "#e13b39";

export class Resource extends Data {
    constructor(props) {
        super(props);

        this.title_expension = this.title_expension.concat([
            <Lock key="Lock"
                  resourceName={this.getName.bind(this)}
                  isLocked={this.isLocked.bind(this)}/>
        ]);
    }
    get filter_list() {
        return ["owner", "reserved", "is_available"].concat(super.filter_list);
    }
    get fields() {
        const class_fields = [
            <TextField name="User"
                       key="User"
                       field_name={this.getUserFieldName.bind(this)}
                       cache_type={this.props.cache_type}
                       object_id={this.props.id}
            />
        ];
        return class_fields.concat(super.fields);
    }
    getName() {
        return this.props.resources_cache[this.props.cache_type][this.props.id].name;
    }
    isLocked() {
        return (this.props.resources_cache[this.props.cache_type][this.props.id].owner ||
                this.props.resources_cache[this.props.cache_type][this.props.id].reserved ||
                !this.props.resources_cache[this.props.cache_type][this.props.id].is_available);
    }
    get titleColor() {
        const reserved =
            this.props.resources_cache
                [this.props.cache_type][this.props.id].reserved;
        const owner =
            this.props.resources_cache
                [this.props.cache_type][this.props.id].owner;
        let title_color = AVAILABLE_TITLE_COLOR;
        if (owner) {
            title_color = OWNER_TITLE_COLOR;
        } else if (reserved) {
            title_color = RESERVED_TITLE_COLOR;
        }
        return title_color;
    }

    getUserFieldName() {
        const reserved =
            this.props.resources_cache
                [this.props.cache_type][this.props.id].reserved;
        const owner =
            this.props.resources_cache
                [this.props.cache_type][this.props.id].owner;
        let user_field = "undefined";
        if (owner) {
            user_field = "owner";
        } else if (reserved) {
            user_field = "reserved";
        }
        return user_field;
    }

}

const mapStateToProps = (state) => {
    return {
        resources_cache: state.cache.resources,
        display_fields_cache: state.cache.display_list
    };
};

export default connect(mapStateToProps)(Resource);