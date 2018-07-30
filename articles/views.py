
# EXTERNAL LIBRARIES
from datetime import datetime, timedelta
import time
import json
import uuid

# DJANGO MODULES
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import last_modified
from django.views.decorators.cache import cache_page, cache_control
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q

# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

# APPLICATION CODE
from .models import SharticleUser, Article, Tag
from articles import tasks










# =============================================================================
# REGISTER view ===============================================================
# =============================================================================

#@cache_control(max_age=3600, public=True)
#@cache_page(60*60)

def register(request):
    # If the method is POST
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password1"]

        try:
            # Create a user and save it to the database
            user = SharticleUser.objects.create_user(username, username + '@domain.com', password)

            # Insert user object in the cache !!!
            # cache.set(username, user, None)
            
            #return HttpResponse("Your account has been created, " + user.username + ".")
            return redirect('articles:login')

        # If the user already exists
        except IntegrityError:
            context = { 'user_already_exists': True, 'username': username }
            return render(request, 'articles/register.html', context)

    # If the method is GET
    return render(request, 'articles/register.html')





# =============================================================================
# LOGIN view ==================================================================
# =============================================================================

#@cache_control(max_age=3600, public=True)
#@cache_page(60*60)

def login(request):
    # If the method is POST
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        # Check user credentials
        user = authenticate(request, username = username, password = password)
        if user is not None:
            # Log in user
            auth_login(request, user)
            # SUBSTITUIR "request.user.username" POR "user.username" PARA EVITAR ACESSOS À BASE DE DADOS
            
            response = redirect('articles:edit_profile')
            response.set_cookie('username', username)
            return response
            # return HttpResponse("You have been successfully logged in, " + request.user.username  + "!")

        # If the user does not exist or the password is wrong
        else:
            context = { 'wrong_credentials': True }
            return render(request, 'articles/login.html', context)
    
    # If the method is GET
    return render(request, 'articles/login.html')










# =============================================================================
# LOGOUT view =================================================================
# =============================================================================

def logout(request):
    start = time.time()

    # Update user status
    auth_logout(request)
    
    end = time.time()
    print(1000*(end - start))
    
    # Redirect to login page
    response = redirect('articles:login')
    response.delete_cookie('username')
    return response










# =============================================================================
# PROFILE view ================================================================
# =============================================================================


def last_modified_func(request, username):
    try:
        start = time.time()
        selected_user = SharticleUser.objects.get(username = username)
        end = time.time()
        print("SELECT user FROM DATABASE:" + str(1000*(end - start)))
        return selected_user.profile_last_modified_date
        
    # If the user does not exist
    except SharticleUser.DoesNotExist:
        return datetime(2019,1,1)



@last_modified(last_modified_func)

def profile(request, username):
    try:
        selected_user = SharticleUser.objects.get(username = username)

        # Retrieve articles from cache
        articles = cache.get(username + '_articles')
        if articles is None:
            print('from DATABASE')
            # Retrieve articles from database
            articles = Article.objects.filter(author = username, already_published = True)
            # Update cache with articles list
            cache.set(username + '_articles', articles, None)
        else:
            print('from CACHE')

        context = {'selected_user' : selected_user, 'articles' : articles}
        
        response = render(request, 'articles/profile.html', context = context)
        response['Cache-Control'] = 'no-cache'
        return response
    # If the user does not exist
    except SharticleUser.DoesNotExist:
        return HttpResponse("User does not exist!")










# =============================================================================
# EDIT PROFILE view ===========================================================
# =============================================================================

def some_func(request):
    user = request.user
    if user.is_authenticated:
        # Return user's profile last modified date
        return user.profile_last_modified_date
    else:
        # Redirect to login page (user is not logged in)
        return datetime(2018,1,1)



@last_modified(some_func)

