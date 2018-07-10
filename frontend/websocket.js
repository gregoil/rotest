const WEBSOCKET_PORT = 9000;

class CustomWebSocket extends WebSocket {
    constructor(...args) {
        super(`ws://${location.hostname}:${WEBSOCKET_PORT}`, ...args);
    }
}

export class CallbackWebSocket extends CustomWebSocket {
    constructor(callback, ...args) {
        super(...args);
        this.callback = callback;
    }

    onmessage(event) {
        this.callback(event.data);
    }
}