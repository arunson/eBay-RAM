from django.http import HttpResponse
from django.shortcuts import render_to_response

from cs130.eram.forms import SearchForm
    
def search(request):
    if 'q' in request.GET and request.GET['q']:
        return HttpResponse("You tried to search for something.")
    else:
        search_form = SearchForm()
    
    return render_to_response('search.html', {'search_form': search_form})

