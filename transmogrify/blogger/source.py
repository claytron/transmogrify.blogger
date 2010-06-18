from lxml import objectify
from zope.annotation.interfaces import IAnnotations
from zope.interface import implements
from zope.interface import classProvides
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import resolvePackageReferenceOrFile

SETTINGS_KEY = "transmogrify.blogger.settings"
SETTINGS_SCHEMA = "http://schemas.google.com/blogger/2008/kind#settings"
POST_SCHEMA = "http://schemas.google.com/blogger/2008/kind#post"
COMMENT_SCHEMA = "http://schemas.google.com/blogger/2008/kind#comment"
BLOGGER_NAMESPACES = {
    'f': "http://www.w3.org/2005/Atom",
    'thr': 'http://purl.org/syndication/thread/1.0',
    }


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
        # custom options for this source
        self.filename = resolvePackageReferenceOrFile(options['filename'])
        self.init_xml_obj(self.filename)
        # get the blog settings and add them as an annotation for
        # use later in the pipeline
        self.storage = IAnnotations(transmogrifier).setdefault(
            SETTINGS_KEY, {})
        # grab the settings from the xml feed
        self.init_settings()

    def init_settings(self):
        settings = self.xml_root.xpath(
            "f:entry/f:category[contains(@term, '%s')]/.." % SETTINGS_SCHEMA,
            namespaces=BLOGGER_NAMESPACES)
        for setting in settings:
            setting_key = setting.id.text.split(".")[-1]
            self.storage[setting_key] = setting.content.text

    def init_xml_obj(self, filename):
        xml_file = open(filename)
        self.xml_obj = objectify.parse(filename)
        self.xml_root = self.xml_obj.getroot()
        xml_file.close()

    def __iter__(self):
        # add any other sources into the stream
        for item in self.previous:
            yield item
        # process the blog posts
        posts = self.xml_root.xpath(
            "f:entry/f:category[contains(@term, '%s')]/.." % POST_SCHEMA,
            namespaces=BLOGGER_NAMESPACES)
        for post in posts:
            # XXX: dates aren't working
            item = dict(
                title=post.title.text,
                text=post.content.text,
                effectiveDate=post.published.text,
                modification_date=post.updated.text,
                )
            # XXX: do I need this?
            item['_transmogrify.blogger.post_id'] = post.id.text
            yield item
        # process the post comments
        comments = self.xml_root.xpath(
            "f:entry/f:category[contains(@term, '%s')]/.." % COMMENT_SCHEMA,
            namespaces=BLOGGER_NAMESPACES)
        for comment in comments:
            # XXX: decide what to do with comments
            pass
