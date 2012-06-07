"""This template tag library is used for displaying pagination links in
paginated Django views. It exposes a template tag `{% paginationplus %}` that
will take care of iterating over the page numbers.

Usage
-----

Add `paginationplus` to your `INSTALLED_APPS` in your settings.

At the start of the template for your paginated view, use the following to load
the tag module:

    {% load paginationplus %}

Then, at the position you want your pagination links to appear, use the
following block tag.

    {% paginationplus page_obj url_name url_arg1=... url_arg2=... %}
        ...
    {% endpaginationplus %}

The first argument passed to the opening tag is the `Page` object of your
paginated view. The remaining arguments are the same as the arguments passed to
the built-in `{% url %}` tag, minus the argument that takes the value for the
page number in the view, eg. `page` in the generic view `ListView`.

The block iterates over the page numbers available from the `Paginator` object
associated with the `Page` object that is passed as the first argument to the
opening tag.

The block's content is rendered once for each iteration, and within this block,
a template variable named `paginationplus` is available.

This template variable exposes four attributes:

  * `number`
    The page number that is the subject of this iteration
  * `url`
    Contains the url of the page for the page number currently iterated over.
  * `is_filler`
    When this is True, the current iteration does not represent a page number,
    but instead represents a filler, ie. a hole in the sequence of page numbers.
    See below for more information.
  * `is_current`
    When this is True, the current iteration represents number of the page that
    is currently displayed in the view.
    
Single tag usage
----------------

An alternative to the block tag, is the following:

    {% paginationplus page_obj url_name url_arg1=... url_arg2=... ... with 'template/name.html' %}

Using `with` in the tag indicates that the iteration will not occur in a block,
but instead in the template that follows `with`. Within this template, the
parent template's full context is available, with an added `paginationplus`
variable. The template passed to the tag needn't be a string, any available
template variable will do.
    
Settings
--------

By default, paginationplus will support displaying the links for the first,
previous, current, next, and last page. For instance, if you have a paginated
view with 99 pages, and the current page is page 30, the following sequence will
be iterated over: `[1, None, 29, 30, 31, None, 99]`. Suppose the current page is
page 3, the sequence will be `[1, 2, 3, 4, None, 99]`.

In the above sequences, the `None` values represent a hole in the page number
sequence, and for these holes, the `paginationplus` template variable will have
its `is_filler` attribute set to `True`, the `number` and `url` attributes will
be set to `None`, and `is_current` will be set to `False`.

To disable this behavior, and iterate over all available page numbers, you can
set the `PAGINATIONPLUS_CONTIGUOUS` setting to `True` in your project's
settings.

To control the number of page numbers before and after the current page that
will be iterated over, you can set the `PAGINATIONPLUS_MAX_DISTANCE`.

For instance, when `PAGINATIONPLUS_MAX_DISTANCE` is set to 2, the following
sequence will be iterated over when the number of pages is 99 and the current
page is 30: `[1, None, 28, 29, 30, 31, 32, None, 99]`. And when the current page
is 3, the sequence will be `[1, 2, 3, 4, 5, None, 99]`.
"""


from django import template
from django.core import paginator
from django.core.urlresolvers import reverse

from django.core.exceptions import ImproperlyConfigured
from django.utils.safestring import mark_safe

import itertools

register = template.Library()

class PartialUrl(object):
    """An object that represents an URL to a paged view, without a value for the
    'page' view argument
    """
    def __init__(self, url_name, **kwargs):
        self.url_name = url_name
        self.kwargs = kwargs
    
    def url_for_page(self, page):
        """Get the URL for the page
        """
        kwargs = dict(self.kwargs)
        kwargs['page'] = page
        return reverse(self.url_name, kwargs=kwargs)

class PaginationPage(object):
    
    def __init__(self, number, is_current, partial_url):
        self.number = number
        self.is_current = is_current
        self.partial_url = partial_url
        
    @property
    def is_filler(self):
        return not self.number
    
    @property
    def url(self):
        if self.is_filler:
            return None
        if self.partial_url:
            return self.partial_url.url_for_page(self.number)
        return '?page=%d' % self.number
    
    def __unicode__(self):
        if self.is_filler:
            return ''
        return mark_safe(u'<a href="%s">%d</a>' % (self.url, self.number))


