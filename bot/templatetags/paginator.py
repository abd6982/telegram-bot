from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
# def paginate_to(context, length=10, show_ellipsis=False):
def paginate_to(context, args=None):
    """
        Usage: {{ context|paginate_to:"length,True" }} eg {{ context|paginate_to:"8,True" }} or {{ context|paginate_to:"8" }} or {{ context|paginate_to:8 }}
    """
    html = ""

    if args is None or isinstance(args, int):
        length = 10 if args is None else args
        show_ellipsis = False
    else:
        args = [arg.strip() for arg in args.split(',')]
        if len(args) == 1:
            length = int(args[0])
            show_ellipsis = False
        else:
            length = int(args[0])
            show_ellipsis = args[1]

    if context or context.has_other_pages:
        maxi = (int((context.number-1)/length)+1)*length
        mini = maxi - (length-1)
        html += '<ul class ="pagination" >'
        if context.has_previous():
            html += '<li class="hidden-xs"><a href="?page=1"> First </a></li>'
            html += '<li class="hidden-xs"><a href="?page=%d"> Previous </a></li>' % context.previous_page_number()

            html += '<li class="visible-xs"><a href="?page=1"> &laquo;&laquo; </a></li>'
            html += '<li class="visible-xs"><a href="?page=%d"> &laquo; </a></li>' % context.previous_page_number()
            if show_ellipsis and mini > length:
                html += '<li class="disabled"><span>...</span></li><li>'
        else:
            html += '<li class="disabled hidden-xs"><span> First </span></li>'
            html += '<li class="disabled hidden-xs"><span> Previous </span></li>'

            html += '<li class="disabled visible-xs"><span> &laquo;&laquo; </span></li>'
            html += '<li class="disabled visible-xs"><span> &laquo; </span></li>'

        for i in context.paginator.page_range:
            if mini <= i <= maxi:
                if context.number == i:
                    html += '<li class="active"><span>%d<span class="sr-only">(current)</span></span></li>' % i
                else:
                    html += '<li><a href="?page=%d" >%d</a></li>' % (i, i)

        if context.has_next():
            print(maxi, "  ", context.paginator.num_pages, "  ", context.end_index())
            if show_ellipsis and maxi < context.paginator.num_pages:
                html += '<li class="disabled"><span>...</span></li><li>'
            html += '<li><a href="?page=%d" class="hidden-xs"> Next </a></li>' % context.next_page_number()
            html += '<li><a href="?page=%d" class="hidden-xs"> Last </a></li>' % context.paginator.num_pages

            html += '<li><a href="?page=%d" class="visible-xs"> &raquo; </a></li>' % context.next_page_number()
            html += '<li><a href="?page=%d" class="visible-xs"> &raquo;&raquo; </a></li>' % context.paginator.num_pages
        else:
            html += '<li class="disabled hidden-xs"><span> Next </span></li>'
            html += '<li class="disabled hidden-xs"><span> Last </span></li>'

            html += '<li class="disabled visible-xs"><span> &raquo; </span></li>'
            html += '<li class="disabled visible-xs"><span> &raquo;&raquo; </span></li>'

        html += '</ul>'

    return format_html(html)
