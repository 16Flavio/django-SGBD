import random
from typing import Match

from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import make_aware

from .models import *
from gui.models import Utilisateur, Tournoi
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth import authenticate
from django.db.models import Q
from datetime import datetime, time, timedelta
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseNotFound
from .forms import ContactForm
from django.conf import settings

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()

    form = ContactForm()

    # Si le formulaire est soumis
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Récupérer les données du formulaire
            nom = form.cleaned_data['nom']
            email = form.cleaned_data['email']
            sujet = form.cleaned_data['sujet']
            message = form.cleaned_data['message']

            send_mail(
                f"Message de {nom} - {sujet}",
                message,
                email,
                ['service.raqtour@gmail.com'],
                fail_silently=False,
            )
            return render(request, 'gui/success.html', {"current_sport":current_sport,"current_tab" : "home" , "is_admin": is_admin})

    aujourdhui = datetime.now().date()
    liste_tournois_tennis = []
    liste_tournois_badminton = []
    liste_tournois_all = Tournoi.objects.all()
    for tournoi in Tournoi.objects.all():
        if tournoi.periode_debut > aujourdhui and current_sport == "Tennis" and tournoi.periode_debut < aujourdhui + timedelta(days=7):
            liste_tournois_tennis.append(tournoi)
        elif tournoi.periode_debut > aujourdhui and current_sport == "Badminton" and tournoi.periode_debut < aujourdhui + timedelta(days=7):
            liste_tournois_badminton.append(tournoi)
        elif current_sport == None:
            if Utilisateur.objects.filter(tournoi=tournoi, user__groups__name="Administrateurs").first().sport_type.sport_type == "Tennis":
                liste_tournois_tennis.append(tournoi)
            elif Utilisateur.objects.filter(tournoi=tournoi, user__groups__name="Administrateurs").first().sport_type.sport_type == "Badminton":
                liste_tournois_badminton.append(tournoi)
    return render(request, 'gui/home.html', context={ 'form': form,"liste_tournois_all" : liste_tournois_all,"liste_tournois_badminton":liste_tournois_badminton,"liste_tournois_tennis":liste_tournois_tennis,"current_sport":current_sport,"current_tab" : "home" , "is_admin": is_admin})

