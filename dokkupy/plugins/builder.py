from dokkupy.utils import resolve_config_value


class Builder(object):
    def __init__(self, app):
        self.app = app

    def set(self, key, value=None, *, global_=False):
        args = ['builder:set']
        if global_:
            args.append('--global')
        else:
            args.append(self.app.name)
        args.append(key)
        if value is not None:
            args.append(str(value))
        return self.app.dokku.run(*args)

    def apply_config(self, builder_config):
        global_set = builder_config.get('global', False)
        for key, value in builder_config.items():
            if key in ('global', 'app'):
                continue
            if value == '' or value is None:
                self.set(key, global_=global_set)
            else:
                self.set(
                    key,
                    resolve_config_value(value),
                    global_=global_set,
                )
