def isin(l1, l2):
    '''
        Checks if any element of a list is included in a second list
    '''
    return any(x in l2 for x in l1)