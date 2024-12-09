# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from datetime import timezone, datetime, date

from django.db import models
from django.contrib.auth.models import User, Group
from django.template.defaultfilters import default


class Classement(models.Model):
    niveau = models.IntegerField(primary_key=True)
    description = models.TextField(blank=True, null=True)


class Equipe(models.Model):
    nom_equipe = models.CharField(primary_key=True, max_length=50)
    tournoi = models.ManyToManyField('Tournoi', blank=True, null=True)
    #user = models.ManyToManyField('Utilisateur', through='Participation_Equipe')


class MatchDeTournoi(models.Model):
    id_match = models.AutoField(primary_key=True)
    score = models.CharField(max_length=50, blank=True, null=True, default="a")
    points = models.IntegerField(blank=True, null=True, default=0)
    date_heure_match = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    tournoi = models.ForeignKey('Tournoi', on_delete=models.CASCADE)


class GroupPermission(models.Model): # Renommé pour éviter les conflits
    role = models.OneToOneField(Group, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)


class Sexe(models.Model):
    sexe = models.CharField(primary_key=True, max_length=50)


class Sports(models.Model):
    sport_type = models.CharField(primary_key=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.sport_type


class Terrain(models.Model):
    numero_terrain = models.IntegerField(primary_key=True)
    commentaire = models.TextField(blank=True, null=True)


class Tournoi(models.Model):
    idtournoi = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=50)
    periode_debut = models.DateField(default=date.today)
    periode_fin = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    type = models.ForeignKey('Type', on_delete=models.CASCADE)
    terrains = models.ManyToManyField(Terrain, blank=True, null=True)
    #equipe = models.ManyToManyField(Equipe, blank=True, through='Participation_Equipe')
    #user = models.ManyToManyField('Utilisateur', through='Participation_Equipe')


class Type(models.Model):
    type = models.CharField(primary_key=True, max_length=50)
    description = models.TextField(blank=True, null=True)


class Utilisateur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    sexe = models.ForeignKey(Sexe, on_delete=models.CASCADE)
    sport_type = models.ForeignKey(Sports, on_delete=models.CASCADE)
    niveau = models.ForeignKey(Classement, on_delete=models.CASCADE)
    equipe = models.ManyToManyField(Equipe, blank=True)
    tournoi = models.ManyToManyField(Tournoi, blank=True)
    match = models.ManyToManyField(MatchDeTournoi, blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"
