from cs130.eram.review_modules import review_module

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

def compute_weighted_mean(score_and_review_list) :
    weighted_sum = 0
    total_weights = 0
    for (score, review_count) in score_and_review_list :
        if (score != -1) :
            weighted_sum += int(score) * int(review_count)
            total_weights += int(review_count)
    if total_weights == 0 :
        return -1
    else :
        return weighted_sum / total_weights    
    
# Returns the score, number of reviews, and last used query        
def query_review_module_by_title(review_module, title, mode) :
    # In quick mode, do not attempt to guess what query would work.
    if mode == "quick":
        number_of_tries = 1
    else:
        number_of_tries = 3
    
    print "\nSearch Mode: " + mode
    
    # This is getting redundant
    number_of_words = 4
    while (number_of_tries > 0) :
        query = get_first_n_words(title, number_of_words)
        print "\nSearch Term: " + query
        (score, reviews_count) = review_module.get_score(query, "title")
        number_of_tries -= 1
        number_of_words -= 1
        if ( score != -1 or reviews_count != -1 ):
            break
            
    return (score, reviews_count, query)