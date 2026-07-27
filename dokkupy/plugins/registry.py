from dokkupy.utils import resolve_config_value


class Registry(object):
    def __init__(self, dokku):
        self.dokku = dokku

    def login(self, server, username, password=None, *, global_=False,
              password_stdin=False, app=None):
        args = ['registry:login']
        if global_:
            args.append('--global')
        elif app:
            args.append(app)
        if password_stdin:
            args.append('--password-stdin')
        args.extend([server, username])
        kwargs = {}
        if password_stdin:
            kwargs['input'] = password
        elif password is not None:
            args.append(password)
        return self.dokku.run(*args, **kwargs)

    def set(self, key, value=None, *, global_=False, app=None):
        args = ['registry:set']
        if global_:
            args.append('--global')
        elif app:
            args.append(app)
        args.append(key)
        if value is not None:
            args.append(str(value))
        return self.dokku.run(*args)

    def apply_config(self, registry_config, app_name):
        login = registry_config.get('login')
        if login:
            global_login = login.get('global', False)
            app = login.get('app')
            if not global_login and app is None:
                app = app_name
            password = resolve_config_value(login.get('password'))
            self.login(
                login['server'],
                login['username'],
                password=password,
                global_=global_login,
                password_stdin=login.get('password_stdin', False),
                app=app if not global_login else None,
            )

        set_config = registry_config.get('set')
        if set_config:
            global_set = set_config.get('global', False)
            app = set_config.get('app')
            if not global_set and app is None:
                app = app_name
            for key, value in set_config.items():
                if key in ('global', 'app'):
                    continue
                if value == '' or value is None:
                    self.set(key, global_=global_set, app=app)
                else:
                    self.set(
                        key,
                        resolve_config_value(value),
                        global_=global_set,
                        app=app,
                    )
