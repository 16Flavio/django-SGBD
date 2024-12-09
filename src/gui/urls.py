from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

import gui
from gui import views
from gui.views import home, calendrier, save_customer, tournois, inscription, connexion, \
    administration, utilisateur_details, profil, creationTournoi, tournoi_details, liste_tournois, logout_view, inscription_tournois, desinscription_tournoi, handle404, error_404_view_handler, charte, gerer_utilisateur_admin, changer_username, changer_niveau,supprimer_utilisateur_admin



urlpatterns = [
    path("", home),
    path("home/", home, name="home"),
    path("calendrier/", calendrier, name="calendrier"),
    path ("save/", save_customer),
    path("tournois/<str:tri>/", liste_tournois, name="liste_tournois"),
    path("tournois/details/<int:idtournoi>/", tournoi_details, name="tournoi_details"),
    path("profil/<str:username>/", utilisateur_details, name="profile"),
    path('joueurs/', views.liste_utilisateurs, name='joueurs_default'),  # Utilisé pour la valeur par défaut
    path("joueurs/<str:sport>/", views.liste_utilisateurs, name = "liste_utilisateurs"),
    path("inscription/", inscription, name="inscription"),
    path("connexion/", connexion, name="connexion"),
    path("administration/", administration),
    path("création_tournoi/", creationTournoi),
    path("logout/", logout_view, name="logout"),
    path("tri/", views.liste_utilisateurs, name="liste_utilisateurs"),
    path("inscription_tournois/<int:idtournoi>/",views.page_inscription_tournoi, name="inscription_tournois"),
    path("inscription_tournois/<int:idtournoi>/equipe", views.inscription_tournois, name="inscription_tournois_equipe"),
    path("supprimer_compte/", views.supprimer_compte, name="supprimer_compte"),
    path("desinscription_tournoi/<int:idtournoi>/", desinscription_tournoi, name="desinscription_tournoi"),
    path("desinscrire/<int:instance_id>/", views.desinscrire_equipe, name="desinscrire_equipe"),
    path("tournois/details/<int:idTournoi>/<int:id_match>/", views.actualiserScore, name="enregistrer_points"),
    path("404/", error_404_view_handler, name="error_404"),
    path("changepassword/",views.recupMDP,name="recuperation_mdp"),
    path('request-reset-code/<str:username>/', views.generateMDP, name='request_reset_code'),
    path('verify-reset-code/<str:email>/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/<str:email>/', views.reset_password, name='reset_password'),
    path('charte/', views.charte, name='charte'),
    path ('gerer_utilisateurs/', gerer_utilisateur_admin, name="gerer_utilisateur_admin"),
    path ('gerer_matchs/', views.gerer_match_admin, name="gerer_match_admin"),

    path ("changer_score_match/", views.changer_score),

    path('contact/', views.contact, name='contact'),
    path('admin/', admin.site.urls),
    path('changer_username/',changer_username),
    path('changer_niveau/', changer_niveau),
    path('supprimer_utilisateur/',supprimer_utilisateur_admin)
]
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG is False:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

