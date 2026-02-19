#!/usr/bin/env bash
# ================================================================
# CCDOC Odoo - Script de sécurisation initiale
# Compatible macOS et Linux
# ================================================================

set -e

echo ""
echo "========================================================"
echo "  CCDOC Odoo - Initialisation de la sécurité"
echo "========================================================"
echo ""

# ----------------------------------------------------------------
# 1. Génération de mots de passe forts
# ----------------------------------------------------------------
echo "[1/4] Génération des mots de passe sécurisés..."

DB_PASSWORD=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)))")
ODOO_ADMIN_PASSWORD=$(python3 -c "import secrets, string; chars = string.ascii_letters + string.digits + '!@#\$%^&*'; print(''.join(secrets.choice(chars) for _ in range(32)))")

echo "  ✅ Mot de passe PostgreSQL généré"
echo "  ✅ Mot de passe admin Odoo généré"
echo ""

# ----------------------------------------------------------------
# 2. Mise à jour du fichier .env
# ----------------------------------------------------------------
echo "[2/4] Mise à jour du fichier .env..."

cat > .env << EOF
# ================================================================
# Variables d'environnement CCDOC Odoo - GÉNÉRÉ AUTOMATIQUEMENT
# NE PAS COMMITER CE FICHIER DANS GIT
# ================================================================

POSTGRES_DB=postgres
POSTGRES_USER=odoo
POSTGRES_PASSWORD=${DB_PASSWORD}
ODOO_ADMIN_PASSWORD=${ODOO_ADMIN_PASSWORD}
EOF

echo "  ✅ Fichier .env mis à jour"

# ----------------------------------------------------------------
# 3. Mise à jour de config/odoo.conf
# Compatible macOS (sed -i '') et Linux (sed -i)
# ----------------------------------------------------------------
echo "[3/4] Mise à jour de config/odoo.conf..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/CHANGE_ME_USE_A_STRONG_32_CHARS_PASSWORD/${ODOO_ADMIN_PASSWORD}/" config/odoo.conf
    sed -i '' "s/CHANGE_ME_STRONG_DB_PASSWORD/${DB_PASSWORD}/" config/odoo.conf
else
    # Linux
    sed -i "s/CHANGE_ME_USE_A_STRONG_32_CHARS_PASSWORD/${ODOO_ADMIN_PASSWORD}/" config/odoo.conf
    sed -i "s/CHANGE_ME_STRONG_DB_PASSWORD/${DB_PASSWORD}/" config/odoo.conf
fi

echo "  ✅ config/odoo.conf mis à jour"

# --- AJOUT : Mise à jour de /etc/odoo.conf si présent ---
if [ -f /etc/odoo.conf ]; then
    echo "  ➡️  Mise à jour de /etc/odoo.conf..."
    sudo sed -i "s/CHANGE_ME_USE_A_STRONG_32_CHARS_PASSWORD/${ODOO_ADMIN_PASSWORD}/" /etc/odoo.conf
    sudo sed -i "s/CHANGE_ME_STRONG_DB_PASSWORD/${DB_PASSWORD}/" /etc/odoo.conf
    echo "  ✅ /etc/odoo.conf mis à jour"
fi

# ----------------------------------------------------------------
# 4. Vérification du .gitignore
# ----------------------------------------------------------------
echo "[4/4] Vérification du .gitignore..."

if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo "  ✅ .env ajouté au .gitignore"
else
    echo "  ✅ .env déjà dans .gitignore"
fi

if ! grep -q "^backups/" .gitignore 2>/dev/null; then
    echo "backups/" >> .gitignore
fi

# ----------------------------------------------------------------
# Récapitulatif
# ----------------------------------------------------------------
echo ""
echo "========================================================"
echo "  RÉCAPITULATIF DES CREDENTIALS GÉNÉRÉS"
echo "  ⚠️  SAUVEGARDER CES INFORMATIONS EN LIEU SÛR !"
echo "========================================================"
echo ""
echo "  PostgreSQL Password : ${DB_PASSWORD}"
echo "  Odoo Admin Password : ${ODOO_ADMIN_PASSWORD}"
echo ""
echo "  Ces valeurs sont également dans le fichier .env"
echo ""
echo "========================================================"
echo "  PROCHAINES ÉTAPES"
echo "========================================================"
echo ""
echo "  1. Redémarrer les conteneurs Docker :"
echo "     docker compose down && docker compose up -d"
echo ""
echo "  2. Installer le module ccdoc_security dans Odoo :"
echo "     Paramètres → Applications → Rechercher 'CCDOC Security' → Installer"
echo ""
echo "  3. Activer le MFA pour tous les utilisateurs :"
echo "     Paramètres → Utilisateurs → Authentification à deux facteurs"
echo ""