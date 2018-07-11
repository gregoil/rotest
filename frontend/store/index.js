import {createStore, applyMiddleware, compose} from 'redux';
import thunk from 'redux-thunk';

import reducer from './reducer';

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;

const store = createStore(reducer, composeEnhancers(applyMiddleware(thunk)));

export const followLink = (resource_cache, link) => {
    if(!link || !("link" in link)) {
        return null;
    }
    return resource_cache[link.link.type][link.link.id];
};
export default store;