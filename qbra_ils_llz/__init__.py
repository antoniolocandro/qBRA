from .qbra_plugin import QbraPlugin

def classFactory(iface):
	return QbraPlugin(iface)