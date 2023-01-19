def shortensize(size):
    unit = 'B'

    if size >= 1024:
        size /= 1024
        unit = 'KB'

    if size >= 1024:
        size /= 1024
        unit = 'MB'

    if size >= 1024:
        size /= 1024
        unit = 'GB'

    return str('%.2f' % round(size, 2)) + ' ' + unit