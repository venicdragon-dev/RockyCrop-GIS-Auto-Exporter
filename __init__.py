def classFactory(iface):
    from .main import RunGeneration
    return RunGeneration(iface)