from collections import defaultdict


class ComponentRegistry:
    __components = defaultdict(lambda: defaultdict(dict))

    @classmethod
    def register(cls, *, spec_id, component_name, key, value):
        cls.__components[spec_id][component_name][key] = value

    @classmethod
    def get_components(cls, *, spec_id, component_name):
        return cls.__components[spec_id][component_name]
