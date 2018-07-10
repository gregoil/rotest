const WEBSOCKET_PORT = 9000;

export class CallbackWebSocket {
    constructor(callback, ...args) {
        this.callback = callback;
        this.websocket = new WebSocket(`ws://${location.hostname}:${WEBSOCKET_PORT}`, ...args);
        this.websocket.onmessage = this.onmessage.bind(this);
    }

    onmessage(event) {
        this.callback(JSON.parse(event.data));
    }
}