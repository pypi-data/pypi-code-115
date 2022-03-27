# automatically generated by the FlatBuffers compiler, do not modify

# namespace: proto

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

class SubscriberFeatures(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = SubscriberFeatures()
        x.Init(buf, n + offset)
        return x

    @classmethod
    def GetRootAsSubscriberFeatures(cls, buf, offset=0):
        """This method is deprecated. Please switch to GetRootAs."""
        return cls.GetRootAs(buf, offset)
    # SubscriberFeatures
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # SubscriberFeatures
    def PublisherIdentification(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return bool(self._tab.Get(flatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

    # SubscriberFeatures
    def PatternBasedSubscription(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return bool(self._tab.Get(flatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

    # SubscriberFeatures
    def PublicationTrustlevels(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return bool(self._tab.Get(flatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

    # SubscriberFeatures
    def SubscriptionRevocation(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return bool(self._tab.Get(flatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

    # SubscriberFeatures
    def EventHistory(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return bool(self._tab.Get(flatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

    # SubscriberFeatures
    def AcknowledgeSubscriberReceived(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(14))
        if o != 0:
            return bool(self._tab.Get(flatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

    # SubscriberFeatures
    def PayloadTransparency(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(16))
        if o != 0:
            return bool(self._tab.Get(flatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

    # SubscriberFeatures
    def PayloadEncryptionCryptobox(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(18))
        if o != 0:
            return bool(self._tab.Get(flatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

def Start(builder): builder.StartObject(8)
def SubscriberFeaturesStart(builder):
    """This method is deprecated. Please switch to Start."""
    return Start(builder)
def AddPublisherIdentification(builder, publisherIdentification): builder.PrependBoolSlot(0, publisherIdentification, 0)
def SubscriberFeaturesAddPublisherIdentification(builder, publisherIdentification):
    """This method is deprecated. Please switch to AddPublisherIdentification."""
    return AddPublisherIdentification(builder, publisherIdentification)
def AddPatternBasedSubscription(builder, patternBasedSubscription): builder.PrependBoolSlot(1, patternBasedSubscription, 0)
def SubscriberFeaturesAddPatternBasedSubscription(builder, patternBasedSubscription):
    """This method is deprecated. Please switch to AddPatternBasedSubscription."""
    return AddPatternBasedSubscription(builder, patternBasedSubscription)
def AddPublicationTrustlevels(builder, publicationTrustlevels): builder.PrependBoolSlot(2, publicationTrustlevels, 0)
def SubscriberFeaturesAddPublicationTrustlevels(builder, publicationTrustlevels):
    """This method is deprecated. Please switch to AddPublicationTrustlevels."""
    return AddPublicationTrustlevels(builder, publicationTrustlevels)
def AddSubscriptionRevocation(builder, subscriptionRevocation): builder.PrependBoolSlot(3, subscriptionRevocation, 0)
def SubscriberFeaturesAddSubscriptionRevocation(builder, subscriptionRevocation):
    """This method is deprecated. Please switch to AddSubscriptionRevocation."""
    return AddSubscriptionRevocation(builder, subscriptionRevocation)
def AddEventHistory(builder, eventHistory): builder.PrependBoolSlot(4, eventHistory, 0)
def SubscriberFeaturesAddEventHistory(builder, eventHistory):
    """This method is deprecated. Please switch to AddEventHistory."""
    return AddEventHistory(builder, eventHistory)
def AddAcknowledgeSubscriberReceived(builder, acknowledgeSubscriberReceived): builder.PrependBoolSlot(5, acknowledgeSubscriberReceived, 0)
def SubscriberFeaturesAddAcknowledgeSubscriberReceived(builder, acknowledgeSubscriberReceived):
    """This method is deprecated. Please switch to AddAcknowledgeSubscriberReceived."""
    return AddAcknowledgeSubscriberReceived(builder, acknowledgeSubscriberReceived)
def AddPayloadTransparency(builder, payloadTransparency): builder.PrependBoolSlot(6, payloadTransparency, 0)
def SubscriberFeaturesAddPayloadTransparency(builder, payloadTransparency):
    """This method is deprecated. Please switch to AddPayloadTransparency."""
    return AddPayloadTransparency(builder, payloadTransparency)
def AddPayloadEncryptionCryptobox(builder, payloadEncryptionCryptobox): builder.PrependBoolSlot(7, payloadEncryptionCryptobox, 0)
def SubscriberFeaturesAddPayloadEncryptionCryptobox(builder, payloadEncryptionCryptobox):
    """This method is deprecated. Please switch to AddPayloadEncryptionCryptobox."""
    return AddPayloadEncryptionCryptobox(builder, payloadEncryptionCryptobox)
def End(builder): return builder.EndObject()
def SubscriberFeaturesEnd(builder):
    """This method is deprecated. Please switch to End."""
    return End(builder)