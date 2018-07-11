import {RESOURCES_DATA_UPDATED_ACTION,
        DISPLAY_LIST_UPDATED_ACTION} from "../actions/data_actions"

const initial_state = {
    resources: {},
    display_list: {}
};

const DELETE_OPERATION = 3;


const delete_from_cache = (state, resource_id) => {
    for (const resource_cache of Object.values(state.resources)) {
        if (resource_id in resource_cache) {
            delete resource_cache[resource_id];
            break;
        }
    }
};

function cloneObject(obj) {
    const clone = {};
    for(const i of Object.keys(obj)) {
        if(obj[i] !== null && typeof(obj[i]) === "object")
            clone[i] = cloneObject(obj[i]);
        else
            clone[i] = obj[i];
    }
    return clone;
}

const data_reducer = (state=initial_state, action) => {
    switch(action.type) {
        case RESOURCES_DATA_UPDATED_ACTION:
            const msg = action.newData;
            const newState = cloneObject(state);
            for(const key of Object.keys(msg)) {
                if (key === "LogEntry") {
                    for (const resource_id of Object.keys(msg[key])) {
                        if(parseInt(msg[key][resource_id].action_flag) === DELETE_OPERATION) {
                            delete_from_cache(newState, resource_id);
                        }
                    }
                    continue;
                }

                let resource = msg[key];
                if(!(key in newState.resources)) {
                    newState.resources[key] = {};
                }
                for(const resource_id of Object.keys(resource)) {
                    newState.resources[key][resource_id] = resource[resource_id];
                }
            }
            return newState;
            
        case DISPLAY_LIST_UPDATED_ACTION:
            return {...state, display_list: action.newData};
    }
    return state;
};

export default data_reducer;