======================
django-pagination-plus
======================

This template tag library is used for displaying pagination links in paginated
Django views. It exposes a template tag ``{% paginationplus %}`` that will take
care of iterating over the page numbers.

Usage
-----

Add ``paginationplus`` to your ``INSTALLED_APPS`` in your settings.

At the start of the template for your paginated view, use the following to load
the tag module: ::

    {% load paginationplus %}

Then, at the position you want your pagination links to appear, use the
following block tag. ::

    {% paginationplus page_obj url_name url_arg1=... url_arg2=... %}
        ...
    {% endpaginationplus %}

The first argument passed to the opening tag is the ``Page`` object of your
paginated view. The remaining arguments are the same as the arguments passed to
the built-in ``{% url %}`` tag, minus the argument that takes the value for the
page number in the view, eg. ``page`` in the generic view ``ListView``.

The block iterates over the page numbers available from the ``Paginator`` object
associated with the ``Page`` object that is passed as the first argument to the
opening tag.

The block's content is rendered once for each iteration, and within this block,
a template variable named ``paginationplus`` is available.

This template variable exposes four attributes:

* ``number``
  The page number that is the subject of this iteration
* ``url``
  Contains the url of the page for the page number currently iterated over.
* ``is_filler``
  When this is True, the current iteration does not represent a page number,
  but instead represents a filler, ie. a hole in the sequence of page numbers.
  See below for more information.
* ``is_current``
  When this is True, the current iteration represents number of the page that
  is currently displayed in the view.
  
Single tag usage
----------------

An alternative to the block tag, is the following: ::

    {% paginationplus page_obj url_name url_arg1=... url_arg2=... ... with 'template/name.html' %}

Using ``with`` in the tag indicates that the iteration will not occur in a block,
but instead in the template that follows ``with``. Within this template, the
parent template's full context is available, with an added ``paginationplus``
variable. The template passed to the tag needn't be a string, any available
template variable will do.
    
Settings
--------

By default, paginationplus will support displaying the links for the first,
previous, current, next, and last page. For instance, if you have a paginated
view with 99 pages, and the current page is page 30, the following sequence will
be iterated over: ``[1, None, 29, 30, 31, None, 99]``. Suppose the current page is
page 3, the sequence will be ``[1, 2, 3, 4, None, 99]``.

In the above sequences, the ``None`` values represent a hole in the page number
sequence, and for these holes, the ``paginationplus`` template variable will have
its ``is_filler`` attribute set to ``True``, the ``number`` and ``url`` attributes will
be set to ``None``, and ``is_current`` will be set to ``False``.

To disable this behavior, and iterate over all available page numbers, you can
set the ``PAGINATIONPLUS_CONTIGUOUS`` setting to ``True`` in your project's settings.

To control the number of page numbers before and after the current page that
will be iterated over, you can set the ``PAGINATIONPLUS_MAX_DISTANCE`` option.

For instance, when ``PAGINATIONPLUS_MAX_DISTANCE`` is set to 2, the following
sequence will be iterated over when the number of pages is 99 and the current
page is 30: ``[1, None, 28, 29, 30, 31, 32, None, 99]``. And when the current page is 3,
the sequence will be ``[1, 2, 3, 4, 5, None, 99]``.