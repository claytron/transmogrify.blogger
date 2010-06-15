from zope.annotation.interfaces import IAnnotations
from zope.interface import implements
from zope.interface import classProvides
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import resolvePackageReferenceOrFile

SETTINGS_KEY = "transmogrify.blogger.settings"


class BloggerSource(object):
    """A transmogrifier section that can read in a Blogger Atom export.
    """

    implements(ISection)
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        # get the blog settings and add them as an annotation for
        # use later in the pipeline
        self.storage = IAnnotations(transmogrifier).setdefault(
            SETTINGS_KEY, {})

    def __iter__(self):
        for item in self.previous:
            yield item
