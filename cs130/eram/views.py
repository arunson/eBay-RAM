from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson

from cs130.eram.forms import SearchForm
from cs130.eram.other_modules import ebay_module
from cs130.eram.review_modules import review_module, productwiki_module, bestbuy_module, ebay_review_module
from cs130.eram import utils
from review_module_thread import ReviewModuleThread
from item_thread import ItemThread

from operator import itemgetter # for sorting items

import os
import threading
        
# Sequential version of search
def search_sequential(request):
    config_path = os.getcwd() + '/eram/module_config.cfg'
		
    if 'q' in request.GET and request.GET['q']:
        ebay_communicator = ebay_module.EbayInterface(config_path)
        item_ids = ebay_communicator.search(request.GET['q'], 20)

        # This list will be passed to results.html
        item_list = []
        
        # Create list of review modules
        module_list = []
        module_list.append(productwiki_module.ProductwikiInterface(config_path))
        module_list.append(bestbuy_module.BestbuyInterface(config_path))
        ebay_reviewer = ebay_review_module.EbayReviewInterface(config_path)
        
        
        for item_id in item_ids :
            item_info = ebay_communicator.get_item_info_by_id(item_id)

            # Templates cannot handle variable names with leading @ or _
            item_info["sellingStatus"]["currentPrice"]["value"] = item_info["sellingStatus"]["currentPrice"]["__value__"]
            item_info["sellingStatus"]["currentPrice"]["currencyId"] = item_info["sellingStatus"]["currentPrice"]["@currencyId"]
            
            # Run the title through a filter
            title = item_info["title"]            
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
                product_id_type = item_info['productId']['@type']
            except KeyError:
                product_id_type = None
            
            if product_id_type == "ReferenceID":
                epid = item_info['productId']['__value__']
                item_scores.append(ebay_reviewer.get_score(epid, "epid"))
            else:
                item_scores.append((-1, -1))
            
            for review_module in module_list:
                (score, number_reviews, query) = utils.query_review_module_by_title(review_module, search_term, search_mode)
                item_scores.append((score, number_reviews))
                """
                # Change search mode if necessary
                if (score != -1 or number_reviews != -1):
                    search_mode = "quick"
                    search_term = query
                else:
                    search_mode = "slow"
                    search_term = title
                """
            item_info['score'] = utils.compute_weighted_mean(item_scores)
            item_info['individual_scores'] = item_scores
            
            # Assign colors to scores
            if item_info['score'] >= 66:
                item_info['score_color'] = "high-score"
            elif item_info['score'] >= 33:
                item_info['score_color'] = "med-score"
            else:
                item_info['score_color'] = "low-score"
            
            item_list.append(item_info)
        
        
        # Sort the item list by score
        item_list = sorted(item_list, key=itemgetter('score'), reverse=True)
        
        # Convert -1s to N/A (if only there was a faster way than another linear pass...)
        for item in item_list:
            if item['score'] == -1:
                item['score'] = "N/A"
        
        # Create a dictionary of variables to pass to the Django template
        template_variables = dict()
        template_variables['search_query'] = request.GET['q']
        template_variables['item_list'] = item_list
        
        # Needed by the JS code used to display items on Google Maps        
        json_list = simplejson.dumps(item_list)
        template_variables['json_list'] = json_list
        
        search_form = SearchForm()['q']
        template_variables['search_form'] = search_form
   
        return render_to_response('results.html', template_variables)
    else:
        search_form = SearchForm()['q']
        return render_to_response('search.html', {'search_form': search_form})

# Spawns threads for review modules
def search(request):
    config_path = os.getcwd() + '/eram/module_config.cfg'
		
    if 'q' in request.GET and request.GET['q']:
        ebay_communicator = ebay_module.EbayInterface(config_path)
        item_ids = ebay_communicator.search(request.GET['q'], 10)


        # This list will be passed to results.html
        item_list = []
        
        # Passed to review modules
        product_ids = []
        product_titles = []
        
        for item_id in item_ids :
            item_info = ebay_communicator.get_item_info_by_id(item_id)

            # Templates cannot handle variable names with leading @ or _
            item_info["sellingStatus"]["currentPrice"]["value"] = item_info["sellingStatus"]["currentPrice"]["__value__"]
            item_info["sellingStatus"]["currentPrice"]["currencyId"] = item_info["sellingStatus"]["currentPrice"]["@currencyId"]
            
            # Run the title through a filter
            title = item_info["title"]            
            blacklist = ["used", "new", "as-is", "asis", "shipping"]
            title = utils.filter(title, blacklist)
            
            product_titles.append(title)
            
            # Try to get the EPID
            try:
                product_id_type = item_info['productId']['@type']
            except KeyError:
                product_id_type = None
            
            # Prepare product_ids[]
            if product_id_type == "ReferenceID":
                epid = item_info['productId']['__value__']
                product_ids.append(epid)
            else:
                product_ids.append("")
                
            item_list.append(item_info)
        
        # Create list of review modules
        module_list = []
        module_list.append(productwiki_module.ProductwikiInterface(config_path))
        module_list.append(bestbuy_module.BestbuyInterface(config_path))
        ebay_reviewer = ebay_review_module.EbayReviewInterface(config_path)
        
        thread_list = []
        
        ebay_thread = ReviewModuleThread(ebay_reviewer, product_ids, "epid", 15)
        thread_list.append(ebay_thread)
        ebay_thread.start()
        
        for module in module_list:
            module_thread = ReviewModuleThread(module, product_titles, "title", 5)
            thread_list.append(module_thread)
            module_thread.start()
        
        scores_list = []
        for module_thread in thread_list:
            module_thread.join()
            scores_list.append(module_thread.get_scores())
        
        # "Invert" the list so that we can take the average scores
        scores_list = zip(*scores_list)

        
        # Average the scores
        averaged_scores = []
        for item_scores, item_info in zip(scores_list, item_list):
            item_info['score'] = utils.compute_weighted_mean(item_scores)
            item_info['individual_scores'] = item_scores
            
            # Assign colors to scores
            try:
                if item_info['score'] >= 66:
                    item_info['score_color'] = "high-score"
                elif item_info['score'] >= 33:
                    item_info['score_color'] = "med-score"
                else:
                    item_info['score_color'] = "low-score"
            except KeyError:
                # If there was no score then it should be "low-score"
                item_info['score_color'] = "low-score"
        
        
        # Sort the item list by score
        item_list = sorted(item_list, key=itemgetter('score'), reverse=True)
        
        # Convert -1s to N/A (if only there was a faster way than another linear pass...)
        for item in item_list:
            try:
                if item['score'] == -1:
                    item['score'] = "N/A"
            except KeyError:
                item['score'] = "N/A"
        
        # Create a dictionary of variables to pass to the Django template
        template_variables = dict()
        template_variables['search_query'] = request.GET['q']
        template_variables['item_list'] = item_list
        
        # Needed by the JS code used to display items on Google Maps
        json_list = simplejson.dumps(item_list)
        template_variables['json_list'] = json_list

        search_form = SearchForm()['q']
        template_variables['search_form'] = search_form
   
        return render_to_response('results.html', template_variables)
    else:
        search_form = SearchForm()['q']
        return render_to_response('search.html', {'search_form': search_form})