class PaginationPlusNode(template.Node):

    def __init__(self, nodelist_or_include, page, url_name, url_kwargs):
        
        self.nodelist_or_include = nodelist_or_include
        self.page = page
        self.url_name = url_name
        self.url_kwargs = url_kwargs
        
        from django.conf import settings
        try:
            self.max_distance = int(
                getattr(settings, 'PAGINATIONPLUS_MAX_DISTANCE', 1)
            )
            if self.max_distance < 1:
                raise ValueError
        except (TypeError, ValueError):
            raise ImproperlyConfigured(
                'PAGINATIONPLUS_MAX_DISTANCE must be a number greater than 0'
            )
        self.contiguous = getattr(settings, 'PAGINATIONPLUS_CONTIGUOUS', False)

    def pagination(self, partial_url):
        page = self.page
        paginator = page.paginator
        if self.contiguous:
            for p in itertools.imap(
                lambda p: PaginationPage(p, page.number, partial_url),
                paginator.page_range
            ):
                yield p
            return
        yield PaginationPage(1, page.number, partial_url)
        last = 1
        startRange = (1, 1)
        currentRange = (
            page.number - self.max_distance, page.number + self.max_distance
        )
        endRange = (paginator.num_pages, paginator.num_pages)
        for r in (startRange, currentRange, endRange):
            if r[0] > last + 1:
                yield PaginationPage(None, page.number, partial_url)
            rangeStart = max(min(paginator.num_pages, r[0]), last + 1)
            rangeEnd = min(paginator.num_pages, r[1])
            if rangeStart <= rangeEnd:
                for p in xrange(rangeStart, rangeEnd + 1):
                    yield PaginationPage(p, page.number, partial_url)
                last = rangeEnd
    
    def url_kwargs_to_dict(self, context):
        args = []
        kwargs = {}
        for index, kwd in enumerate(self.url_kwargs):
            splitted = kwd.split('=')
            
            if len(splitted) > 2:
                raise template.TemplateSyntaxError(
                    'Could not parse argument %d: %r' % (index + 2, kwargs)
                )
            arg_name = None
            if len(splitted) == 2:
                arg_name, arg_value = splitted
            else:
                arg_value = splitted[0]
            
            arg_value = template.Variable(arg_value)
            arg_value = arg_value.resolve(context)
            if arg_name:
                kwargs[arg_name] = arg_value
            else:
                args.append(arg_value)
        return args, kwargs
                
    
    def render(self, context):
        page = template.Variable(self.page)
        page = page.resolve(context)
        self.page = page
        if not isinstance(page, paginator.Page):
            raise template.TemplateSyntaxError(
                '%r is not a valid Page object' % self.page
            )
        url_args, url_kwargs = self.url_kwargs_to_dict(context)
        partial_url = PartialUrl(self.url_name, *url_args, **url_kwargs)

        if not isinstance(self.nodelist_or_include, template.NodeList):
            # 'with' used in tag, template include is assumed
            nodelist_var = template.Variable(self.nodelist_or_include)
            nodelist = template.loader.get_template(
                nodelist_var.resolve(context)
            )
        else:
            nodelist = self.nodelist_or_include
        result = []
        
        for paginated in self.pagination(partial_url):
            context.push()
            context['paginationplus'] = paginated
            result.append(nodelist.render(context))
            context.pop()
        return u''.join(result)



@register.assignment_tag
def paginationplus_url(url_name, **kwargs):
    return PartialUrl(url_name, **kwargs)

@register.filter
def paginate(partial_pagination_url, page):
    return partial_pagination_url.render(page)

@register.tag('paginationplus')
def paginationplus(parser, token):
    contents = token.split_contents()
    
    try:
        tag_name, page, url_name = contents[:3]
    except ValueError:
        raise template.TemplateSyntaxError(
            '%r tag expects at least 2 arguments', contents[0]
        )
    url_kwargs = contents[3:]
    if contents[-2] == 'with':
        include_template = contents[-1]
        url_kwargs = url_kwargs[:-2]
        nodelist_or_include = include_template
    else:
        nodelist_or_include = parser.parse(('endpaginationplus',))
    parser.delete_first_token()
    return PaginationPlusNode(nodelist_or_include, page, url_name, url_kwargs)
