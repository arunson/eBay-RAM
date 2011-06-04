import threading
import time # For call limit enforcement
from cs130.eram import utils


class ReviewModuleThread(threading.Thread):

    def __init__(self, review_module, search_terms, search_type, call_limit_per_sec=1000):
        threading.Thread.__init__(self)
        self.review_module = review_module
        self.search_terms = search_terms
        self.search_type = search_type
        self.call_limit_per_sec = call_limit_per_sec
        
        # A list of tuples
        self.score_list = []
        
    def run(self):
        # Try to generate a score for each item
        for term in self.search_terms:
            # Searching by eBay Product IDs
            if self.search_type == "epid":
                if term != "":
                    self.score_list.append(self.review_module.get_score(term, self.search_type))
                else:
                    self.score_list.append((-1,-1))
            
            # Searching by plaintext titles
            else:
                (score, number_reviews, query) = utils.query_review_module_by_title(self.review_module, term, "slow")
                self.score_list.append((score, number_reviews))
                
            # Pause between calls if the call limit per second is reasonably low.
            # The assumption here is that with network latency, a high call limit 
            # will not be hit.
            if self.call_limit_per_sec <= 15:
                time.sleep(1./self.call_limit_per_sec)
        
    def get_scores(self):
        return self.score_list