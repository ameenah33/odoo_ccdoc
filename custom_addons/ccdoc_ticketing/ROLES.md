# Rôles et Droits d'accès - Module Ticketing CCDOC



Ce document décrit les 4 rôles utilisateurs du module Ticketing et leurs droits d'accès respectifs.

---

## 📋 Vue d'ensemble des rôles

| Rôle | Description | Cas d'usage typique |
|------|-------------|---------------------|
| **Demandeur** | Crée et suit ses propres tickets | Clients, utilisateurs finaux |
| **Agent Support** | Prend en charge, traite et clôture les tickets | Techniciens support, équipe de première ligne |
| **Superviseur Support** | Suit l'activité, valide clôtures, consulte rapports | Chef d'équipe support, manager |
| **Administrateur** | Paramètre le module et gère les droits | Admin système, responsable IT |

---

## 1️⃣ Demandeur (Requester)

### Description
Rôle pour les **clients** ou **utilisateurs finaux** qui créent des tickets de support et suivent leur progression.

### Droits d'accès

#### Tickets:
- ✅ **Voir** uniquement SES PROPRES tickets (liés à son compte partenaire)
- ❌ **Modifier** les tickets (lecture seule)
- ✅ **Créer** de nouveaux tickets
- ❌ **Supprimer** les tickets

#### Configuration (Étapes, Catégories, Tags):
- ✅ **Voir** (lecture seule)
- ❌ Aucune modification

#### Menus visibles:
- Ticketing → Tickets → **Mes tickets**

### Comment assigner ce rôle:

1. **Aller dans Paramètres → Utilisateurs & Entreprises → Utilisateurs**
2. **Sélectionner ou créer un utilisateur**
3. **Onglet "Droits d'accès"**
4. **Services → Cocher "Ticketing / Demandeur"**
5. **Lier l'utilisateur à un contact/partenaire** (important pour voir ses tickets)

### Notes importantes:
- Le demandeur doit avoir un **Contact (res.partner)** lié à son compte utilisateur
- Les tickets doivent avoir le champ `partner_id` rempli pour être visibles
- Ce rôle est parfait pour donner un accès limité aux clients

---

## 2️⃣ Agent Support (Agent)

### Description
Rôle pour les **techniciens** et **équipe de support** qui traitent les tickets au quotidien.

### Droits d'accès

#### Tickets:
- ✅ **Voir** les tickets qui lui sont assignés + tickets non assignés
- ✅ **Modifier** les tickets (changer statut, ajouter commentaires, etc.)
- ✅ **Créer** de nouveaux tickets
- ❌ **Supprimer** les tickets

#### Configuration (Étapes, Catégories, Tags):
- ✅ **Voir** (lecture seule)
- ❌ Aucune modification

#### Menus visibles:
- Ticketing → Tickets → **Tous les tickets**
- Ticketing → Tickets → **Mes tickets**

### Comment assigner ce rôle:

1. **Aller dans Paramètres → Utilisateurs & Entreprises → Utilisateurs**
2. **Sélectionner ou créer un utilisateur**
3. **Onglet "Droits d'accès"**
4. **Services → Cocher "Ticketing / Agent Support"**

### Notes importantes:
- Les agents voient automatiquement les tickets non assignés (pour prise en charge)
- Idéal pour l'équipe de première ligne
- Hérite automatiquement du rôle "Demandeur"

---

## 3️⃣ Superviseur Support (Supervisor)

### Description
Rôle pour les **managers** et **superviseurs** qui suivent l'activité globale et valident les clôtures.

### Droits d'accès

#### Tickets:
- ✅ **Voir** TOUS les tickets (sans restriction)
- ✅ **Modifier** tous les tickets
- ✅ **Créer** de nouveaux tickets
- ❌ **Supprimer** les tickets

#### Configuration (Étapes, Catégories, Tags):
- ✅ **Voir** la configuration
- ✅ **Modifier** la configuration (étapes, catégories, tags)
- ✅ **Créer** de nouveaux éléments de configuration
- ❌ **Supprimer** les éléments de configuration

#### Menus visibles:
- Ticketing → Tickets → **Tous les tickets**
- Ticketing → Tickets → **Mes tickets**
- *(Configuration NON visible - réservé aux admins)*

### Comment assigner ce rôle:

1. **Aller dans Paramètres → Utilisateurs & Entreprises → Utilisateurs**
2. **Sélectionner ou créer un utilisateur**
3. **Onglet "Droits d'accès"**
4. **Services → Cocher "Ticketing / Superviseur Support"**

### Notes importantes:
- Voit tous les tickets pour supervision globale
- Peut valider/modifier les clôtures
- Hérite automatiquement des rôles "Agent" et "Demandeur"
- Parfait pour les chefs d'équipe support

---

## 4️⃣ Administrateur (Admin)

### Description
Rôle pour les **administrateurs système** qui paramètrent le module et gèrent tous les aspects techniques.

### Droits d'accès

#### Tickets:
- ✅ **Voir** TOUS les tickets
- ✅ **Modifier** tous les tickets
- ✅ **Créer** de nouveaux tickets
- ✅ **Supprimer** les tickets

#### Configuration (Étapes, Catégories, Tags):
- ✅ **Voir** la configuration
- ✅ **Modifier** la configuration
- ✅ **Créer** de nouveaux éléments
- ✅ **Supprimer** des éléments

