export const RESOURCES_DATA_UPDATED_ACTION = 'cache/resources';
export const DISPLAY_LIST_UPDATED_ACTION = 'cache/display_list';

export const updateResourcesData = (data) => ({
    type: RESOURCES_DATA_UPDATED_ACTION,
    newData: data
});

export const updateDisplayList = (data) => ({
    type: DISPLAY_LIST_UPDATED_ACTION,
    newData: data
});