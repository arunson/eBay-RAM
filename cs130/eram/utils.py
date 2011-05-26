# Filters a space-delimited string based on a blacklist.
# The blacklist should be a list of lowercase words.
# The input will automatically be lowercased.
def filter(string, blacklist) :
    # Lowercase the input
    lowercase = string.lower()
    
    word_list = lowercase.split(' ')
    filtered_words = []
    for word in word_list:
        if word not in blacklist:
            filtered_words.append(word)
    
    return ' '.join(filtered_words)

def get_first_n_words(string, n) :
    word_list = string.split(' ')
    return_val = ""
    for word in (word_list[:n]) :
        return_val += word + " "
    return return_val
    
def test(self):
    return "lol"