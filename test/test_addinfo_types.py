""" Tests for basic oboe event construction type safety. """
import oboe
import unit.base as base

class TestOboeAddInfo(base.TraceTestCase):

    def __init__(self, *args, **kwargs):
        super(TestOboeAddInfo, self).__init__(*args, **kwargs)

    def test_addinfo(self):
        """ Ensures that the c extension doesn't barf on any datatypes a user might log. """
        md = oboe.Metadata.makeRandom()
        evt = oboe.SwigEvent.startTrace(md)
        evt.addInfo('String', 'teststring')
        evt.addInfo('Null', None)
        evt.addInfo('Int', 33)
        evt.addInfo('Float', 33.33)
        evt.addInfo('Array', [33.33, 22])
        evt.addInfo('Map', {'key': 'val'})
        oboe.Context.get_default().report(evt)
        self.assertTrue(True)
