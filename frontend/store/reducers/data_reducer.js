import {RESOURCES_DATA_UPDATED_ACTION,
        DISPLAY_LIST_UPDATED_ACTION} from "../actions/data_actions"

const initial_state = {
    resources: {},
    display_list: {}
};

const DELETE_OPERATION = 3;
const data_reducer = (state=initial_state, action) => {
    switch(action.type) {
        case RESOURCES_DATA_UPDATED_ACTION:
            const msg = state.resources.action.newData;
            for(const key of Object.keys(msg)) {
                if (key === "LogEntry") {
                    for (const resource_id of Object.keys(msg[key])) {
                        if(parseInt(msg[key][resource_id].action_flag) === DELETE_OPERATION) {
                            delete_from_cache(resource_id);
                        }
                    }
                    continue;
                }

                let resource = msg[key];
                if(!(msg in this.cache)) {
                    this.cache[key] = {};
                }
                for(const resource_id of Object.keys(resource)) {
                    state.resources[key][resource_id] = resource[resource_id];
                }
            }
            return state;
            
        case DISPLAY_LIST_UPDATED_ACTION:
            return {...state, display_list: action.newData};
    }
    return state;
};

export default data_reducer;