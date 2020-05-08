from app.models.registry import Registry


def add_registries():
    registry_names = ['dockerhub']

    for name in registry_names:
        try:
            exists = Registry.find_first(name=name)

            if not exists:
                registry = Registry(name=name)
                registry.save()
        except Exception as e:
            print(str(e))
            return
