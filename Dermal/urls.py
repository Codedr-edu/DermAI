from .views import *
from django.urls import path

urlpatterns = [
    path('', home_view, name='home'),
    path('upload/', upload_image, name='upload_image'),
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('chatbot/', chatbot_view, name='chatbot'),
    path('community/', community_view, name='community'),
    path('create-post/', create_post, name='create_post'),
    path('edit-post/<int:post_id>/', edit_post, name='edit_post'),
    path('delete-post/<int:post_id>/', delete_post, name='delete_post'),
    path('post/<int:post_id>/vote/', toggle_vote, name='toggle_vote'),
    path('post/<int:post_id>/comment/', post_comment, name='post_comment'),
    path('comment/<int:comment_id>/vote/',
         toggle_comment_vote, name='toggle_comment_vote'),
    path('chatbot/api/', chatbot_api, name='chatbot_api'),
    path('result/<int:image_id>/', result_view, name='result'),
    path('pharmacy/', pharmacy, name='pharmacy'),
    path('profile/', your_profile, name='your_profile'),
    path('upload/file/', upload_file, name='upload_file'),
    # path('edit_profile/', edit_profile, name='edit_profile'),
    path('predict/<int:id>', predict, name="predict"),
    #path('health/', health, name='health'),
    #path('memory/', memory_status, name='memory_status'),
]
