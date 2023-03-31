

def paginate(items,per_page,page):

    paginated_items = items[(per_page*page)-per_page : per_page*page]

    pagination = {
        'per_page' : per_page,
        'count' : len(paginated_items),
        'total_count' : len(items),
        'page' : page,
        'next' : page+1 if per_page*page < len(items) else 'null',
        'previous' : 'null' if page ==1 else page-1
    }

    return pagination , paginated_items