'''
def calendrier(request):
    is_admin = request.user.groups.filter(name="Administrateur").exists()
    return render(request, 'gui/calendrier.html', context={"current_tab" : "calendrier", "is_admin" : is_admin })
'''
def save_customer(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    customer_name = request.POST.get('customer_name', '')
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    return render(request, "gui/welcome.html", context={"current_sport":current_sport,'customer_name': customer_name, "is_admin" : is_admin})

def tournois(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    return render(request, 'gui/tournois.html', context={"current_sport":current_sport,"current_tab" : "tournois", "is_admin" : is_admin})

def inscription_tournois(request,idtournoi):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    Use = request.user
    userConnected = Utilisateur.objects.get(user=Use)
    tournoi = Tournoi.objects.get(idtournoi=idtournoi)
    liste_equipes = []
    for equipe in userConnected.equipe.all():
        joueur1 = Utilisateur.objects.filter(equipe=equipe)[0]
        joueur2 = Utilisateur.objects.filter(equipe=equipe)[1]
        if joueur1.user.groups.name == "Supprimé" or joueur2.user.groups.name == "Supprimé":
            continue
        liste_equipes.append(equipe)
    if tournoi.type.type == "Double mixte":
        liste_teammates = Utilisateur.objects.filter(sport_type=userConnected.sport_type).exclude(sexe=userConnected.sexe).exclude(user=userConnected.user).exclude(user__groups__name="Administrateurs").exclude(user__groups__name="Supprimé").exclude(equipe__tournoi=tournoi)
    elif tournoi.type.type == "Double dames":
        liste_teammates = Utilisateur.objects.filter(sport_type=userConnected.sport_type, sexe=userConnected.sexe).exclude(user=userConnected.user).exclude( user__groups__name="Administrateurs").exclude(user__groups__name="Supprimé").exclude(equipe__tournoi=tournoi)
    elif tournoi.type.type == "Double hommes":
        liste_teammates = Utilisateur.objects.filter(sport_type=userConnected.sport_type, sexe=userConnected.sexe).exclude(user=userConnected.user).exclude( user__groups__name="Administrateurs").exclude(user__groups__name="Supprimé").exclude(equipe__tournoi=tournoi)

    if request.method == 'POST':
        if request.POST.get('selectedTeam') == '':
            TeamName = request.POST.get('teamName')
            usernameTeamMate = request.POST.get('teamMate')
            if Equipe.objects.filter(nom_equipe=TeamName).exists() and not Utilisateur.objects.filter(equipe=Equipe.objects.get(nom_equipe=TeamName), user__username=usernameTeamMate).exists():
                messages.error(request, "Ce nom d'équipe existe déjà, veuillez en choisir un autre.")
                return render(request, 'gui/inscription_tournois.html', context={"liste_equipes" : liste_equipes, "liste_teammates" : liste_teammates,"current_sport": current_sport,'tournoi': tournoi, "is_admin" : is_admin,"current_tab" : "tournois"})
            elif Equipe.objects.filter(nom_equipe=TeamName).exists() and Utilisateur.objects.filter(equipe=Equipe.objects.get(nom_equipe=TeamName), user__username=usernameTeamMate).exists():
                Equipe.objects.get(nom_equipe=TeamName).tournoi.add(tournoi)
                messages.success(request, "Votre inscription et celle de votre coéquipier ont bien été effectuée")
                return redirect("home")
            if not User.objects.filter(username=usernameTeamMate).exists():
                messages.error(request, "Ce nom d'utilisateur n'existe pas! Veuillez entrez le bon username ou demander à votre coéquipier de s'inscire ! ")
                return render(request, 'gui/inscription_tournois.html', context={"liste_equipes" : liste_equipes, "liste_teammates" : liste_teammates,"current_sport":current_sport,'tournoi': tournoi, "is_admin" : is_admin,"current_tab" : "tournois"})
            if Utilisateur.objects.filter(user__username=usernameTeamMate, equipe__tournoi=tournoi).exists():
                messages.error(request,"Cette personne est déja inscrite au tournoi!")
                return render(request, 'gui/inscription_tournois.html', context={"liste_equipes" : liste_equipes, "liste_teammates" : liste_teammates,"current_sport":current_sport,'tournoi': tournoi, "is_admin": is_admin,"current_tab" : "tournois"})

            if tournoi.type.type == "Double mixte":
                if Utilisateur.objects.get(user=User.objects.get(username=usernameTeamMate)).sexe.sexe == Utilisateur.objects.get(user=Use).sexe.sexe:
                    messages.error(request, "Vous et votre cooéquipier devez être de sexe opposé!")
                    return render(request, 'gui/inscription_tournois.html', context={"liste_equipes" : liste_equipes, "liste_teammates" : liste_teammates,"current_sport":current_sport,'tournoi': tournoi, "is_admin": is_admin,"current_tab" : "tournois"})
            elif tournoi.type.type == "Double dames":
                if Utilisateur.objects.get(user=User.objects.get(username=usernameTeamMate)).sexe.sexe != Utilisateur.objects.get(user=Use).sexe:
                    messages.error(request, "Votre cooéquipier doit être une femme!")
                    return render(request, 'gui/inscription_tournois.html', context={"liste_equipes" : liste_equipes, "liste_teammates" : liste_teammates,"current_sport": current_sport,'tournoi': tournoi, "is_admin": is_admin,"current_tab" : "tournois"})
            elif tournoi.type.type == "Double hommes":
                if Utilisateur.objects.get(
                        user=User.objects.get(username=usernameTeamMate)).sexe.sexe != Utilisateur.objects.get(user=Use).sexe.sexe:
                    messages.error(request, "Votre cooéquipier doit être un homme!")
                    return render(request, 'gui/inscription_tournois.html', context={"liste_equipes" : liste_equipes, "liste_teammates" : liste_teammates,"current_sport": current_sport,'tournoi': tournoi, "is_admin": is_admin,"current_tab" : "tournois"})
        elif request.POST.get('selectedTeam') != '':
            TeamName = request.POST.get('selectedTeam')
        """
        if tournoi.type.type not in ["Double mixtes", "Double dames", "Double hommes"] :
            messages.success(request, "Votre inscription a bien été effectuée")
            return redirect('tournoi_details', idtournoi=idtournoi)
        """
        """
        if Utilisateur.objects.get(user=Use).tournoi.filter(idtournoi=idtournoi).exists():
            messages.error(request,"Vous êtes déja inscrit à ce tournoi! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        """
        if Equipe.objects.filter(nom_equipe=TeamName).exists():
            Equipe.objects.get(nom_equipe=TeamName).tournoi.add(tournoi)
        else:
            team = Equipe(nom_equipe=TeamName)
            team.save()

            utili = Utilisateur.objects.get(user=Use)
            if utili.user.is_active or utili.user.groups.filter(name="Supprimé").exists():
                utili.equipe.add(team)
            equipier = Utilisateur.objects.get(user=User.objects.get(username=usernameTeamMate))
            if equipier.user.is_active or equipier.user.groups.filter(name="Supprimé").exists():
                equipier.equipe.add(team)
            Equipe.objects.get(nom_equipe=TeamName).tournoi.add(tournoi)
            utili.equipe.add(Equipe.objects.get(nom_equipe=TeamName))
            equipier.equipe.add(Equipe.objects.get(nom_equipe=TeamName))

        user1 = Utilisateur.objects.get(equipe=Equipe.objects.get(nom_equipe=TeamName))[0]
        email1 = user1.user.email
        user2 = Utilisateur.objects.get(equipe=Equipe.objects.get(nom_equipe=TeamName))[1]
        email2 = user1.user.email

        html_message = render_to_string('gui/tournoi_inscription_double.html', {
            'user1': user1,  # Passer l'utilisateur pour le personnaliser dans le template
            'user2' : user2,
            'equipe' : Equipe.objects.get(nom_equipe=TeamName),
            'site_url': 'https://raqtour.pythonanywhere.com',  # L'URL de ton site
            'tournoi' : Tournoi.objects.get(idtournoi=idtournoi),
        })
        send_mail(
            f"Inscription au Tournoi {Tournoi.objects.get(idtournoi=idtournoi).nom} réussie !",  # Sujet
            "Ceci est un message automatique.",
            # Message texte brut (en cas de problème avec HTML)
            'service.raqtour@gmail.com',  # Ton adresse e-mail
            [email1],  # Adresse de l'utilisateur
            html_message=html_message,  # Corps HTML de l'email
            fail_silently=False
        )
        send_mail(
            f"Inscription au Tournoi {Tournoi.objects.get(idtournoi=idtournoi).nom} réussie !",  # Sujet
            "Ceci est un message automatique.",
            # Message texte brut (en cas de problème avec HTML)
            'service.raqtour@gmail.com',  # Ton adresse e-mail
            [email2],  # Adresse de l'utilisateur
            html_message=html_message,  # Corps HTML de l'email
            fail_silently=False
        )

        messages.success(request, "Votre inscription et celle de votre coéquipier ont bien été effectuée")
        return redirect("home")
    return render(request, 'gui/inscription_tournois.html', context={"liste_equipes" : liste_equipes, "liste_teammates" : liste_teammates,"current_sport": current_sport,'tournoi': tournoi, "is_admin" : is_admin, "current_tab" : "tournois"})


def page_inscription_tournoi(request, idtournoi):
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    Use = request.user
    user = Utilisateur.objects.get(user=Use)
    tournoi = get_object_or_404(Tournoi, idtournoi=idtournoi)

    gerants = Utilisateur.objects.filter(tournoi=tournoi, user__groups__name="Administrateurs")
    gerant = gerants.first()
    sport_gerant = gerant.sport_type.sport_type

    if tournoi.type.type[:6] == "Simple":
        if not Use.is_authenticated:
            messages.error(request, "Vous devez être connecté! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        if Utilisateur.objects.filter(tournoi=tournoi, user=request.user).exists():
            messages.error(request, "Vous êtes déja inscrit à ce tournoi! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        if Utilisateur.objects.get(user=Use).sport_type.sport_type != sport_gerant:
            messages.error(request, "Vous ne pratiquez pas le bon sport! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        if tournoi.type.type[7:] == "dames" and Utilisateur.objects.get(user=Use).sexe.sexe == "Homme":
            messages.error(request, "Vous devez être une femme pour participer à ce tournoi! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        elif tournoi.type.type[7:] == "hommes" and Utilisateur.objects.get(user=Use).sexe.sexe == "Femme":
            messages.error(request, "Vous devez être un homme pour participer à ce tournoi! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        messages.success(request, "Votre inscription a bien été effectuée")

        html_message = render_to_string('gui/tournoi_inscription_simple.html', {
            'user': user,
            'site_url': 'https://raqtour.pythonanywhere.com',  # L'URL de ton site
            'tournoi': Tournoi.objects.get(idtournoi=idtournoi),
        })
        send_mail(
            f"Inscription au Tournoi {Tournoi.objects.get(idtournoi=idtournoi).nom} réussie !",  # Sujet
            "Ceci est un message automatique.",
            # Message texte brut (en cas de problème avec HTML)
            'service.raqtour@gmail.com',  # Ton adresse e-mail
            [user.user.email],  # Adresse de l'utilisateur
            html_message=html_message,  # Corps HTML de l'email
            fail_silently=False
        )

        Utilisateur.objects.get(user=request.user).tournoi.add(tournoi)

        return redirect('liste_tournois', tri=default)
    elif tournoi.type.type[:6] == "Double":
        if not Use.is_authenticated:
            messages.error(request, "Vous devez être connecté! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        if Utilisateur.objects.filter(equipe__tournoi=tournoi, user=request.user).exists():
            messages.error(request, "Vous êtes déja inscrit à ce tournoi! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        if Utilisateur.objects.get(user=Use).sport_type.sport_type != sport_gerant:
            messages.error(request, "Vous ne pratiquez pas le bon sport! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        if tournoi.type.type[7:] == "dames" and Utilisateur.objects.get(user=Use).sexe.sexe == "Homme":
            messages.error(request, "Vous devez être une femme pour participer à ce tournoi! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        elif tournoi.type.type[7:] == "hommes" and Utilisateur.objects.get(user=Use).sexe.sexe == "Femme":
            messages.error(request, "Vous devez être un homme pour participer à ce tournoi! ")
            return redirect('tournoi_details', idtournoi=idtournoi)
        return redirect('inscription_tournois_equipe', idtournoi=idtournoi)

def profil(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    return render(request, 'gui/profil.html', context={"current_sport": current_sport,"current_tab" : "profil", "is_admin" : is_admin})

def administration(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    return render(request, 'gui/administration.html', context={"current_sport": current_sport,"current_tab": "administration", "is_admin" : is_admin})

def utilisateurs_profil(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    utilisateurs = Utilisateur.objects.all()
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    return render(request, "gui/profil.html", context={"current_sport": current_sport,"current_tab" : "utilisateurs", "utilisateurs": utilisateurs, "is_admin" : is_admin})

def creationTournoi(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    if request.method == 'POST':
        nom = request.POST.get('TournamentName')
        description = request.POST.get('description')
        type = request.POST.get('type')
        date_debut = request.POST.get('dateDebut')
        num_terrains = int(request.POST.get("numTerrains", 0))

        terrains = []  # Liste pour stocker les détails des terrains

        for i in range(1, num_terrains + 1):
            number = request.POST.get(f"terrainNumber{i}")
            direction = request.POST.get(f"terrainDirections{i}")
            if number and direction:
                terrains.append({"number": number, "direction": direction})

        tour = Tournoi.objects.create(nom=nom, periode_debut=date_debut, description=description, type=Type.objects.get(type=type))
        tour.save()

        Use = request.user
        utili = Utilisateur.objects.get(user=Use)
        utili.tournoi.add(tour)

        #Pour gérer les terrains
        for i in range(len(terrains)):
            idterrain = terrains[i]['number']
            description = terrains[i]['direction']
            if not Terrain.objects.filter(numero_terrain=idterrain).exists():
                temp = Terrain.objects.create(numero_terrain=idterrain, commentaire=description)
                temp.save()
                tour.terrains.add(temp)
            else:
                if Terrain.objects.get(numero_terrain=idterrain).commentaire == description:
                    tour.terrains.add(Terrain.objects.get(numero_terrain=idterrain))
                else:
                    temp = Terrain.objects.get(numero_terrain=idterrain)
                    temp.commentaire = description
                    temp.save()
                    tour.terrains.add(temp)

        messages.success(request, f"Création du tournoi {nom} réussie !")
        return redirect("liste_tournois", tri="default")
    return render(request,"gui/creation_tournoi.html", context={"current_sport" : current_sport,"current_tab" : "administration", "is_admin" : is_admin})

from django.template.loader import render_to_string
def inscription(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        sex = request.POST.get('sex')
        sport = request.POST.get('sport')
        niveau = request.POST.get('niveau')

        #Vérifier si l'email est déja dans la BD
        if User.objects.filter(email=email).exists():
            messages.error(request,"Cet email est déja pris. Veuillez vous connecter ou créer un compte avec une nouvelle adresse email.")
            return redirect('inscription')
        #if User.objects.filter(role=role).exists():

        # Vérifier si les mots de passe correspondent
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('inscription')

        # Vérifier la validité du mot de passe
        if not (8 <= len(password1) <= 20 and any(c.isdigit() for c in password1) and any(c.isalpha() for c in password1)):
            messages.error(request, "Le mot de passe doit contenir 8-20 caractères, des lettres et des chiffres.")
            return redirect('inscription')

        #Vérifier si l'username est déja pris ou pas
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")
            return redirect('inscription')  # Réafficher le formulaire avec l'erreur

        user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name, password=password1)
        user.groups.add(Group.objects.get(name="Joueurs"))
        user.save()
        if sex == "Homme":
            sex = Sexe.objects.get(sexe="Homme")
        elif sex == "Femme":
            sex = Sexe.objects.get(sexe="Femme")
        if sport == "Tennis":
            sport = Sports.objects.get(sport_type="Tennis")
        elif sport == "Badminton":
            sport = Sports.objects.get(sport_type="Badminton")
        if niveau=="1":
            niveau = Classement.objects.get(niveau="1")
        if niveau=="2":
            niveau = Classement.objects.get(niveau="2")
        if niveau=="3":
            niveau = Classement.objects.get(niveau="3")
        if niveau=="4":
            niveau = Classement.objects.get(niveau="4")
        if niveau=="5":
            niveau = Classement.objects.get(niveau="5")
        if niveau=="6":
            niveau = Classement.objects.get(niveau="6")
        if niveau=="7":
            niveau = Classement.objects.get(niveau="7")
        if niveau=="8":
            niveau = Classement.objects.get(niveau="8")
        if niveau=="9":
            niveau = Classement.objects.get(niveau="9")
        if niveau=="10":
            niveau = Classement.objects.get(niveau="10")
        profile = Utilisateur(user=user, sexe=sex, sport_type=sport, niveau=niveau)
        profile.save()
        login(request, user)

        new_user = authenticate(username=email, password=password1)
        login(request, new_user)

        html_message = render_to_string('gui/email_inscription.html', {
            'user': user,  # Passer l'utilisateur pour le personnaliser dans le template
            'site_url': 'https://www.raqtour.com',  # L'URL de ton site
        })
        send_mail(
            "Inscription au site RAQTOUR réussie !",  # Sujet
            "Ceci est un message automatique.",
            # Message texte brut (en cas de problème avec HTML)
            'service.raqtour@gmail.com',  # Ton adresse e-mail
            [email],  # Adresse de l'utilisateur
            html_message=html_message,  # Corps HTML de l'email
            fail_silently=False
        )
        return redirect("home")  # Rediriger vers la page d'accueil après l'inscription

    return render(request, 'gui/inscription.html', context={"current_sport" : current_sport,"current_tab":"connexion", "is_admin" : is_admin})


def connexion(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    if request.method == 'POST':
        username = request.POST.get('utilisateur_username')
        password1 = request.POST.get('utilisateur_mdp')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "Aucun utilisateur trouvé avec cet email")
            return render(request, "gui/connexion.html", {"current_sport" : current_sport,"current_tab" : "connexion", "is_admin" : is_admin})

        new_user = authenticate(username=username, password=password1)

        if new_user is not None:
            login(request, new_user)
            messages.success(request, f"Vous êtes connecté sous le nom de {username} ")

            return redirect("home")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, "gui/connexion.html", {"current_sport" : current_sport,"current_tab": "connexion", "is_admin" : is_admin})


from django.shortcuts import render
from calendar import month_name, monthrange
import calendar

def calendrier(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()

    current_month = datetime.now().month

    utilisateurs = Utilisateur.objects.all()

    try:
        month = int(request.GET.get('month', current_month))
        year = int(request.GET.get('year', 2024))
        tri = str(request.GET.get('tri', "all"))
    except ValueError:

        month = current_month
        year = 2024
        tri = "all"

    if month < 1:
        month = 1
    elif month > 12:
        month = 12

    month_name = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre",
                  "Novembre", "Décembre"]

    month_name_display = month_name[month]

    _, num_days = monthrange(year, month)



    current_year = datetime.now().year
    years = list(range(current_year - 1, current_year + 3))

    first_day_weekday, num_days = monthrange(year, month)

    days = list(range(8-first_day_weekday, num_days + 1))

    empty_before = list(range(1,first_day_weekday+1))
    empty_after = list(range(1,8-first_day_weekday))

    months_list = [month_name[i] for i in range(1, 13)]



    if request.user.is_authenticated:
        if tri == "perso":
            return render(request, 'gui/calendrier.html', {
                'is_admin' : is_admin,
                'current_tab' : 'calendrier',
                'month_name': month_name_display,
                'year': year,
                'months_list': months_list,
                'month': month,
                'days': days,
                'empty_before': empty_before,
                'empty_after': empty_after,
                'years':years,
                'current_month' : current_month,
                'liste_matchs' : utilisateurs.get(user=request.user).match.all(),
                "current_sport" : current_sport
            })
        elif tri == "Tennis":
            tournois = Tournoi.objects.all()
            liste_tournois = []
            liste_matchs = []
            for tournoi in tournois:
                if utilisateurs.filter(tournoi=tournoi)[0].sport_type.sport_type == "Tennis":
                    liste_tournois.append(tournoi)
            for match in MatchDeTournoi.objects.all():
                for tournoi in liste_tournois:
                    if match.tournoi.idtournoi == tournoi.idtournoi:
                        liste_matchs.append(match)
            return render(request, 'gui/calendrier.html', {
                'is_admin': is_admin,
                'current_tab': 'calendrier',
                'month_name': month_name_display,
                'year': year,
                'months_list': months_list,
                'month': month,
                'days': days,
                'empty_before': empty_before,
                'empty_after': empty_after,
                'years': years,
                'liste_matchs': liste_matchs,
                "current_sport" : current_sport
            })
        elif tri == "Badminton":
            tournois = Tournoi.objects.all()
            liste_tournois = []
            liste_matchs = []
            for tournoi in tournois:
                if utilisateurs.filter(tournoi=tournoi)[0].sport_type.sport_type == "Badminton":
                    liste_tournois.append(tournoi)
            for match in MatchDeTournoi.objects.all():
                for tournoi in liste_tournois:
                    if match.tournoi.idtournoi == tournoi.idtournoi:
                        liste_matchs.append(match)
            return render(request, 'gui/calendrier.html', {
                    'is_admin': is_admin,
                    'current_tab': 'calendrier',
                    'month_name': month_name_display,
                    'year': year,
                    'months_list': months_list,
                    'month': month,
                    'days': days,
                    'empty_before': empty_before,
                    'empty_after': empty_after,
                    'years': years,
                    'liste_matchs': liste_matchs,
                    "current_sport" : current_sport
                })
        elif tri == "all":
            return render(request, 'gui/calendrier.html', {
                'is_admin': is_admin,
                'current_tab': 'calendrier',
                'month_name': month_name_display,
                'year': year,
                'months_list': months_list,
                'month': month,
                'days': days,
                'empty_before': empty_before,
                'empty_after': empty_after,
                'years': years,
                'liste_matchs': MatchDeTournoi.objects.all(),
                "current_sport" : current_sport
            })
        else:
            return render(request, 'gui/calendrier.html', {
                'is_admin': is_admin,
                'current_tab': 'calendrier',
                'month_name': month_name_display,
                'year': year,
                'months_list': months_list,
                'month': month,
                'days': days,
                'empty_before': empty_before,
                'empty_after': empty_after,
                'years': years,
                'current_month': current_month,
                'liste_matchs': utilisateurs.get(user=request.user).match.all(),
                "current_sport": current_sport
            })
    else:
        if tri == "Tennis":
            tournois = Tournoi.objects.all()
            liste_tournois = []
            liste_matchs = []
            for tournoi in tournois:
                if utilisateurs.filter(tournoi=tournoi)[0].sport_type.sport_type == "Tennis":
                    liste_tournois.append(tournoi)
            for match in MatchDeTournoi.objects.all():
                for tournoi in liste_tournois:
                    if match.tournoi.idtournoi == tournoi.idtournoi:
                        liste_matchs.append(match)
            return render(request, 'gui/calendrier.html', {
                'is_admin': is_admin,
                'current_tab': 'calendrier',
                'month_name': month_name_display,
                'year': year,
                'months_list': months_list,
                'month': month,
                'days': days,
                'empty_before': empty_before,
                'empty_after': empty_after,
                'years': years,
                'liste_matchs': liste_matchs,
                "current_sport" : current_sport
            })
        elif tri == "Badminton":
            tournois = Tournoi.objects.all()
            liste_tournois = []
            liste_matchs = []
            for tournoi in tournois:
                if utilisateurs.filter(tournoi=tournoi)[0].sport_type.sport_type == "Badminton":
                    liste_tournois.append(tournoi)
            for match in MatchDeTournoi.objects.all():
                for tournoi in liste_tournois:
                    if match.tournoi.idtournoi == tournoi.idtournoi:
                        liste_matchs.append(match)
            return render(request, 'gui/calendrier.html', {
                'is_admin': is_admin,
                'current_tab': 'calendrier',
                'month_name': month_name_display,
                'year': year,
                'months_list': months_list,
                'month': month,
                'days': days,
                'empty_before': empty_before,
                'empty_after': empty_after,
                'years': years,
                'liste_matchs': liste_matchs,
                "current_sport" : current_sport
            })
        elif tri == "all":
            return render(request, 'gui/calendrier.html', {
                'is_admin': is_admin,
                'current_tab': 'calendrier',
                'month_name': month_name_display,
                'year': year,
                'months_list': months_list,
                'month': month,
                'days': days,
                'empty_before': empty_before,
                'empty_after': empty_after,
                'years': years,
                'liste_matchs': MatchDeTournoi.objects.all(),
                "current_sport" : current_sport
            })
        else:
            return render(request, 'gui/calendrier.html', {
                'is_admin': is_admin,
                'current_tab': 'calendrier',
                'month_name': month_name_display,
                'year': year,
                'months_list': months_list,
                'month': month,
                'days': days,
                'empty_before': empty_before,
                'empty_after': empty_after,
                'years': years,
                'liste_matchs': MatchDeTournoi.objects.all(),
                "current_sport": current_sport
            })

def utilisateur_details(request, username):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None

    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    #username = request.GET.get('username')
    if username == "default":
        use = request.user
    else:
        use = User.objects.get(username=username)

    #User.objects.get(username=username)
    utili = Utilisateur.objects.get(user=use)

    matchAVenir = []
    matchFait = []
    for match in utili.match.all():
        if str(match.score) == "a" :
            if match.tournoi.type.type[:6] == "Simple":
                joueur1 = utili
                joueur2 = Utilisateur.objects.filter(match=match).exclude(user=use).first()
                matchAVenir.append({"match" : match, "joueur1" : joueur1, "joueur2" : joueur2, "type" : match.tournoi.type.type[:6]})
            elif match.tournoi.type.type[:6] == "Double":
                equipe1 = utili.equipe.get(tournoi=match.tournoi)
                equipe2 = Equipe.objects.filter(tournoi=match.tournoi).exclude(nom_equipe=equipe1.nom_equipe).first()
                joueur11 = utili
                joueur12 = Utilisateur.objects.filter(match=match, equipe=equipe1).exclude(user=use).first()
                joueur21 = Utilisateur.objects.filter(match=match, equipe=equipe2).first()
                joueur22 = Utilisateur.objects.filter(match=match, equipe=equipe2)[1]
                matchAVenir.append({"match" : match,
                                  "equipe1" : equipe1,
                                  "equipe2" : equipe2,
                                  "joueur11" : joueur11,
                                  "joueur12" : joueur12,
                                  "joueur21" : joueur21,
                                  "joueur22" : joueur22,
                                "type" : match.tournoi.type.type[:6]})
        else:
            score = str(match.score)
            index = score.find("-")
            gagnant = "Indéterminé"
            if match.tournoi.type.type[:6] == "Simple":
                joueur1 = utili
                joueur2 = Utilisateur.objects.filter(match=match).exclude(user=use).first()
                if int(score[:index]) > int(score[index+1:]):
                    gagnant = joueur1.user.username
                elif int(score[:index]) < int(score[index+1:]):
                    gagnant = joueur2.user.username
                elif int(score[:index]) == int(score[index + 1:]):
                    gagnant = "Égalité"
                matchFait.append({"match" : match, "joueur1" : joueur1, "joueur2" : joueur2, "gagnant" : gagnant,"type" : match.tournoi.type.type[:6]})
            elif match.tournoi.type.type[:6] == "Double":
                equipe1 = utili.equipe.get(tournoi=match.tournoi)
                equipe2 = Equipe.objects.filter(tournoi=match.tournoi).exclude(nom_equipe=equipe1.nom_equipe).first()
                joueur11 = utili
                joueur12 = Utilisateur.objects.filter(match=match, equipe=equipe1).exclude(user=use).first()
                joueur21 = Utilisateur.objects.filter(match=match, equipe=equipe2).first()
                joueur22 = Utilisateur.objects.filter(match=match, equipe=equipe2)[1]
                if int(score[:index]) > int(score[index+1:]):
                    gagnant = equipe1.nom_equipe
                elif int(score[:index]) < int(score[index+1:]):
                    gagnant = equipe2.nom_equipe
                elif int(score[:index]) == int(score[index+1:]):
                    gagnant = "Égalité"
                matchFait.append({"match" : match,
                                  "equipe1" : equipe1,
                                  "equipe2" : equipe2,
                                  "joueur11" : joueur11,
                                  "joueur12" : joueur12,
                                  "joueur21" : joueur21,
                                  "joueur22" : joueur22,
                                "gagnant" : gagnant,
                                "type" : match.tournoi.type.type[:6]})
    contexte = {
        'username': use.username,
        'first_name': use.first_name,
        'last_name': use.last_name,
        'email': use.email,
        "sexe": utili.sexe.sexe,
        "sport_type": utili.sport_type.sport_type,
        "niveau": utili.niveau.niveau,
        "is_admin" : is_admin,
        "current_tab": "profil",
        "matchFait" : matchFait,
        "matchAVenir" : matchAVenir,
        "current_sport":current_sport
    }

    return render(request, 'gui/profil.html', contexte)

def liste_tournois(request, tri):
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    research = request.GET.get('research')

    if not research:
        tournois = Tournoi.objects.all()
        tournois_avec_sport = []
        for tournoi in tournois:
            gerants = Utilisateur.objects.filter(tournoi=Tournoi.objects.get(idtournoi=tournoi.idtournoi), user__groups__name="Administrateurs")
            sport_gerant = gerants.first().sport_type.sport_type
            gerant = gerants.first()
            date_debut = tournoi.periode_debut
            date_cloture = date_debut - timedelta(days=7)
            inscriptions_cloturees = date.today() > date_cloture
            if MatchDeTournoi.objects.filter(tournoi=tournoi).exists():
                match_fini = True
                for match in MatchDeTournoi.objects.filter(tournoi=tournoi):
                    if str(match.score) == "a":
                        match_fini = False
                        break
            else:
                match_fini = False

            if tri == "tennis":
                if sport_gerant == "Tennis":
                    tournois_avec_sport.append({
                        "tournoi": tournoi,
                        "sport_type": sport_gerant,
                        "gerant" : gerant,
                        "fin_inscription" : inscriptions_cloturees,
                        "match_fini" : match_fini
                    })
            elif tri == "badminton":
                if sport_gerant == "Badminton":
                    tournois_avec_sport.append({
                        "tournoi": tournoi,
                        "sport_type": sport_gerant,
                        "gerant": gerant,
                        "fin_inscription": inscriptions_cloturees,
                        "match_fini": match_fini
                    })
            else:
                tournois_avec_sport.append({
                    "tournoi": tournoi,
                    "sport_type": sport_gerant,
                    "gerant": gerant,
                    "fin_inscription": inscriptions_cloturees,
                    "match_fini": match_fini
                })

        return render(request,'gui/tournois.html', context={'tournois_avec_sport': tournois_avec_sport, "is_admin" : is_admin, "current_sport":current_sport,"current_tab" : "tournois"})
    else:
        tournois_avec_sport = []
        tournois = Tournoi.objects.all()
        tournois = tournois.filter(
            Q(nom__icontains=research)
        )
        for tournoi in tournois:
            gerants = Utilisateur.objects.filter(tournoi=Tournoi.objects.get(idtournoi=tournoi.idtournoi),user__groups__name="Administrateurs")
            sport_gerant = gerants.first().sport_type.sport_type
            gerant = gerants.first()
            date_debut = tournoi.periode_debut
            date_cloture = date_debut - timedelta(days=7)
            inscriptions_cloturees = date.today() > date_cloture
            if tri == "tennis":
                if sport_gerant == "Tennis":
                    tournois_avec_sport.append({
                        "tournoi": tournoi,
                        "sport_type": sport_gerant,
                        "gerants": gerants,
                        "fin_inscription" : inscriptions_cloturees
                    })
            elif tri == "badminton":
                if sport_gerant == "Badminton":
                    tournois_avec_sport.append({
                        "tournoi": tournoi,
                        "sport_type": sport_gerant,
                        "gerants": gerants,
                        "fin_inscription": inscriptions_cloturees
                    })
            else:
                tournois_avec_sport.append({
                    "tournoi": tournoi,
                    "sport_type": sport_gerant,
                    "gerants": gerants,
                    "fin_inscription": inscriptions_cloturees
                })
        return render(request, 'gui/tournois.html',
                      context={'tournois_avec_sport': tournois_avec_sport, "is_admin": is_admin,
                               "current_tab": "tournois",
                               "current_sport":current_sport})


def tournoi_details(request, idtournoi):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    today = date.today()
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    user_participate = False
    tournoi = Tournoi.objects.get(idtournoi=idtournoi)
    gerants = Utilisateur.objects.filter(tournoi=tournoi,
                                         user__groups__name="Administrateurs")
    if request.user.is_authenticated:
        if tournoi.periode_debut > today + timedelta(days=7):
            if is_admin:
                if tournoi.type.type[:6] == "Simple":
                    liste_inscrits = Utilisateur.objects.filter(tournoi=tournoi).exclude(user__groups__name="Administrateurs")
                elif tournoi.type.type[:6] == "Double":
                    liste_inscrits = Utilisateur.objects.filter(equipe__tournoi=tournoi)
                return render(request, 'gui/tournoi_details.html',
                              {"liste_inscrits" : liste_inscrits,'tournoi': tournoi, "is_admin": is_admin, "current_tab": "tournois", "gerants": gerants,
                               "user_participe": True,
                               "current_sport":current_sport})
            else:
                if tournoi.type.type[:6] == "Simple":
                    liste_inscrits = Utilisateur.objects.filter(tournoi=tournoi)
                    if Utilisateur.objects.filter(user=request.user, tournoi=tournoi).exists():
                        user_participate = True
                    return render(request, 'gui/tournoi_details.html',
                                  {"liste_inscrits" : liste_inscrits,'tournoi': tournoi, "is_admin": is_admin, "current_tab": "tournois",
                                   "gerants": gerants, "user_participe": user_participate,
                                   "current_sport":current_sport})
                elif tournoi.type.type[:6] == "Double":
                    liste_inscrits = Utilisateur.objects.filter(equipe__tournoi=tournoi)
                    for equipe in Utilisateur.objects.get(user=request.user).equipe.all():
                        equipe = equipe.nom_equipe
                        if Equipe.objects.get(nom_equipe=equipe).tournoi.filter(idtournoi=tournoi.idtournoi).exists():
                            user_participate = True
                    return render(request, 'gui/tournoi_details.html',
                                      {"liste_inscrits" : liste_inscrits,'tournoi': tournoi, "is_admin": is_admin, "current_tab": "tournois",
                                       "gerants": gerants, "user_participe": user_participate,
                                       "current_sport":current_sport})
        else:
            if tournoi.type.type[:6] == "Simple":
                if Utilisateur.objects.filter(tournoi=tournoi).count() < 3:
                    liste_inscrit = Utilisateur.objects.filter(tournoi=tournoi).exclude(user__groups__name="Administrateurs")
                    user = request.user
                    email = Utilisateur.objects.filter(tournoi=tournoi, user__groups__name="Administrateurs").first().user.email
                    html_content = render_to_string('gui/annulation_tournoi.html', {'user': user,"liste_inscrit" : liste_inscrit})
                    send_mail(
                        f'Annulation du tournoi : {tournoi.nom}',
                        f"Bonjour {user.username},\n\nLe tournoi {tournoi.nom} a été annulé car le nombre d'inscrit était insuffisant pour pouvoir créer le tournoi",
                        'service.raqtour@gmail.com',
                        [email],
                        fail_silently=False,
                        html_message=html_content
                    )
                    Tournoi.objects.get(idtournoi=idtournoi).delete()
                    return redirect("liste_tournois", tri="default")
                infos = []
                match_a_venir = []
                match_fait = []
                tournoi = Tournoi.objects.get(idtournoi=idtournoi)
                inscrit = Utilisateur.objects.filter(tournoi=tournoi)[1]
                liste_inscription = Utilisateur.objects.filter(tournoi=tournoi).exclude(user__groups__name="Administrateurs")
                n = tournoi.terrains.count()
                if not inscrit.match.filter(tournoi=tournoi).exists():
                    #Création des matchs
                    date_debut = tournoi.periode_debut
                    debut = time(17, 0)
                    fin = time(21, 0)
                    duree = timedelta(hours=1)
                    current_day = datetime.combine(date_debut, debut)
                    tournoi = get_object_or_404(Tournoi, idtournoi=idtournoi)
                    used = []

                    match_cree = []
                    match_a_cree = 0
                    for i in range(liste_inscription.count()-1, 0, -1):
                        match_a_cree += i

                    while len(match_cree) != match_a_cree:
                        duo = []
                        terrain = None

                        for joueur in liste_inscription:
                            conflit = False
                            if joueur.match.filter(tournoi=tournoi).count() == liste_inscription.count() - 1:
                                continue
                            for match in joueur.match.all():
                                if match.date_heure_match == make_aware(current_day):
                                    conflit = True
                            if not conflit:
                                duo.append(joueur)
                            if len(duo) == 2:
                                for match in MatchDeTournoi.objects.filter(tournoi=tournoi):
                                    joueur1 = Utilisateur.objects.filter(match=match)[0]
                                    joueur2 = Utilisateur.objects.filter(match=match)[1]
                                    if (duo[0] == joueur1 and duo[1] == joueur2) or (duo[0] == joueur2 and duo[1] == joueur1):
                                        duo.pop(-1)
                                        break
                            if len(duo) == 2:
                                n = tournoi.terrains.count()
                                terrains = tournoi.terrains.all()
                                while (n > 0):
                                    conflit_terrain = False
                                    if MatchDeTournoi.objects.filter(date_heure_match=current_day).exclude(tournoi=tournoi).exists():
                                        for match_conflit in MatchDeTournoi.objects.filter(date_heure_match=current_day).exclude(tournoi=tournoi):
                                            n_conflit = match_conflit.tournoi.terrains.count()
                                            for match in MatchDeTournoi.objects.filter(tournoi=match_conflit.tournoi):
                                                if match.date_heure_match == make_aware(current_day):
                                                    if terrains[n-1] == match_conflit.tournoi.terrains.all()[n_conflit - 1]:
                                                        conflit_terrain = True
                                                        print("conflit_terrain")
                                                n_conflit -= 1
                                                if n_conflit <= 0:
                                                    n_conflit = match_conflit.tournoi.terrains.count()
                                    if not conflit_terrain:
                                        terrain = terrains[n-1]
                                    if terrain is not None:
                                        break
                                    n -= 1
                                if terrain is not None:
                                    temp = MatchDeTournoi.objects.create(date_heure_match=current_day, tournoi=tournoi, points=10)
                                    temp.save()

                                    duo[0].match.add(temp)
                                    duo[1].match.add(temp)
                                    match_cree.append(temp)
                                    break

                        current_day += duree
                        heure = current_day.hour
                        minutes = current_day.minute
                        reconstructed_time = time(heure, minutes)
                        if reconstructed_time >= fin:
                            current_day += timedelta(hours=20)

                    tournoi.periode_fin = current_day.date()
                    tournoi.save()

                n = tournoi.terrains.count()
                for match in MatchDeTournoi.objects.filter(tournoi=tournoi):
                    joueur1 = Utilisateur.objects.filter(match=match)[0]
                    joueur2 = Utilisateur.objects.filter(match=match)[1]
                    if n == 0:
                        n = tournoi.terrains.count()
                    if str(match.score) == "a":
                        joueur1Exist = False
                        joueur2Exist = False
                        for info in infos:
                            if info["inscrit"] == joueur1:
                                joueur1Exist = True
                            if info["inscrit"] == joueur2:
                                joueur2Exist = True
                        if joueur1Exist == False:
                            infos.append({"inscrit": joueur1, "total": 0})
                        if joueur2Exist == False:
                            infos.append({"inscrit": joueur2, "total": 0})
                        match_a_venir.append(
                            {"match": match, "joueur1": Utilisateur.objects.filter(match=match)[0],
                             "joueur2": Utilisateur.objects.filter(match=match)[1],
                             "terrain": tournoi.terrains.all()[n-1]})
                        n -= 1
                    else:
                        txt = str(match.score)
                        index = txt.find("-")

                        if str(match.score)[:index] != str(match.score)[index+1:]:
                            if int(str(match.score)[:index]) > int(str(match.score)[index+1:]):
                                gagnant = Utilisateur.objects.filter(match=match)[0].user.username
                            elif int(str(match.score)[:index]) < int(str(match.score)[index+1:]):
                                gagnant = Utilisateur.objects.filter(match=match)[1].user.username
                            exist = False
                            for info in infos:
                                if info["inscrit"] == Utilisateur.objects.get(user__username=str(gagnant)):
                                    info["total"] += match.points
                                    exist = True
                                    break
                            if exist == False:
                                infos.append({"inscrit": Utilisateur.objects.get(user__username=str(gagnant)), "total": match.points})
                            match_fait.append(
                                {"match": match, "joueur1": Utilisateur.objects.filter(match=match)[0],
                                 "joueur2": Utilisateur.objects.filter(match=match)[1],
                                 "terrain": tournoi.terrains.all()[n-1],
                                 "gagnant": gagnant})
                            n -= 1
                        elif str(match.score)[:index] == str(match.score)[index+1:]:
                            joueur1Exist = False
                            joueur2Exist = False
                            for info in infos:
                                if info["inscrit"] == joueur1:
                                    info["total"] += int(match.points/2)
                                    joueur1Exist = True
                                if info["inscrit"] == joueur2:
                                    info["total"] += int(match.points/2)
                                    joueur2Exist = True
                            if joueur1Exist == False:
                                infos.append({"inscrit": joueur1, "total": int(match.points/2)})
                            if joueur2Exist == False:
                                infos.append({"inscrit": joueur2, "total": int(match.points/2)})
                            match_fait.append(
                                {"match": match, "joueur1": Utilisateur.objects.filter(match=match)[0],
                                 "joueur2": Utilisateur.objects.filter(match=match)[1],
                                 "terrain": tournoi.terrains.all()[n - 1],
                                 "gagnant": "Égalité"})
                            n -= 1

                for utili in Utilisateur.objects.filter(tournoi=tournoi).exclude(user__groups__name="Administrateurs"):
                    exist = False
                    for info in infos:
                        if info["inscrit"] == utili:
                            exist = True
                    if exist == False:
                        infos.append({"inscrit": utili, "total": 0})
                infos_sorted_decroissant = sorted(infos, key=lambda x: x["total"], reverse=True)

                liste_terrains = tournoi.terrains.all()

                return render(request, 'gui/current_tournoi.html',
                              {"is_admin": is_admin, "current_tab": "tournois", "infos": infos_sorted_decroissant,
                               "current_user": request.user, "matchAVenir": match_a_venir,
                               "match_fait": match_fait,
                               "current_sport":current_sport,
                               "liste_terrains" : liste_terrains})
            elif tournoi.type.type[:6] == "Double":
                infos = []
                match_a_venir = []
                match_fait = []
                tournoi = Tournoi.objects.get(idtournoi=idtournoi)
                inscrit = Utilisateur.objects.filter(equipe__tournoi=tournoi)[1]
                liste_inscription = Equipe.objects.filter(tournoi=tournoi)
                n = tournoi.terrains.count()
                if not inscrit.match.filter(tournoi=tournoi).exists():
                    # Création des matchs
                    date_debut = tournoi.periode_debut
                    debut = time(17, 0)
                    fin = time(21, 0)
                    duree = timedelta(hours=1)
                    current_day = datetime.combine(date_debut, debut)
                    tournoi = get_object_or_404(Tournoi, idtournoi=idtournoi)
                    used = []

                    match_cree = []
                    match_a_cree = 0
                    for i in range(liste_inscription.count() - 1, 0, -1):
                        match_a_cree += i

                    while len(match_cree) != match_a_cree:
                        duo = []
                        terrain = None

                        for equipe in liste_inscription:
                            joueur1 = Utilisateur.objects.filter(equipe=equipe)[0]
                            joueur2 = Utilisateur.objects.filter(equipe=equipe)[1]
                            conflit = False
                            if joueur1.match.filter(tournoi=tournoi).count() == liste_inscription.count() - 1 and joueur2.match.filter(tournoi=tournoi).count() == liste_inscription.count() - 1:
                                continue
                            for match in joueur1.match.all():
                                if match.date_heure_match == make_aware(current_day):
                                    conflit = True
                            for match in joueur2.match.all():
                                if match.date_heure_match == make_aware(current_day):
                                    conflit = True

                            if not conflit:
                                duo.append(equipe)
                            if len(duo) == 2:
                                for match in MatchDeTournoi.objects.filter(tournoi=tournoi):
                                    equipe1 = Utilisateur.objects.filter(match=match)[0].equipe.get(tournoi=tournoi)
                                    equipe2 = Utilisateur.objects.filter(match=match)[2].equipe.get(tournoi=tournoi)
                                    if (duo[0] == equipe1 and duo[1] == equipe2) or (
                                            duo[0] == equipe2 and duo[1] == equipe1):
                                        duo.pop(-1)
                                        break
                            if len(duo) == 2:
                                n = tournoi.terrains.count()
                                terrains = tournoi.terrains.all()
                                while (n > 0):
                                    conflit_terrain = False
                                    if MatchDeTournoi.objects.filter(date_heure_match=current_day).exclude(
                                            tournoi=tournoi).exists():
                                        for match_conflit in MatchDeTournoi.objects.filter(
                                                date_heure_match=current_day).exclude(tournoi=tournoi):
                                            n_conflit = match_conflit.tournoi.terrains.count()
                                            for match in MatchDeTournoi.objects.filter(tournoi=match_conflit.tournoi):
                                                if match.date_heure_match == make_aware(current_day):
                                                    if terrains[n - 1] == match_conflit.tournoi.terrains.all()[
                                                        n_conflit - 1]:
                                                        conflit_terrain = True
                                                        print("conflit_terrain")
                                                n_conflit -= 1
                                                if n_conflit <= 0:
                                                    n_conflit = match_conflit.tournoi.terrains.count()
                                    if not conflit_terrain:
                                        terrain = terrains[n - 1]
                                    if terrain is not None:
                                        break
                                    n -= 1
                                if terrain is not None:
                                    temp = MatchDeTournoi.objects.create(date_heure_match=current_day, tournoi=tournoi,
                                                                         points=10)
                                    temp.save()

                                    Utilisateur.objects.filter(equipe=duo[0])[0].match.add(temp)
                                    Utilisateur.objects.filter(equipe=duo[0])[1].match.add(temp)
                                    Utilisateur.objects.filter(equipe=duo[1])[0].match.add(temp)
                                    Utilisateur.objects.filter(equipe=duo[1])[1].match.add(temp)

                                    match_cree.append(temp)
                                    break

                        current_day += duree
                        heure = current_day.hour
                        minutes = current_day.minute
                        reconstructed_time = time(heure, minutes)
                        if reconstructed_time >= fin:
                            current_day += timedelta(hours=20)

                    tournoi.periode_fin = current_day.date()
                    tournoi.save()

                n = tournoi.terrains.count()
                for match in MatchDeTournoi.objects.filter(tournoi=tournoi):
                    if n == 0:
                        n = Tournoi.objects.get(idtournoi=idtournoi).terrains.count()
                    if str(match.score) == "a":
                        joueurs = Utilisateur.objects.filter(match=match)
                        equipes = []
                        for joueur in joueurs:
                            if not joueur.equipe.get(tournoi=tournoi) in equipes:
                                equipes.append(joueur.equipe.get(tournoi=tournoi))
                        exist1 = False
                        exist2 = False
                        for info in infos:
                            if info["equipe"] == equipes[0]:
                                exist1 = True
                            if info["equipe"] == equipes[1]:
                                exist2 = True
                        if exist1 == False:
                            infos.append({"total": 0, "joueur1" : Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                          "joueur2" : Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                          "equipe": equipes[0]})
                        if exist2 == False:
                            infos.append(
                                {"total": 0, "joueur1": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                 "joueur2": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                 "equipe": equipes[1]})
                        match_a_venir.append(
                                {"match": match,
                                 "equipe1": equipes[0],
                                 "equipe2": equipes[1],
                                 "joueur11": Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                 "joueur12": Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                 "joueur21": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                 "joueur22": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                 "terrain" : Tournoi.objects.get(idtournoi=idtournoi).terrains.all()[n-1]})
                        n -= 1
                    else:
                        txt = str(match.score)
                        index = txt.find("-")

                        if str(match.score)[:index] != str(match.score)[index + 1:]:
                            joueurs = Utilisateur.objects.filter(match=match)
                            equipes = []
                            for joueur in joueurs:
                                if not joueur.equipe.get(tournoi=tournoi) in equipes:
                                    equipes.append(joueur.equipe.get(tournoi=tournoi))
                            if int(str(match.score)[:index]) > int(str(match.score)[index + 1:]):
                                gagnant = equipes[0].nom_equipe
                                exist = False
                                for info in infos:
                                    if info["equipe"] == equipes[0]:
                                        info["total"] += match.points
                                        exist = True
                                if exist == False:
                                    infos.append({"total": match.points,
                                                  "joueur1" : Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                                  "joueur2" : Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                                  "equipe": equipes[0]})
                            elif int(str(match.score)[:index]) < int(str(match.score)[index + 1:]):
                                gagnant = equipes[1].nom_equipe
                                exist = False
                                for info in infos:
                                    if info["equipe"] == equipes[1]:
                                        info["total"] += match.points
                                        exist = True
                                if exist == False:
                                    infos.append({"total": match.points,
                                                  "joueur1": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                                  "joueur2": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                                  "equipe": equipes[1]})
                            match_fait.append(
                                {"match": match,
                                 "equipe1": equipes[0],
                                 "equipe2": equipes[1],
                                 "joueur11": Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                 "joueur12": Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                 "joueur21": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                 "joueur22": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                 "terrain": Tournoi.objects.get(idtournoi=idtournoi).terrains.all()[n - 1],
                                 "gagnant" : gagnant})
                            n -= 1
                        elif str(match.score)[:index] == str(match.score)[index + 1:]:
                            joueurs = Utilisateur.objects.filter(match=match)
                            equipes = []
                            for joueur in joueurs:
                                if not joueur.equipe.get(tournoi=tournoi) in equipes:
                                    equipes.append(joueur.equipe.get(tournoi=tournoi))
                            exist1 = False
                            exist2 = False
                            for info in infos:
                                if info["equipe"] == equipes[0]:
                                    info["total"] += int(match.points/2)
                                    exist1 = True
                                if info["equipe"] == equipes[1]:
                                    info["total"] += int(match.points / 2)
                                    exist2 = True
                            if exist1 == False:
                                infos.append({"total": int((match.points)/2),
                                              "joueur1" : Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                              "joueur2" : Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                              "equipe" : equipes[0]})
                            if exist2 == False:
                                infos.append({"total": int((match.points)/2),
                                              "joueur1" : Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                              "joueur2" : Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                              "equipe" : equipes[1]})
                            match_fait.append(
                                {"match": match,
                                 "equipe1": equipes[0],
                                 "equipe2": equipes[1],
                                 "joueur11": Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                 "joueur12": Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                 "joueur21": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                 "joueur22": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                 "terrain": Tournoi.objects.get(idtournoi=idtournoi).terrains.all()[n - 1],
                                 "gagnant": "Égalité"})
                            n -= 1
                for equipe in Equipe.objects.filter(tournoi=tournoi):
                    exist = False
                    for info in infos:
                        if info["equipe"] == equipe:
                            exist = True
                    if exist == False:
                        infos.append({"total": 0,
                                      "joueur1" : Utilisateur.objects.filter(match=match, equipe=equipe)[0],
                                      "joueur2" : Utilisateur.objects.filter(match=match, equipe=equipe)[1],
                                      "equipe" : equipe})
                infos_sorted_decroissant = sorted(infos, key=lambda x: x["total"], reverse=True)

                liste_terrains = tournoi.terrains.all()

                return render(request, 'gui/current_tournoi_equipe.html',
                              {"is_admin": is_admin, "current_tab": "tournois", "current_user": request.user,
                               "infos": infos_sorted_decroissant, "matchAVenir": match_a_venir, "match_fait": match_fait,
                               "current_sport":current_sport,
                               "liste_terrains" : liste_terrains})
    else:
        if MatchDeTournoi.objects.filter(tournoi=tournoi).exists():
            if tournoi.type.type[:6] == "Simple":
                infos = []
                match_a_venir = []
                match_fait = []
                tournoi = Tournoi.objects.get(idtournoi=idtournoi)
                inscrit = Utilisateur.objects.filter(tournoi=tournoi)[1]
                liste_inscription = Utilisateur.objects.filter(tournoi=tournoi)
                n = tournoi.terrains.count()
                for match in MatchDeTournoi.objects.filter(tournoi=tournoi):
                    joueur1 = Utilisateur.objects.filter(match=match)[0]
                    joueur2 = Utilisateur.objects.filter(match=match)[1]
                    if n == 0:
                        n = tournoi.terrains.count()
                    if str(match.score) == "a":
                        joueur1Exist = False
                        joueur2Exist = False
                        for info in infos:
                            if info["inscrit"] == joueur1:
                                joueur1Exist = True
                            if info["inscrit"] == joueur2:
                                joueur2Exist = True
                        if joueur1Exist == False:
                            infos.append({"inscrit": joueur1, "total": 0})
                        if joueur2Exist == False:
                            infos.append({"inscrit": joueur2, "total": 0})
                        match_a_venir.append(
                            {"match": match, "joueur1": Utilisateur.objects.filter(match=match)[0],
                             "joueur2": Utilisateur.objects.filter(match=match)[1],
                             "terrain": tournoi.terrains.all()[n - 1]})
                        n -= 1
                    else:
                        txt = str(match.score)
                        index = txt.find("-")

                        if str(match.score)[:index] != str(match.score)[index + 1:]:
                            if int(str(match.score)[:index]) > int(str(match.score)[index + 1:]):
                                gagnant = Utilisateur.objects.filter(match=match)[0].user.username
                            elif int(str(match.score)[:index]) < int(str(match.score)[index + 1:]):
                                gagnant = Utilisateur.objects.filter(match=match)[1].user.username
                            exist = False
                            for info in infos:
                                if info["inscrit"] == Utilisateur.objects.get(user__username=str(gagnant)):
                                    info["total"] += match.points
                                    exist = True
                                    break
                            if exist == False:
                                infos.append({"inscrit": Utilisateur.objects.get(user__username=str(gagnant)),
                                              "total": match.points})
                            match_fait.append(
                                {"match": match, "joueur1": Utilisateur.objects.filter(match=match)[0],
                                 "joueur2": Utilisateur.objects.filter(match=match)[1],
                                 "terrain": tournoi.terrains.all()[n - 1],
                                 "gagnant": gagnant})
                            n -= 1
                        elif str(match.score)[:index] == str(match.score)[index + 1:]:
                            joueur1Exist = False
                            joueur2Exist = False
                            for info in infos:
                                if info["inscrit"] == joueur1:
                                    info["total"] += int(match.points / 2)
                                    joueur1Exist = True
                                if info["inscrit"] == joueur2:
                                    info["total"] += int(match.points / 2)
                                    joueur2Exist = True
                            if joueur1Exist == False:
                                infos.append({"inscrit": joueur1, "total": int(match.points / 2)})
                            if joueur2Exist == False:
                                infos.append({"inscrit": joueur2, "total": int(match.points / 2)})
                            match_fait.append(
                                {"match": match, "joueur1": Utilisateur.objects.filter(match=match)[0],
                                 "joueur2": Utilisateur.objects.filter(match=match)[1],
                                 "terrain": tournoi.terrains.all()[n - 1],
                                 "gagnant": "Égalité"})
                            n -= 1

                for utili in Utilisateur.objects.filter(tournoi=tournoi).exclude(user__groups__name="Administrateurs"):
                    exist = False
                    for info in infos:
                        if info["inscrit"] == utili:
                            exist = True
                    if exist == False:
                        infos.append({"inscrit": utili, "total": 0})
                infos_sorted_decroissant = sorted(infos, key=lambda x: x["total"], reverse=True)
                return render(request, 'gui/current_tournoi.html',
                              {"is_admin": is_admin, "current_tab": "tournois", "infos": infos_sorted_decroissant,
                               "current_user": request.user, "matchAVenir": match_a_venir,
                               "match_fait": match_fait,
                               "current_sport": current_sport})
            elif tournoi.type.type[:6] == "Double":
                infos = []
                match_a_venir = []
                match_fait = []
                tournoi = Tournoi.objects.get(idtournoi=idtournoi)
                inscrit = Utilisateur.objects.filter(equipe__tournoi=tournoi)[1]
                liste_inscription = Equipe.objects.filter(tournoi=tournoi)
                n = tournoi.terrains.count()
                for match in MatchDeTournoi.objects.filter(tournoi=tournoi):
                    if n == 0:
                        n = Tournoi.objects.get(idtournoi=idtournoi).terrains.count()
                    if str(match.score) == "a":
                        joueurs = Utilisateur.objects.filter(match=match)
                        equipes = []
                        for joueur in joueurs:
                            if not joueur.equipe.get(tournoi=tournoi) in equipes:
                                equipes.append(joueur.equipe.get(tournoi=tournoi))
                        exist1 = False
                        exist2 = False
                        for info in infos:
                            if info["equipe"] == equipes[0]:
                                exist1 = True
                            if info["equipe"] == equipes[1]:
                                exist2 = True
                        if exist1 == False:
                            infos.append(
                                {"total": 0, "joueur1": Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                 "joueur2": Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                 "equipe": equipes[0]})
                        if exist2 == False:
                            infos.append(
                                {"total": 0, "joueur1": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                 "joueur2": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                 "equipe": equipes[1]})
                        match_a_venir.append(
                            {"match": match,
                             "equipe1": equipes[0],
                             "equipe2": equipes[1],
                             "joueur11": Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                             "joueur12": Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                             "joueur21": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                             "joueur22": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                             "terrain": Tournoi.objects.get(idtournoi=idtournoi).terrains.all()[n - 1]})
                        n -= 1
                    else:
                        txt = str(match.score)
                        index = txt.find("-")

                        if str(match.score)[:index] != str(match.score)[index + 1:]:
                            joueurs = Utilisateur.objects.filter(match=match)
                            equipes = []
                            for joueur in joueurs:
                                if not joueur.equipe.get(tournoi=tournoi) in equipes:
                                    equipes.append(joueur.equipe.get(tournoi=tournoi))
                            if int(str(match.score)[:index]) > int(str(match.score)[index + 1:]):
                                gagnant = equipes[0].nom_equipe
                                exist = False
                                for info in infos:
                                    if info["equipe"] == equipes[0]:
                                        info["total"] += match.points
                                        exist = True
                                if exist == False:
                                    infos.append({"total": match.points,
                                                  "joueur1": Utilisateur.objects.filter(match=match, equipe=equipes[0])[
                                                      0],
                                                  "joueur2": Utilisateur.objects.filter(match=match, equipe=equipes[0])[
                                                      1],
                                                  "equipe": equipes[0]})
                            elif int(str(match.score)[:index]) < int(str(match.score)[index + 1:]):
                                gagnant = equipes[1].nom_equipe
                                exist = False
                                for info in infos:
                                    if info["equipe"] == equipes[1]:
                                        info["total"] += match.points
                                        exist = True
                                if exist == False:
                                    infos.append({"total": match.points,
                                                  "joueur1": Utilisateur.objects.filter(match=match, equipe=equipes[1])[
                                                      0],
                                                  "joueur2": Utilisateur.objects.filter(match=match, equipe=equipes[1])[
                                                      1],
                                                  "equipe": equipes[1]})
                            match_fait.append(
                                {"match": match,
                                 "equipe1": equipes[0],
                                 "equipe2": equipes[1],
                                 "joueur11": Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                 "joueur12": Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                 "joueur21": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                 "joueur22": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                 "terrain": Tournoi.objects.get(idtournoi=idtournoi).terrains.all()[n - 1],
                                 "gagnant": gagnant})
                            n -= 1
                        elif str(match.score)[:index] == str(match.score)[index + 1:]:
                            joueurs = Utilisateur.objects.filter(match=match)
                            equipes = []
                            for joueur in joueurs:
                                if not joueur.equipe.get(tournoi=tournoi) in equipes:
                                    equipes.append(joueur.equipe.get(tournoi=tournoi))
                            exist1 = False
                            exist2 = False
                            for info in infos:
                                if info["equipe"] == equipes[0]:
                                    info["total"] += int(match.points / 2)
                                    exist1 = True
                                if info["equipe"] == equipes[1]:
                                    info["total"] += int(match.points / 2)
                                    exist2 = True
                            if exist1 == False:
                                infos.append({"total": int((match.points) / 2),
                                              "joueur1": Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                              "joueur2": Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                              "equipe": equipes[0]})
                            if exist2 == False:
                                infos.append({"total": int((match.points) / 2),
                                              "joueur1": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                              "joueur2": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                              "equipe": equipes[1]})
                            match_fait.append(
                                {"match": match,
                                 "equipe1": equipes[0],
                                 "equipe2": equipes[1],
                                 "joueur11": Utilisateur.objects.filter(match=match, equipe=equipes[0])[0],
                                 "joueur12": Utilisateur.objects.filter(match=match, equipe=equipes[0])[1],
                                 "joueur21": Utilisateur.objects.filter(match=match, equipe=equipes[1])[0],
                                 "joueur22": Utilisateur.objects.filter(match=match, equipe=equipes[1])[1],
                                 "terrain": Tournoi.objects.get(idtournoi=idtournoi).terrains.all()[n - 1],
                                 "gagnant": "Égalité"})
                            n -= 1
                for equipe in Equipe.objects.filter(tournoi=tournoi):
                    exist = False
                    for info in infos:
                        if info["equipe"] == equipe:
                            exist = True
                    if exist == False:
                        infos.append({"total": 0,
                                      "joueur1": Utilisateur.objects.filter(match=match, equipe=equipe)[0],
                                      "joueur2": Utilisateur.objects.filter(match=match, equipe=equipe)[1],
                                      "equipe": equipe})
                infos_sorted_decroissant = sorted(infos, key=lambda x: x["total"], reverse=True)
                return render(request, 'gui/current_tournoi_equipe.html',
                              {"is_admin": is_admin, "current_tab": "tournois", "current_user": request.user,
                               "infos": infos_sorted_decroissant, "matchAVenir": match_a_venir,
                               "match_fait": match_fait,
                               "current_sport": current_sport})
        else:
            if tournoi.type.type[:6] == "Simple":
                liste_inscrits = Utilisateur.objects.filter(tournoi=tournoi).exclude(
                    user__groups__name="Administrateurs")
            elif tournoi.type.type[:6] == "Double":
                liste_inscrits = Utilisateur.objects.filter(equipe__tournoi=tournoi)
            return render(request, 'gui/tournoi_details.html',
                          {"liste_inscrits": liste_inscrits, 'tournoi': tournoi, "is_admin": is_admin,
                           "current_tab": "tournois", "gerants": gerants,
                           "user_participe": True,
                           "current_sport": current_sport})

def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')
    #return render(request)

def liste_utilisateurs(request, sport="default"):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    # Récupérer les paramètres de recherche et de tri
    tri = request.GET.get('tri')
    research = request.GET.get('research')

    # Appliquer la recherche si un terme est donné
    utilisateurs = Utilisateur.objects.all()  # Commencez avec tous les utilisateurs

    if research:
        utilisateurs = utilisateurs.filter(
            Q(user__first_name__icontains=research) |  # Recherche sur le prénom
            Q(user__last_name__icontains=research)   |   # Recherche sur le nom
            Q(user__username__icontains=research) #Recherche sur le surnom
        )
    utilisateurs = utilisateurs.exclude(user__groups__name="Administrateurs")
    utilisateurs = utilisateurs.exclude(user__groups__name="Supprimé")
    # Appliquer le tri
    if tri == 'Niveau':
        utilisateurs = utilisateurs.order_by('niveau__niveau')
    elif tri == 'Sport':
        utilisateurs = utilisateurs.order_by('sport_type__sport_type')
    elif tri == 'Nom_de_famille':
        utilisateurs = utilisateurs.order_by('user__last_name')
    if sport == "Tennis" or sport == "Badminton":
        utilisateurs = utilisateurs.filter(sport_type__sport_type=sport)
    elif current_sport == "Tennis" or current_sport == "Badminton":
        utilisateurs = utilisateurs.filter(sport_type__sport_type=current_sport)

    return render(request, 'gui/joueurs.html', {"current_sport":current_sport,'utilisateurs': utilisateurs, 'tri': tri, "current_tab" : "joueurs", "is_admin" : is_admin})

def supprimer_compte(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    if request.method == 'POST':
        groupe_supprime, cree = Group.objects.get_or_create(name="Supprimé")
        user = request.user
        user.groups.clear()
        user.groups.add(groupe_supprime)
        user.is_active = False
        user.save()
        messages.success(request, "Votre compte a été supprimé avec succès.")
        return redirect('home')
    return render(request, 'gui/supprimer_compte.html', context={"current_sport":current_sport,"current_tab" : "profil", "is_admin" : is_admin})

def desinscription_tournoi(request, idtournoi):
    tournoi = get_object_or_404(Tournoi, idtournoi=idtournoi)
    if tournoi.type.type[:6] == "Simple":
        Utilisateur.objects.get(user=request.user).tournoi.delete(tournoi)
        html_content = render_to_string('gui/email_desinscription_simple.html',
                                        {'tournoi': tournoi})
        send_mail(
            f'Désinscription au tournoi {tournoi.nom}',
            f'Bonjour {request.user.username}, vous avez été désinscrits avec succès',
            'service.raqtour@gmail.com',
            [request.user.email],
            fail_silently=False,
            html_message=html_content
        )
    elif tournoi.type.type[:6] == "Double":
        liste_equipes = Utilisateur.objects.get(user=request.user).equipe.all()
        for equipe_inscrit in liste_equipes:
            liste_tournois = equipe_inscrit.tournoi.all()
            for tournoi_inscrit in liste_tournois:
                if tournoi_inscrit == tournoi:
                    equipe = equipe_inscrit
        teammate = Utilisateur.objects.filter(equipe=equipe).exclude(user=request.user).first()
        #Utilisateur.objects.get(user=request.user).equipe.tournoi.delete(tournoi)
        if equipe:
            equipe.tournoi.remove(tournoi)
            user = Utilisateur.objects.get(user=request.user)
            html_content = render_to_string('gui/email_desinscription_tournoi.html', {'user': user, 'nom_equipe': equipe, 'tournoi': tournoi})
            send_mail(
                f'Désinscription de votre équipe {equipe.nom_equipe} au tournoi {tournoi.nom}',
                f'Bonjour {equipe.nom_equipe}, vous avez été désinscrits avec succès',
                'service.raqtour@gmail.com',
                [teammate.user.email, user.user.email],
                fail_silently=False,
                html_message=html_content
            )
    messages.success(request, "Vous avez été désinscrit avec succès.")
    return redirect('liste_tournois', tri=default)

def desinscrire_equipe(request, instance):
    participations = Utilisateur.objects.filter(user=instance)

    for participation in participations:
        equipe = participation.equipe

        # Si l'équipe existe
        if equipe:
            # Désinscrire l'équipe s'il manque un membre
            membres_restants = Utilisateur.objects.filter(equipe=equipe).exclude(user=instance)

            # Si l'équipe devient incomplète
            if membres_restants.count() < 2:
                # Supprimer toutes les participations de l'équipe au tournoi
                equipe.delete()

        participation.delete()

    messages.success(request, "Votre compte a été supprimé et l'équipe désinscrite avec succès.")

    return redirect('home')

def handle404(request, exception):
    return render(request, 'gui/404.html', status=404)

from django.utils.translation import gettext_lazy as _

# Dictionnaire pour stocker les titres et contenus des erreurs
VIEW_ERRORS = {
    404: {'title': _("Erreur 404 : Page non trouvée"),
          'content': _("Cette page n'existe pas ou a été déplacée.")},
}
def error_view_handler(request, exception, status):
    return render(request, template_name='gui/404.html', status=status,
                  context={'error': exception, 'status': status,
                           'title': VIEW_ERRORS[status]['title'],
                           'content': VIEW_ERRORS[status]['content']})

import logging
logger = logging.getLogger(__name__)

def error_404_view_handler(request, exception=None):
    logger.error("404 error handler called")
    return error_view_handler(request, exception, 404)

def handler404(request, exception):
    return render(request, 'gui/error.html', status=404)

def handler500(request, *args, **argv):
    return render(request, 'gui/error.html', status=500)

def handler403(request, exception):
    return render(request, 'gui/error.html', status=403)

def handler400(request, exception):
    return render(request, 'gui/error.html', status=400)
def actualiserScore(request, idTournoi, id_match):
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    if request.method == 'POST':
        match = MatchDeTournoi.objects.get(id_match=id_match)
        match_date_naive = match.date_heure_match.replace(tzinfo=None)
        if datetime.now() > match_date_naive :
            points1 = str(request.POST.get('points_1'))
            points2 = str(request.POST.get('points_2'))
            score = points1 + "-" + points2
            match.score = score
            match.points = 10
            match.save()

            return redirect("tournoi_details", idTournoi)
        else:
            messages.error(request, "Vous ne pouvez changez le score avant l'heure du match !")
            return redirect("tournoi_details", idTournoi)
def recupMDP(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    if request.method == 'POST':
        email = request.POST.get("email")
        exist = False
        for utilisateur in Utilisateur.objects.all():
            if utilisateur.user.email == email:
                bonUtilisateur = utilisateur
                exist = True
        if exist == True:
            return redirect("request_reset_code", username=bonUtilisateur.user.username)
        else:
            messages.error(request, "L'adresse mail n'existe pas ! Essayez une nouvelle adresse")
            return redirect("recuperation_mdp")
    return render(request, "gui/changepassword.html", {"is_admin" : is_admin, "current_sport" : current_sport, "current_tab" : "connexion"})

verification_codes = {}
def generateMDP(request, username):
    user = User.objects.get(username=username)
    email = Utilisateur.objects.get(user=user).user.email
    # Generate a random 6-digit code
    reset_code = random.randint(100000, 999999)
    verification_codes[email] = reset_code  # Store the code temporarily

    # Send the code via email
    html_content = render_to_string('gui/email_mdp.html', {'user': user, 'reset_code': reset_code})
    send_mail(
        'Réinitialisation de mot de passe',
        f'Bonjour {user.username},\n\nVotre code de réinitialisation est : {reset_code}',
        'service.raqtour@gmail.com',
        [email],
        fail_silently=False,
        html_message=html_content
    )
    messages.success(request, "Un code de réinitialisation a été envoyé à votre adresse e-mail.")
    return redirect('verify_reset_code', email=email)  # Redirect to the verification page
def verify_reset_code(request, email):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    """
    View to verify the reset code.
    """
    if request.method == "POST":
        #email = request.POST.get("email")
        entered_code = request.POST.get("code")
        if email in verification_codes and str(verification_codes[email]) == entered_code:
            messages.success(request, "Code vérifié. Vous pouvez maintenant changer votre mot de passe.")
            return redirect('reset_password', email=email)  # Redirect to the password reset page
        else:
            messages.error(request, "Code invalide ou expiré.")
    return render(request, "gui/verify_reset_code.html", {"is_admin" : is_admin, "current_sport" : current_sport, "current_tab" : "connexion"})
def reset_password(request, email):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    """
    View to reset the password.
    """
    if request.method == "POST":
        #email = request.POST.get("email")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if new_password == confirm_password:
            try:
                user = User.objects.get(email=email)
                user.password = make_password(new_password)
                user.save()
                messages.success(request, "Votre mot de passe a été modifié avec succès.")
                return redirect('connexion')  # Redirect to the login page
            except User.DoesNotExist:
                messages.error(request, "Aucun utilisateur trouvé avec cette adresse e-mail.")
        else:
            messages.error(request, "Les mots de passe ne correspondent pas.")
    return render(request, "gui/reset_password.html", {"is_admin":is_admin, "current_sport" : current_sport, "current_tab" : "connexion"})

def charte(request):
    return render(request, 'gui/charte.html')


def gerer_utilisateur_admin(request):
    current_sport = None
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    return render(request,'gui/gerer_utilisateurs_admin.html', {"is_admin" : is_admin, "current_sport" : current_sport, "current_tab" : "administration"})

def gerer_match_admin(request):
    current_sport = None
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    return render(request,'gui/gerer_matchs_admin.html', {"is_admin" : is_admin, "current_sport" : current_sport, "current_tab" : "administration"})


def changer_score(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirigez les utilisateurs non authentifiés

    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    if not is_admin:
        return redirect('home')  # Redirigez les utilisateurs non autorisés

    tournois = Utilisateur.objects.get(user=request.user).tournoi.all()
    selected_tournoi = None
    selected_match = None
    type_tournoi = None
    participant1 = None
    participant2 = None
    matchs = []
    message = None

    if request.method == "POST":
        tournoi_id = request.POST.get('tournoi')
        match_id = request.POST.get('match')
        score1 = request.POST.get('score1')
        score2 = request.POST.get('score2')

        if tournoi_id:
            selected_tournoi = get_object_or_404(Tournoi, idtournoi=tournoi_id)
            matchs_tournoi = MatchDeTournoi.objects.filter(tournoi=selected_tournoi)
            type_tournoi = selected_tournoi.type.type[:6]

        if match_id:
            selected_match = get_object_or_404(MatchDeTournoi, id_match=match_id)

        if match_id and score1 is not None and score2 is not None:
            selected_match = get_object_or_404(MatchDeTournoi, id_match=match_id)
            selected_match.score = f"{score1}-{score2}"
            selected_match.save()
            message = "Score mis à jour avec succès."
            return redirect('tournoi_details', idtournoi=tournoi_id)

        if type_tournoi == "Simple":
            for match in matchs_tournoi:
                participant1 = Utilisateur.objects.filter(match=match)[0]
                participant2 = Utilisateur.objects.filter(match=match)[1]
                matchs.append({"match": match, "participant1": participant1, "participant2": participant2})
        elif type_tournoi == "Double":
            for match in matchs_tournoi:
                participant1 = Utilisateur.objects.filter(match=match)[0].equipe.get(tournoi=selected_tournoi)
                participant2 = Utilisateur.objects.filter(match=match)[2].equipe.get(tournoi=selected_tournoi)
                matchs.append({"match": match, "participant1": participant1, "participant2": participant2})

    return render(request, 'gui/change_score.html', {
        "is_admin": is_admin,
        "tournois": tournois,
        "matchs": matchs,
        "selected_tournoi": selected_tournoi,
        "type_tournoi" : type_tournoi,
        "selected_match": selected_match,
        "message": message,
        "participant1" : participant1,
        "participant2": participant2,
    })

def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Récupérer les données du formulaire
            nom = form.cleaned_data['nom']
            email = form.cleaned_data['email']
            sujet = form.cleaned_data['sujet']
            message = form.cleaned_data['message']

            # Envoyer un email (exemple)
            send_mail(
                sujet,
                message,
                email,
                [settings.DEFAULT_FROM_EMAIL],  # Utiliser l'email défini dans settings.py
                fail_silently=False,
            )

            # Rediriger vers une page de succès
            return render(request, 'gui/success.html')  # Page de succès après envoi
    else:
        form = ContactForm()

    return render(request, 'gui/contact_form.html', {'form': form})



def changer_username(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    liste_utilisateurs = Utilisateur.objects.filter(sport_type=Utilisateur.objects.get(user=request.user).sport_type).exclude(user__groups__name="Administrateurs").exclude(user__groups__name="Supprimé")
    if request.method == 'POST':
        username_avant = request.POST.get('username_avant')
        username_now = request.POST.get('username_changed')
        if User.objects.filter(username=username_avant).exists():
            temp = User.objects.get(username=username_avant)
            temp.username = username_now
            temp.save()
            messages.success(request, "Username changé avec succès !")
            return redirect('/home')
        else:
            messages.error(request,"Cet username n'a pas été trouvé dans nos données.")
            return redirect('/changer_username')
    return render(request, 'gui/change_username.html', {"liste_utilisateurs":liste_utilisateurs,"is_admin": is_admin, "current_sport" : current_sport, "current_tab" : "administration"})

def changer_niveau(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None
    is_admin = request.user.groups.filter(name="Administrateurs").exists()
    liste_utilisateurs = Utilisateur.objects.filter(
        sport_type=Utilisateur.objects.get(user=request.user).sport_type).exclude(
        user__groups__name="Administrateurs").exclude(user__groups__name="Supprimé")
    liste_niveaux = Classement.objects.all()
    if request.method == 'POST':
        username_joueur = request.POST.get('username_joueur')
        niveau_now = int(request.POST.get('niveau_nouveau'))
        if User.objects.filter(username=username_joueur).exists():
            user = User.objects.get(username=username_joueur)
            temp = Utilisateur.objects.get(user=user)
            temp.niveau = Classement.objects.get(niveau=niveau_now)
            temp.save()
            messages.success(request, f"Niveau de {username_joueur} changé avec succès !")
            return redirect('/home')
        else:
            messages.error(request, "Cet username n'a pas été trouvé dans nos données.")
            return redirect('/changer_username')
    return render(request, 'gui/changer_niveau.html',{"liste_utilisateurs" : liste_utilisateurs, "liste_niveaux" : liste_niveaux,"is_admin": is_admin, "current_sport": current_sport, "current_tab": "administration"})

def supprimer_utilisateur_admin(request):
    if request.user.is_authenticated:
        current_sport = Utilisateur.objects.get(user=request.user).sport_type.sport_type
    else:
        current_sport = None

    is_admin = request.user.groups.filter(name="Administrateurs").exists()

    if request.method == 'POST':
        username_joueur = request.POST.get('username_joueur')
        if User.objects.filter(username=username_joueur).exists():
            groupe_supprime, cree = Group.objects.get_or_create(name="Supprimé")
            user = User.objects.get(username=username_joueur)
            user.groups.clear()
            user.groups.add(groupe_supprime)
            user.is_active = False
            user.save()
            messages.success(request, f"L'utilisateur {username_joueur} a été supprimé avec succès")
            return redirect('/home')
        else:
            messages.error(request, "Cet username n'a pas été trouvé dans nos données.")
            return redirect('/supprimer_utilisateur_admin')

    # Récupérer la liste des utilisateurs actifs pour l'administrateur
    utilisateurs = Utilisateur.objects.filter(sport_type__sport_type=current_sport).exclude(user__groups__name="Supprimé").exclude(user__groups__name="Administrateurs") # Vous pouvez filtrer selon des critères si nécessaire
    return render(request, 'gui/supprimer_utilisateur_admin.html', {
        "is_admin": is_admin,
        "current_sport": current_sport,
        "current_tab": "administration",
        "utilisateurs": utilisateurs  # Passer les utilisateurs à la vue
    })