#### Menus visibles:
- Ticketing → Tickets → **Tous les tickets**
- Ticketing → Tickets → **Mes tickets**
- Ticketing → **Configuration** (Étapes, Catégories, Tags)

### Comment assigner ce rôle:

1. **Aller dans Paramètres → Utilisateurs & Entreprises → Utilisateurs**
2. **Sélectionner ou créer un utilisateur**
3. **Onglet "Droits d'accès"**
4. **Services → Cocher "Ticketing / Administrateur"**

### Notes importantes:
- Seul rôle avec droit de suppression
- Seul rôle avec accès au menu Configuration
- Hérite automatiquement de tous les autres rôles
- Réservé aux admins système

---

## 🔄 Hiérarchie des rôles

Les rôles sont hiérarchiques (chaque rôle supérieur hérite des droits du rôle inférieur):

```
Administrateur
    ↓ (hérite de)
Superviseur Support
    ↓ (hérite de)
Agent Support
    ↓ (hérite de)
Demandeur
```

### Implications pratiques:
- Si vous assignez **Agent**, l'utilisateur a aussi les droits **Demandeur**
- Si vous assignez **Superviseur**, l'utilisateur a les droits **Agent** + **Demandeur**
- Si vous assignez **Admin**, l'utilisateur a TOUS les droits

---

## 🛠️ Guide de configuration des utilisateurs

### Scénario 1: Client externe
**Objectif:** Permettre au client de créer et suivre ses tickets

1. Créer un contact (Contacts → Créer)
2. Créer un utilisateur lié à ce contact
3. Assigner le rôle **Demandeur**
4. Le client verra uniquement ses propres tickets

### Scénario 2: Technicien support
**Objectif:** Traiter les tickets assignés

1. Créer un utilisateur interne
2. Assigner le rôle **Agent Support**
3. Le technicien voit les tickets assignés + non assignés

### Scénario 3: Responsable support
**Objectif:** Superviser l'équipe et valider les clôtures

1. Créer un utilisateur interne
2. Assigner le rôle **Superviseur Support**
3. Le responsable voit tous les tickets

### Scénario 4: Admin système
**Objectif:** Configurer le module

1. Créer un utilisateur interne
2. Assigner le rôle **Administrateur**
3. L'admin a accès complet (y compris Configuration)

---

## 📊 Tableau récapitulatif des droits

| Action | Demandeur | Agent | Superviseur | Admin |
|--------|:---------:|:-----:|:-----------:|:-----:|
| **TICKETS** | | | | |
| Voir ses propres tickets | ✅ | ✅ | ✅ | ✅ |
| Voir tickets assignés + non assignés | ❌ | ✅ | ✅ | ✅ |
| Voir tous les tickets | ❌ | ❌ | ✅ | ✅ |
| Créer un ticket | ✅ | ✅ | ✅ | ✅ |
| Modifier un ticket | ❌ | ✅ | ✅ | ✅ |
| Supprimer un ticket | ❌ | ❌ | ❌ | ✅ |
| **CONFIGURATION** | | | | |
| Voir étapes/catégories/tags | ✅ | ✅ | ✅ | ✅ |
| Modifier configuration | ❌ | ❌ | ✅ | ✅ |
| Supprimer configuration | ❌ | ❌ | ❌ | ✅ |
| Accès menu Configuration | ❌ | ❌ | ❌ | ✅ |

---

## ⚠️ Bonnes pratiques

### 1. Principe du moindre privilège
Assignez le rôle le plus bas nécessaire pour chaque utilisateur. Ne donnez pas le rôle Admin à tout le monde.

### 2. Lier les demandeurs à des contacts
Pour que la règle d'accès fonctionne correctement, les utilisateurs avec le rôle "Demandeur" **DOIVENT** être liés à un contact (res.partner).

### 3. Tester les droits
Après avoir assigné un rôle, testez en vous connectant avec ce compte pour vérifier les accès.

### 4. Documentation interne
Documentez qui a quel rôle dans votre organisation et pourquoi.

---

## 🔍 Dépannage

### Problème: Un demandeur ne voit aucun ticket

**Cause:** L'utilisateur n'est pas lié à un contact OU les tickets n'ont pas de `partner_id`

**Solution:**
1. Vérifier que l'utilisateur a un contact lié (Paramètres → Utilisateurs → Onglet Contact associé)
2. Vérifier que les tickets ont le champ "Client" rempli

### Problème: Un agent ne voit pas les tickets non assignés

**Cause:** Les règles d'accès ne sont pas bien appliquées

**Solution:**
1. Mettre à jour le module Ticketing
2. Vérifier que l'utilisateur a bien le rôle "Agent Support"
3. Rafraîchir la page (F5)

### Problème: Le menu Configuration n'apparaît pas

**Cause:** L'utilisateur n'a pas le rôle Administrateur

**Solution:**
1. Seuls les utilisateurs avec le rôle "Administrateur" voient ce menu
2. Vérifier dans Paramètres → Utilisateurs → Droits d'accès

---

## 📞 Support

Pour toute question sur les rôles et droits d'accès:
- Consulter ce document
- Contacter l'équipe technique CCDOC
- Vérifier les logs Odoo en cas d'erreur d'accès
