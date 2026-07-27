class Certs(object):
    def __init__(self, app):
        self.app = app

    def add(self, crt, key, ca_chain=None):
        args = ['certs:add', self.app.name, crt, key]
        if ca_chain:
            args.append(ca_chain)
        return self.app.dokku.run(*args)

    def generate(self, country, state, city, company,
                 section, email, password, opt_company):
        domain = '{}.{}'.format(self.app.name, self.app.dokku.hostname_only)
        inputs = [country,
                  state,
                  city,
                  company,
                  section,
                  domain,
                  email,
                  password,
                  opt_company
        ]
        inputs = ''.join([i + '\n' for i in inputs])
        return self.app.dokku.run(
            'certs:generate', self.app.name, domain, input=inputs,
        )

    def remove(self):
        return self.app.dokku.run('certs:remove', self.app.name)

    @property
    def has_cert(self):
        output = self.app.dokku.run('certs:report', self.app.name)
        return 'Ssl enabled:         true' in output

    def apply_config(self, certs_config):
        add_config = certs_config.get('add')
        if add_config:
            self.add(
                add_config['crt'],
                add_config['key'],
                ca_chain=add_config.get('ca_chain'),
            )

        generate_config = certs_config.get('generate')
        if generate_config:
            self.generate(**generate_config)
