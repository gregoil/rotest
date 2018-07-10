import React from "react";

import "./index.css";

const DEFAULT_FONT_SIZE = 12;

export class TextField extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            name: this.props.name,
            value: this.props.value,
            font_size: this.props.fontSize | DEFAULT_FONT_SIZE
        };
    }

    render() {
        return (
            <div className="TextField">
                <div className="Name">{this.state.name}</div>
                <div className="Value">
                    <span style={{fontSize: this.state.fontSize}}>
                        {this.state.value}
                    </span>
                </div>
            </div>
        );
    }
}
