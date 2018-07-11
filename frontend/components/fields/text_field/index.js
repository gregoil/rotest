import React from "react";
import {connect} from "react-redux";
import "./index.css";

const DEFAULT_FONT_SIZE = 12;

class TextField extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            font_size: this.props.fontSize | DEFAULT_FONT_SIZE
        };
    }

    render() {
        const value = this.props.getFieldValue();
        return (
            <div className="TextField">
                <div className="Name">{this.props.name}</div>
                <div className="Value">
                    <span style={{fontSize: this.state.fontSize}}>
                        {value ? value : "-"}
                    </span>
                </div>
            </div>
        );
    }
}

const mapStateToProps = (state) => {
    return {
        resources_cache: state.cache.resources,
    };
};

export default connect(mapStateToProps)(TextField);