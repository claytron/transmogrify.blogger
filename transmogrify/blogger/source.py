from lxml import objectify
from dateutil.parser import parse
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
ATOM_URL = "http://www.w3.org/2005/Atom"
ATOM_NAMESPACE = "{%s}" % ATOM_URL
BLOGGER_NAMESPACES = {
    'a': ATOM_URL,
    'thr': 'http://purl.org/syndication/thread/1.0',
    'app': 'http://purl.org/atom/app#',
    }
# XXX: leaving off the "%z" for now as DateTime fields in
#      Archetypes don't seem to accept it.
RFC822_FMT = "%a, %d %h %Y %T"


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
            "a:entry/a:category[contains(@term, '%s')]/.." % SETTINGS_SCHEMA,
            namespaces=BLOGGER_NAMESPACES)
        for setting in settings:
            setting_key = setting.id.text.split(".")[-1]
            self.storage[setting_key] = setting.content.text

    def init_xml_obj(self, filename):
        xml_file = open(filename)
        self.xml_obj = objectify.parse(filename)
        self.xml_root = self.xml_obj.getroot()
        xml_file.close()

    def extract_comments(self, post_id, parent_path):
        """TODO: Move this down into iter?"""
        parsed_comments = []
        comments = self.xml_root.xpath(
            "a:entry/thr:in-reply-to[@ref='%s']/.." % post_id,
            namespaces=BLOGGER_NAMESPACES)
        for comment in comments:
            item = {}
            # XXX: Is this really needed, some other way around this?
            item['_transmogrify.blogger.comment'] = True
            item['_transmogrify.blogger.comment.id'] = comment.id.text
            if parent_path:
                item['_parent_path'] = parent_path
            item['title'] = comment.title.text
            item['text'] = comment.content.text
            item['author.name'] = comment.author.name.text
            # the uri may not exist, use find to get it
            item['author.url'] = comment.author.find("%suri" % ATOM_NAMESPACE)
            item['author.email'] = comment.author.email.text
            published = parse(comment.published.text)
            item['published'] = published
            published_rfc822 = published.strftime(RFC822_FMT)
            item['published.rfc822'] = published_rfc822
            updated = parse(comment.updated.text)
            item['updated'] = updated
            updated_rfc822 = updated.strftime(RFC822_FMT)
            item['updated.rfc822'] = updated_rfc822
            alt_link = comment.xpath(
                "a:link[@rel='alternate']/@href",
                namespaces=BLOGGER_NAMESPACES)
            item['link'] = alt_link and alt_link[0] or ""
            parsed_comments.append(item)
        return parsed_comments

    def __iter__(self):
        # add any other sources into the stream
        for item in self.previous:
            yield item
        # process the blog posts
        posts = self.xml_root.xpath(
            "a:entry/a:category[contains(@term, '%s')]/.." % POST_SCHEMA,
            namespaces=BLOGGER_NAMESPACES)
        for post in posts:
            item = {}
            item['_transmogrify.blogger.id'] = post.id.text
            item['_transmogrify.blogger.title'] = post.title.text
            text_type = dict(post.content.items()).get('type', '')
            mimetype = text_type and 'text/%s' % text_type or ''
            item['_transmogrify.blogger.mimetype'] = mimetype
            item['_transmogrify.blogger.content'] = post.content.text
            item['_transmogrify.blogger.author.name'] = post.author.name.text
            item['_transmogrify.blogger.author.uri'] = post.author.uri.text
            item['_transmogrify.blogger.author.email'] = post.author.email.text
            published = parse(post.published.text)
            item['_transmogrify.blogger.published'] = published
            published_rfc822 = published.strftime(RFC822_FMT)
            item['_transmogrify.blogger.published.rfc822'] = published_rfc822
            updated = parse(post.updated.text)
            item['_transmogrify.blogger.updated'] = updated
            updated_rfc822 = updated.strftime(RFC822_FMT)
            item['_transmogrify.blogger.updated.rfc822'] = updated_rfc822
            alt_link = post.xpath(
                "a:link[@rel='alternate']/@href",
                namespaces=BLOGGER_NAMESPACES)
            alt_link = alt_link and alt_link[0] or ""
            item['_transmogrify.blogger.link'] = alt_link
            post_state = "published"
            draft = post.xpath(
                "app:control/app:draft",
                namespaces=BLOGGER_NAMESPACES)
            if draft and draft[0] == "yes":
                post_state = "draft"
            item['_transmogrify.blogger.state'] = post_state
            comment_total = post.xpath(
                "thr:total",
                namespaces=BLOGGER_NAMESPACES)[0]
            item['_transmogrify.blogger.comments.number'] = int(comment_total)
            yield item
            # get the path for the blog post so we can pass it on to the
            # comments
            parent_path = item.get('_path', '')
            for comment in self.extract_comments(post.id.text, parent_path):
                yield comment
