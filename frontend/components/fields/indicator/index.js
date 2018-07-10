import React from "react";

import "./index.css";

export class IndicatorField extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            src: this.props.src,
            title: this.props.title,
            predicate: this.props.predicate,
        };
    }

    render() {
        return (
            <div style={{display: this.predicate()? "" : "none"}}
                 className="Indicator">
                <img src={this.state.src} />
            </div>
        );
    }
}
