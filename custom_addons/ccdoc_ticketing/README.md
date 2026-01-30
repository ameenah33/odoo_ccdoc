# Module CCDOC Ticketing - Documentation

## Vue d'ensemble

Module de gestion de tickets de support pour CCDOC avec automatisations complètes conformes au cahier des charges.

## ✅ Fonctionnalités implémentées (Phase 1 - Automatisations)

### 1. Création automatique de tickets par email

Le module supporte la création automatique de tickets à partir d'emails reçus.

#### Configuration de l'alias email:

1. **Aller dans Paramètres → Technique → Alias d'email**
2. **Créer un nouvel alias:**
   - Nom de l'alias: `support` (ou autre selon votre choix)
   - Modèle: `ccdoc.ticket`
   - Créer des enregistrements: Activé

3. **Configuration du serveur email entrant** (si pas déjà fait):
   - Aller dans Paramètres → Technique → Serveurs de messagerie entrants
   - Configurer votre serveur IMAP/POP3
   - Exemple: support@ccdoc.com

Une fois configuré, tous les emails reçus à `support@votredomaine.com` créeront automatiquement un ticket.

### 2. Accusé de réception automatique

Dès qu'un ticket est créé (manuellement ou par email), un email d'accusé de réception est automatiquement envoyé au demandeur.

**Contenu de l'email:**
- Numéro du ticket
- Sujet
- Priorité
- Statut initial
- Date de création

**Template:** `CCDOC Ticketing: Accusé de réception`

### 3. Notifications automatiques de changement de statut

Chaque changement d'étape du ticket déclenche une notification email au client.

**Événements notifiés:**
- Changement de statut général
- Clôture du ticket (avec résolution si renseignée)

**Templates:**
- `CCDOC Ticketing: Changement de statut`
- `CCDOC Ticketing: Ticket clôturé`

### 4. Alertes SLA automatiques

Un cron job vérifie toutes les heures les tickets avec SLA dépassé ou à risque.

#### Fonctionnement:

- **Fréquence:** Toutes les heures
- **Critères:** Tickets ouverts avec statut SLA = "En retard" ou "À risque"
- **Destinataires:** Agent assigné au ticket
- **Limite:** Maximum 1 alerte par ticket toutes les 24h (pour éviter le spam)

**Template:** `CCDOC Ticketing: Alerte SLA`

## Configuration requise

### Serveur de messagerie sortant (SMTP)

Pour que les notifications fonctionnent, configurez un serveur SMTP:

1. **Aller dans Paramètres → Technique → Serveurs de messagerie sortants**
2. **Configurer le serveur SMTP:**
   - Nom: Serveur CCDOC
   - Serveur SMTP: smtp.votre-domaine.com
   - Port: 587 (ou 465 pour SSL)
   - Connexion sécurisée: TLS/SSL
   - Nom d'utilisateur: support@ccdoc.com
   - Mot de passe: [votre mot de passe]

3. **Tester la connexion**

### Serveur de messagerie entrant (IMAP/POP3)

Pour la création automatique de tickets par email:

1. **Aller dans Paramètres → Technique → Serveurs de messagerie entrants**
2. **Configurer le serveur:**
   - Nom: Support CCDOC
   - Type de serveur: IMAP ou POP3
   - Serveur: imap.votre-domaine.com
   - Port: 993 (IMAP SSL) ou 995 (POP3 SSL)
   - SSL/TLS: Activé
   - Nom d'utilisateur: support@ccdoc.com
   - Mot de passe: [votre mot de passe]

3. **Lier à l'alias email** créé précédemment

## Utilisation

### Création d'un ticket

**Méthode 1: Depuis l'interface Odoo**
1. Menu Ticketing → Tickets → Créer
2. Remplir le formulaire
3. Le client recevra un email de confirmation automatique

