dokkupy - Python API and script for dokku
=========================================

Install ::

    pip install dokkupy

    # or from source
    pip install git+https://github.com/fenrrir/dokkupy.git

Requires ::

    Python >= 3.10
    GitPython>=3.1.30

Debugging ::

    export DOKKUPY_DEBUG=1

Features
--------
- API for apps
    - list
    - create
    - exists
    - is_running
    - start
    - stop
    - restart
    - destroy
    - get_config
    - set_config
    - del_config
    - scale

- API for addons/plugins
    - list
    - create
    - exists
    - is_running
    - start
    - stop
    - restart
    - clone
    - destroy
    - link
    - unlink
    - links

- API for registry (`registry:login`, `registry:set`)
    - login
    - set

- API for builder (`builder:set`)
    - set

- API for deployment (`git:from-image`)
    - from_image


Examples
--------

Stopping a application ::

    dokku = dokkupy.Dokku('dokku@mydokkuhost.net')
    apps = list(dokku)
    first_app = apps[0]
    first_app.stop()


Connecting on a non-default SSH port ::

    dokku = dokkupy.Dokku('dokku@mydokkuhost.net', ssh_port=2222)


Logging into a Docker registry ::

    dokku = dokkupy.Dokku('dokku@mydokkuhost.net')
    dokku.registry.login(
        'registry.gitlab.com', 'gitlab-ci-token', 'password', global_=True,
    )
    dokku.registry.set('server', 'registry.gitlab.com', app='myapp')
    dokku.registry.set('image-repo', 'group/project', app='myapp')


Setting the builder for an app ::

    dokku = dokkupy.Dokku('dokku@mydokkuhost.net')
    app = dokku['myapp']
    app.builder.set('selected', 'dockerfile')


Deploying from a Docker image ::

    dokku = dokkupy.Dokku('dokku@mydokkuhost.net')
    app = dokku['myapp']
    app.git.from_image('registry.gitlab.com/group/project:tag')


Creating a postgres database ::

    dokku = dokkupy.Dokku('dokku@mydokkuhost.net')
    postgres = dokku.get_service('postgres')
    if postgres:  # is available?
        mydb = postgres['mydb']
        if mydb: # database exists
            mydb.destroy()
        mydb.create()
        mydb.link(first_app)



Deploying with cli ::

    $ cat config-example.json
    {
      "registry": {
        "login": {
          "global": true,
          "server": "registry.gitlab.com",
          "username": "gitlab-ci-token",
          "password": {"env": "CI_REGISTRY_PASSWORD"}
        },
        "set": {
          "server": "registry.gitlab.com",
          "image-repo": "group/project"
        }
      },
      "builder": {
        "set": {
          "selected": "dockerfile"
        }
      },
      "deployment": {
        "method": "image",
        "image": {
          "from": "registry.gitlab.com/group/project:tag"
        }
      },
      "services": [
        {
          "name": "postgres",
          "destroy_on_remove": true
        }
      ],
      "environ": {
        "key": "secret"
      },
      "scale": {
        "worker": 1
    }
    $ cd <project path>
    $ dokkupycli --project-name mydeploy --config config-example.json --address dokku@mydokkuhost.net deploy
    $ dokkupycli --project-name mydeploy --config config-example.json --address dokku@mydokkuhost.net --ssh-port 2222 deploy