def edit_profile(request):
    # If the user is authenticated
    if request.user.is_authenticated:

        # If the method is POST
        if request.method == "POST":
            theUser = request.user

            # Update user's resume
            theUser.resume = request.POST['resume']
            
            # Update user's first name
            if request.POST['first_name']:
                theUser.first_name = request.POST['first_name']
            
            # Update user's last name
            if request.POST['last_name']:
                theUser.last_name = request.POST['last_name']
            
            # Update user's email
            if request.POST['email']:
                theUser.email = request.POST['email']
            
            # Update user's profile last modified date
            theUser.profile_last_modified_date = datetime.now()

            # Save user object to the database
            theUser.save()
            return render(request, 'articles/edit_profile.html')
        
        # If the method is GET
        else:
            start = time.time()
            t = render(request, 'articles/edit_profile.html')
            # cache.set('edit_profile_page', t)
            end = time.time()
            print(1000*(end - start))

            start = time.time()
            cache.delete('edit_profile_page')
            #r = cache.get('edit_profile_page')
            end = time.time()
            print(1000*(end - start))

            if ("a"!="a"):
                print("Damn!")
            else:
                print ("YEAH!!")

            return t

    # If the user is not authenticated
    else:
        # Redirect to login page
        return redirect('articles:login')










# =============================================================================
# ARTICLES view ===============================================================
# =============================================================================

def drafts_last_modified_func(request):
    user = request.user
    if request.user.is_authenticated:
        return user.drafts_last_modified_date
    else:
        return datetime(2018,1,1)



@last_modified(drafts_last_modified_func)

def draft_articles_view(request):  
    # If the user is authenticated
    if request.user.is_authenticated:  
        user = request.user 

        
        # PLAYING AROUND WITH THE CACHE
        # article1 = Article(author = 'author', title = 'title', description = 'description', content = 'content', image_path = 'image_name', tags=[])
        # cache.set('article', article1, None)
        # article2 = cache.get('article')
        # print(article2.image_path)
        
        # Store articles in cache
        # cache.set(request.user.username + 'articles', articles, None)
        # Retrieve articles from cache
        # articles = cache.get(request.user.username + 'articles')
        # END_OF_PLAY


        # Retrieve articles from the db
        articles = Article.objects.filter(author = user.username, already_published = False)
        # Construct response
        response = render(request, 'articles/articles.html', context = {'drafts': True, 'articles': articles})
        response['Cache-Control'] = 'no-cache'
        return response
    
    # If the user is not authenticated
    else:
        # Redirect to login page
        return redirect('articles:login')





def articles_last_modified_func(request):
    user = request.user
    if request.user.is_authenticated:
        return user.articles_last_modified_date
    else:
        return datetime(2018,1,1)


@last_modified(articles_last_modified_func)

def published_articles_view(request):    
    # If the user is authenticated
    if request.user.is_authenticated:  
        user = request.user

        # Retrieve articles from the db
        articles = Article.objects.filter(author = user.username, already_published = True)
        
        # Construct response
        response = render(request, 'articles/articles.html', context = {'published': True, 'articles': articles})
        response['Cache-Control'] = 'no-cache'
        return response
    
    # If the user is not authenticated
    else:
        # Redirect to login page
        return redirect('articles:login')





@last_modified(articles_last_modified_func)

def json_published_articles(request):
    # If the user is authenticated
    if request.user.is_authenticated:  
        # Get list of articles from db
        user = request.user
        articles = Article.objects.filter(author = user.username, already_published = True)  

        # Serialize response in JSON format
        json_data = { 'articles': list(articles.values('id', 'title', 'description', 'author', 'image_path', 'last_modified_date')),
                    'author': { 'username' : user.username, 'resume' : user.resume, 'profileImagePath' : user.profileImagePath } }
        
        response = JsonResponse(json_data)
        response['Cache-Control'] = 'no-cache'
        return response
    
    # If the user is not authenticated
    else:
        # Return unsuccessful response
        return JsonResponse({'success' : False})
    




@last_modified(drafts_last_modified_func)

def json_draft_articles(request):
    # If the user is authenticated
    if request.user.is_authenticated:  
        # Get list of articles from db
        user = request.user
        articles = Article.objects.filter(author = user.username, already_published = False)

        # Serialize response in JSON format
        json_data = { 'articles': list(articles.values('id', 'title', 'description', 'author', 'image_path', 'last_modified_date')),
                    'author': { 'username' : user.username, 'resume' : user.resume, 'profileImagePath' : user.profileImagePath } }

        response = JsonResponse(json_data)
        response['Cache-Control'] = 'no-cache'
        return response
    
    # If the user is not authenticated
    else:
        # Return unsuccessful response
        return JsonResponse({'success' : False})










# =============================================================================
# CREATE NEW ARTICLE view =====================================================
# =============================================================================