**Méthode 2: Par email**
1. Envoyer un email à support@votredomaine.com
2. Le ticket sera créé automatiquement
3. L'expéditeur recevra un accusé de réception

### Suivi d'un ticket

1. L'agent assigné travaille sur le ticket
2. À chaque changement d'étape, le client reçoit une notification
3. Si le SLA risque d'être dépassé, l'agent reçoit une alerte

### Clôture d'un ticket

1. Renseigner le champ "Résolution" (optionnel mais recommandé)
2. Passer le ticket à l'étape "Fermé"
3. Le client reçoit automatiquement un email de clôture avec le résumé

## Gestion des templates d'email

### Personnaliser les templates:

1. **Aller dans Paramètres → Technique → Templates d'email**
2. **Rechercher:** "CCDOC Ticketing"
3. **4 templates disponibles:**
   - Accusé de réception
   - Changement de statut
   - Ticket clôturé
   - Alerte SLA

4. **Modifier selon vos besoins:**
   - Sujet de l'email
   - Corps du message (HTML)
   - Expéditeur
   - Destinataires

## Gestion du cron job SLA

### Vérifier le cron job:

1. **Aller dans Paramètres → Technique → Actions planifiées**
2. **Rechercher:** "CCDOC Ticketing: Vérification des SLA"
3. **Configuration:**
   - Intervalle: 1 heure (modifiable)
   - Actif: Oui
   - Exécutions: Illimité

### Désactiver les alertes SLA:

Si vous souhaitez temporairement désactiver les alertes SLA:
1. Décocher "Actif" sur l'action planifiée

### Modifier la fréquence:

Vous pouvez changer la fréquence des vérifications:
- Toutes les 30 minutes: Intervalle = 30, Type = Minutes
- Toutes les 2 heures: Intervalle = 2, Type = Heures
- Une fois par jour: Intervalle = 1, Type = Jours

## Tests recommandés

### Test 1: Création de ticket manuel
1. Créer un ticket avec un client ayant une adresse email valide
2. Vérifier que l'email d'accusé de réception est bien envoyé

### Test 2: Changement de statut
1. Passer un ticket de "Nouveau" à "En cours"
2. Vérifier que le client reçoit la notification

### Test 3: Clôture de ticket
1. Renseigner une résolution
2. Fermer le ticket
3. Vérifier l'email de clôture

### Test 4: Alerte SLA
1. Créer un ticket avec SLA de 1 heure
2. Attendre que le SLA soit dépassé
3. Lancer manuellement le cron: Paramètres → Technique → Actions planifiées → "Vérification des SLA" → Bouton "Lancer maintenant"
4. Vérifier que l'agent assigné reçoit l'alerte

## Dépannage

### Les emails ne sont pas envoyés

**Vérifications:**
1. Le serveur SMTP est-il correctement configuré et testé?
2. Le mode développeur permet de voir les logs d'erreur
3. Vérifier dans Paramètres → Technique → Emails pour voir les emails en attente

### Le cron ne s'exécute pas

**Vérifications:**
1. Le cron est-il actif?
2. Vérifier les logs Odoo: `docker-compose logs odoo | grep -i "cron"`
3. Tester manuellement l'action planifiée

### Les tickets ne se créent pas par email

**Vérifications:**
1. Le serveur de messagerie entrant est-il configuré?
2. L'alias email est-il bien lié au modèle `ccdoc.ticket`?
3. Tester la récupération manuelle des emails

## Prochaines phases

### Phase 2 - Reporting (À venir)
- Rapports d'analyse
- Statistiques de performance
- Export Excel/PDF

### Phase 3 - Améliorations fonctionnelles (À venir)
- Champ "Temps passé"
- Catégorisation avancée (Type + Domaine)
- Dashboard avec KPIs
- Rôle "Demandeur" distinct

## Support

Pour toute question ou problème:
- Consulter les logs Odoo
- Vérifier la configuration email
- Contacter l'équipe technique CCDOC
