import {RESOURCES_DATA_UPDATED_ACTION,
        DISPLAY_LIST_UPDATED_ACTION} from "../actions/data_actions"

const initial_state = {
    resources: {},
    display_list: {}
};

const data_reducer = (state=initial_state, action) => {
    switch(action.type) {
        case RESOURCES_DATA_UPDATED_ACTION:
            return {...state, resources: action.newData};
        case DISPLAY_LIST_UPDATED_ACTION:
            return {...state, display_list: action.newData};
    }
    return state;
};

export default data_reducer;