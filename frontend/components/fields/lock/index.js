import axios from "axios";
import React from "react";
import {connect} from "react-redux";

import lockSrc from "./img/lock.png";
import unlockSrc from "./img/unlock.png";
import "./index.css";

class Lock extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isHovered: false
        };
        this.onMouseEnter = this.onMouseEnter.bind(this);
        this.onMouseLeave = this.onMouseLeave.bind(this);
        this.onClick = this.onClick.bind(this);
    }
    get isLocked() {
        return this.props.isLocked();
    }
    get resourceName() {
        return this.props.resourceName();
    }
    onClick() {
        if(this.isLocked) {
            axios.get(`/api/rotest/release_owner/${this.resourceName}`);
            axios.get(`/api/rotest/release_reserved/${this.resourceName}`);
        } else {
            axios.get(`/api/rotest/lock_resource/${this.resourceName}`);
        }
    }

    onMouseEnter() {
        this.setState({
            ...this.state,
            isHovered: true
        });
    }

    onMouseLeave() {
        this.setState({
            ...this.state,
            isHovered: false
        });
    }

    render() {
        return (
            <img className="Lock"
                 onClick={this.onClick}
                 onMouseEnter={this.onMouseEnter}
                 onMouseLeave= {this.onMouseLeave}
                 src={this.isLocked ^ this.state.isHovered?
                        lockSrc: unlockSrc}/>
        );
    }
}

const mapStateToProps = (state) => {
    return {
        resources_cache: state.cache.resources,
    };
};

export default connect(mapStateToProps)(Lock);