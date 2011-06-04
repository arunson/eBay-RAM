import threading
from cs130.eram import utils

class ItemThread(threading.Thread):
    def __init__(self, item_info, ebay_review_module, module_list):
        threading.Thread.__init__(self)
        self.ebay_review_module = ebay_review_module
        self.module_list = module_list
        self.item_info = item_info
    
    def run(self):
        # Templates cannot handle variable names with leading @ or _
        self.item_info["sellingStatus"]["currentPrice"]["value"] = self.item_info["sellingStatus"]["currentPrice"]["__value__"]
        self.item_info["sellingStatus"]["currentPrice"]["currencyId"] = self.item_info["sellingStatus"]["currentPrice"]["@currencyId"]
        
        # Run the title through a filter
        title = self.item_info["title"]            
        blacklist = ["used", "new", "as-is", "asis", "shipping"]
        title = utils.filter(title, blacklist)
        
        # TODO: filter results with the word "broken"
        #       keep a cache of results for the same query
        # Problem: can't handle input with a star (causes a key error) u\2605
        
        # Query each review module for this item
        search_mode = "slow"
        search_term = title
        item_scores = []
        
        # Try to get the EPID
        try:
            product_id_type = self.item_info['productId']['@type']
        except KeyError:
            product_id_type = None
        
        if product_id_type == "ReferenceID":
            epid = self.item_info['productId']['__value__']
            item_scores.append(self.ebay_review_module.get_score(epid, "epid"))
        else:
            item_scores.append((-1, -1))
        
        for review_module in self.module_list:
            (score, number_reviews, query) = utils.query_review_module_by_title(review_module, search_term, search_mode)
            item_scores.append((score, number_reviews))
            
            # Change search mode if necessary
            if (score != -1 or number_reviews != -1):
                search_mode = "quick"
                search_term = query
            else:
                search_mode = "slow"
                search_term = title

        self.item_info['score'] = utils.compute_weighted_mean(item_scores)
        self.item_info['individual_scores'] = item_scores
        
        # Assign colors to scores
        if self.item_info['score'] >= 66:
            self.item_info['score_color'] = "high-score"
        elif self.item_info['score'] >= 33:
            self.item_info['score_color'] = "med-score"
        else:
            self.item_info['score_color'] = "low-score"

    def get_item_info(self):
        return self.item_info