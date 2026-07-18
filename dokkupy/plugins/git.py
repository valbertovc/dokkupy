class Git(object):
    def __init__(self, app):
        self.app = app

    def from_image(self, image, *, force=False, build_dir=None,
                   author_name=None, author_email=None):
        args = ['git:from-image']
        if force:
            args.append('--force')
        if build_dir:
            args.extend(['--build-dir', build_dir])
        args.extend([self.app.name, image])
        if author_name:
            args.append(author_name)
            if author_email:
                args.append(author_email)
        return self.app.dokku.run(*args)

    def apply_config(self, deployment_config):
        image_config = deployment_config['image']
        author = image_config.get('author', {})
        self.from_image(
            image_config['from'],
            force=image_config.get('force', False),
            build_dir=image_config.get('build_dir'),
            author_name=author.get('name'),
            author_email=author.get('email'),
        )
