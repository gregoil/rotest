import React from "react";
import {connect} from "react-redux";

import lockSrc from "./img/lock.svg";
import unlockSrc from "./img/unlock.svg";
import "./index.css";

class Lock extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isLocked: false,
            isHovered: false
        };

        this.onMouseEnter = this.onMouseEnter.bind(this);
        this.onMouseLeave = this.onMouseLeave.bind(this);
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
                 onMouseEnter={this.onMouseEnter}
                 onMouseLeave= {this.onMouseLeave}
                 src={this.state.isLocked ^ this.state.isHovered?
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