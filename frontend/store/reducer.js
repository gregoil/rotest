import { combineReducers } from 'redux';

import data_reducer from "./reducers/data_reducer";

export default combineReducers({
    cache: data_reducer
});