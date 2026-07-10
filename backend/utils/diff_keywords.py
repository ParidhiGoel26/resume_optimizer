def find_added_keywords(original, optimized):
    orig_words = set(original.lower().split())
    opt_words = set(optimized.lower().split())
    new_words = opt_words - orig_words
    return list(word for word in new_words if len(word) > 3)