def create_article(request):    
    user = request.user

    # If the method is POST
    if request.method == "POST":

        # Retrieve POST data
        if request.POST["title"]:
            title = request.POST["title"]
        if request.POST["description"]:
            description = request.POST["description"]     
        
        # In case of successful image upload  
        if request.FILES:
            image = request.FILES["file"]     
            image_extension = image.name.split(".")[-1]        
            static_url = '/home/joao/Desktop/staticfiles/articles/'
            image_name = 'article_' + str(uuid.uuid4()) + '.' + image_extension
            dir = static_url + image_name

            # Write image to disk
            with open(dir, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

        # If no image was uploaded
        else:
            image_name = ''
                
        # Create new article and save it to the db
        article = Article(author = user.username, title = title, description = description, content='', image_path = image_name, tags=[])
        article.save()

        # Increment user's draft articles count
        user.number_of_drafts = user.number_of_drafts + 1

        # Update user draft articles' last modified date (used for HTTP caching)
        current_date = datetime.now()
        user.drafts_last_modified_date = current_date
        user.save()

        # Return article editing view
        response = render(request, 'articles/edit_article.html', context = {'article': article, 'topics': dict(Article.TOPICS).items()})
        return response










# =============================================================================
# EDIT ARTICLE view ===========================================================
# =============================================================================

def article_last_modified_func(request, id):
    try:
        return Article.objects.get(id = id).last_modified_date
    # If the requested article does not exist
    except Article.DoesNotExist:
        return datetime(2018,1,1)


@last_modified(article_last_modified_func)

def edit_article(request, id):   
    user = request.user
    
    # Check user authentication status
    if user.is_authenticated:

        try:
            # Retrieve article from db
            article = Article.objects.get(id = id)

            # Check if user is the author and the article is a draft
            if user.username == article.author and not article.already_published:
                response = render(request, 'articles/edit_article.html', context = {'article': article, 'topics': dict(Article.TOPICS).items()})    
            
            # If the user is not the article's author or the article is not a draft
            else:
                response = HttpResponse("You can not edit this article!")

            response['Cache-Control'] = 'no-cache'
            return response

        # If the article does not exist
        except Article.DoesNotExist:
            return HttpResponse("There is no article with id " + id + "!")
    
    # If the user is not authenticated, redirect to login page
    else:
        return redirect('articles:login')










# =============================================================================
# DELETE ARTICLE view =========================================================
# =============================================================================

def delete_article(request, id):  
    # If the method is POST
    if request.method == "POST":  
        user = request.user
        
        try:
            article = Article.objects.get(id = id)
            
            # Check if user is the author
            if user.username == article.author:
                if not article.already_published:
                    draft = True
                else:
                    draft = False

                # Remove article from db
                article.delete()

                current_date = datetime.now()
                
                if draft:
                     # Decrement user's draft articles count
                    user.number_of_drafts = user.number_of_drafts - 1

                    # Update user draft articles' last modified date (used for HTTP caching)
                    # ( No need to update user.profile_last_modified_date, 
                    #   since the profile view does not change )
                    user.drafts_last_modified_date = current_date

                else:
                    # Decrement user's published articles count
                    user.number_of_articles = user.number_of_articles - 1

                    # Update user profile + published articles' last modified date (used for HTTP caching)
                    user.profile_last_modified_date = current_date
                    user.articles_last_modified_date = current_date
                    
                user.save()
        
                # ??? Update article's last modified date (used for HTTP caching) ???
                # ??? ... ???

                # Return successful JSON encoded response
                return JsonResponse({'success' : True})

            # If the user is not the article's author
            else:
                # Return unsuccessful response
                return JsonResponse({'success' : False, 'error_message' : "You can not delete this article!"})

        # If the article does not exist
        except Article.DoesNotExist:
            # Return unsuccessful response
            return JsonResponse({'success' : False, 'error_message' : "There is no article with id " + id + "!"})










# =============================================================================
# SAVE ARTICLE view ===========================================================
# =============================================================================

def save_article(request, id):    
    # If the method is POST
    if request.method == "POST":
        
        if request.POST["content"]:
            user = request.user
            new_content = request.POST["content"]

            # ===========================================================================================
            # article = Article.objects.filter(id = id)
            # if user.username == article.author and not article.already_published:
            #     article.update(content = new_content))
            #     ...
            # ===========================================================================================

            current_date = datetime.now()

            # Update article in db      
            number_of_updates = Article.objects.filter(id = id, author = user.username, already_published = False).update(content = new_content, last_modified_date = current_date)
            
            # Check if user is the author and the article is a draft
            if number_of_updates == 1:                    
                
                # Return successful JSON encoded response
                return JsonResponse({'success' : True})
            
            # If user is not the article's author or the article is not a draft or does not exist
            else:
                # Return unsuccessful response
                return JsonResponse({'success' : False, 'error_message' : "You can not save this article!"})










# =============================================================================
# PUBLISH ARTICLE view ========================================================
# =============================================================================

def publish_article(request, id):  
    # If the method is POST
    if request.method == "POST":          

        user = request.user
        new_tags = []
        
        if request.POST["tags"]:
            for tag in request.POST["tags"].split(","):
                new_tags.append(Tag(tag = tag))
        
        if request.POST["topic"]:
            topic = request.POST["topic"]

        # ===========================================================================================
        # article = Article.objects.filter(id = id)
        # if user.username == article.author and not article.already_published:
        #     article.update(already_published = True, tags = new_tags))
        #     ...
        # ===========================================================================================

        current_date = datetime.now()

        # Update article in db      
        number_of_updates = Article.objects.filter(id = id, author = user.username, already_published = False).update(already_published = True, tags = new_tags, topic = topic, last_modified_date = current_date, pub_date = current_date)
        
        # Check if user is the author and the article is a draft
        if number_of_updates == 1:
                    
            # Update user's number of draft + published articles
            user.number_of_drafts = user.number_of_drafts - 1
            user.number_of_articles = user.number_of_articles + 1

            # Update user profile + draft + published articles' last modified date (used for HTTP caching)
            user.profile_last_modified_date = current_date
            user.drafts_last_modified_date = current_date
            user.articles_last_modified_date = current_date
            user.save()                
            
            # Return successful JSON encoded response
            return JsonResponse({'success' : True})

        # If user is not the article's author or the article is not a draft or does not exist
        else:
            # Return unsuccessful response
            return JsonResponse({'success' : False, 'error_message' : "You can not publish this article!"})
        










# =============================================================================
# ... view ====================================================================
# =============================================================================

def unvariable_view(request):
    response = render(request, 'articles/unvariable.html', context = {'current_date' : datetime.now().second })
    response["Cache-control"] = "max-age=30"
    return response







def upload_article_image(request):
    user = request.user

    # If the method is POST
    if request.method == "POST":

        # Retrieve POST data
        if request.POST["article_id"]:
            id = request.POST["article_id"]
        
        # In case of successful image upload  
        if request.FILES:
            image = request.FILES["uploaded_image"]     
            image_extension = image.name.split(".")[-1]        
            static_url = '/home/joao/Desktop/staticfiles/articles/'
            image_name = 'article_' + id + "_" + str(uuid.uuid4()) + '.' + image_extension
            dir = static_url + image_name

            # Write image to disk
            with open(dir, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

        # If no image was uploaded
        else:
            image_name = ''
         

        return JsonResponse({'success' : True, 'imageSrc' : image_name})




















# =============================================================================
# TEST view ===================================================================
# =============================================================================

def test_view(request):
    from .tests import nosql_testing
    nosql_testing()
    return HttpResponse("Done")










# =============================================================================
# READ ARTICLE view ===========================================================
# =============================================================================


def read_article(request, id):   
    
    try:
        # Retrieve article from db
        article = Article.objects.get(id = id)
        
        # Retrieve author from CACHE / DATABASE
        author = SharticleUser.objects.get(username = article.author)

        # Generate response
        response = render(request, 'articles/read_article.html', context = {'article': article, 'author': author}) 
        response['Cache-Control'] = 'max-age=1000'
        return response

    # If the article does not exist
    except Article.DoesNotExist:
        return HttpResponse("There is no article with id " + id + "!")










# =============================================================================
# SEARCH BY TOPIC view ========================================================
# =============================================================================


def search_by_topic(request, topic = 'WP'):   

    if topic in (
        Article.ARTIFICIAL_INTELLIGENCE,
        Article.WEB_PROGRAMMING,
        Article.SOFTWARE_ENGINEERING,
        Article.DATA_SCIENCE,
        Article.CRYPTOGRAPHY,
    ):
        '''
        # Retrieve articles from db
        qs = Article.objects.filter(topic = topic).order_by('pub_date').all()
        paginator = Paginator(qs, 50)
        articles = paginator.page(1).object_list
        '''

        # Retrieve articles from cache
        articles = cache.get(topic + '1')
        
        # Generate response
        response = render(request, 'articles/search_by_topic.html', context = {'articles': articles, 'topic': dict(Article.TOPICS)[topic], 'topic_key': topic, 'topics': dict(Article.TOPICS).items()}) 
        
        # Cache response for 30 minutes
        if cache.get('topics_expiry_date') is None:
            cache.set('topics_expiry_date', datetime.now() + timedelta(minutes = 30), None)
        expiry_date = cache.get('topics_expiry_date')
        response['Expires'] = expiry_date
        return response


    # If the topic does not exist
    else:
        return HttpResponse("Topic " + topic + " does not exist!")
    






def json_search_by_topic(request, topic, page_number = 1):

    # Check if the topic exists
    if topic in (
        Article.ARTIFICIAL_INTELLIGENCE,
        Article.WEB_PROGRAMMING,
        Article.SOFTWARE_ENGINEERING,
        Article.DATA_SCIENCE,
        Article.CRYPTOGRAPHY,
    ):
        
        '''
        try:
            # Retrieve articles from db
            qs = Article.objects.filter(topic = topic).order_by('pub_date').all()
            paginator = Paginator(qs, 50)
            articles_list = paginator.page(page_number).object_list
            articles = list(articles_list.values('id', 'title', 'description', 'author', 'image_path', 'last_modified_date'))
        except EmptyPage:
            articles = None
        '''

        # Retrieve articles from cache
        articles = cache.get(topic + str(page_number))
                
        # Serialize response in JSON format
        json_data = { 'articles': articles }
        
        response = JsonResponse(json_data)

        # Cache response for 30 minutes
        expiry_date = cache.get('topics_expiry_date')
        response['Expires'] = expiry_date
        return response
    
    # If the topic does not exist
    else:
        # Return unsuccessful response
        return JsonResponse({'success' : False})










# =============================================================================
# SEARCH ARTICLES/PEOPLE view =================================================
# =============================================================================


def search(request):

    '''
    import string
    import random
    # Create some users
    for i in range(100):
        username = ''.join(random.choice(string.ascii_lowercase) for x in range(5 + i%2 + i%3))
        user = SharticleUser.objects.create_user(username, username + '@domain.com', 'pass')
    '''

    # If the method is GET
    if request.method == "GET":

        # Search for articles
        if request.GET.get("articles"):
            keyword = request.GET["articles"].split(' ')[0]
            page_number = int(request.GET["page"])

            #users = SharticleUser.objects.raw('SELECT id FROM sharticle_user LIMIT 1')

            q = Q(title__contains = keyword) | Q(description__contains = keyword)
            
            #qs = Article.objects.filter(q).order_by('id')
            #, already_published = True)

            #qs = Article.objects.raw('{$or: [{title:/1/}, {description:/ar/}]}')

            articles = Article.objects.mongo_find({'$and': [{'$text': { '$search': keyword }}, {'already_published':True}]}, {'_id':0})
            #.skip(page_number-1).limit(1)
            print(Article.objects.filter(tags={'tag':'taggy'}))
            
            new_list = []
            for article in articles:
                new_list.append(list(article.values()))

            #paginator = Paginator(articles, 5)
            #articles = paginator.page(page_number).object_list


            # Serialize response in JSON format
            if articles:
                json_data = { 'articles': new_list }
            else:
                json_data = { 'articles': None }                
            response = JsonResponse(json_data)
            return response     


        # Search for people
        elif request.GET.get("people"):
            keyword = request.GET["people"].split(' ')[0]
            page_number = int(request.GET["page"])

            q = Q(username__contains = keyword)
            qs = SharticleUser.objects.filter(q).order_by('id')
            #, already_published = True)

            paginator = Paginator(qs, 5)
            people = paginator.page(page_number).object_list

            if people:
                json_data = { 'people': list(people.values()) }
            else:
                json_data = { 'people': None }  
            response = JsonResponse(json_data)
            return response     

        
        # HTTP request
        else:
            return render(request, 'articles/search.html')