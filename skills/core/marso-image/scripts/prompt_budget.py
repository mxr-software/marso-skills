"""Check a final prompt against an explicitly supplied endpoint length limit."""


def check(text, limit, *, counting='codepoints'):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Nonempty final submitted prompt required')
    if type(limit) is not int or limit <= 0:
        raise ValueError('Positive documented endpoint limit required')
    if counting == 'codepoints':
        length = len(text)
    elif counting == 'utf16':
        length = len(text.encode('utf-16-le')) // 2
    elif counting == 'utf8':
        length = len(text.encode('utf-8'))
    else:
        raise ValueError('Use documented codepoints, utf16 or utf8 counting; tokens unsupported')
    return {'passed': length <= limit, 'length': length, 'limit': limit,
            'remaining': limit-length, 'counting': counting,
            'scope': 'Supplied text only; include actual reference expansion/enhancement before checking'}
