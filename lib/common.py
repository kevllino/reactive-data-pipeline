import json

def exportJsonToString(jsonObject):
    return json.dumps(jsonObject, separators=(',', ':')) + "\n"

# create a new dict by removing given field
def remove_dict_element(initial_dict, key):
    dict_copy = dict(initial_dict)
    del dict_copy[key]
    return dict_copy