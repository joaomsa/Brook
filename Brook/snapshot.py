from libvirt import virDomainSnapshot
from xml.etree import ElementTree

class brookDomainSnapshot(virDomainSnapshot):
    def __new__(cls, snapshot):
        snapshot.__class__ = cls
        return snapshot

    def __init__(self, snapshot):
        self.xml = ElementTree.fromstring(snapshot.getXMLDesc())
        pass

    def getDate(self):
        return int(self.xml.find('creationTime').text)

    def getState(self):
        return self.xml.find('state').text
