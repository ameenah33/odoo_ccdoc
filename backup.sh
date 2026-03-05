#!/bin/bash

# Script de sauvegarde automatique pour CCDOC Odoo
# Auteur: Aminata Diagne
# Date de création: 2026-02-02

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="ccdoc-postgres"
DB_NAME="odoo"
DB_USER="odoo"


GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "  CCDOC - Sauvegarde Automatique"
echo "======================================"
echo ""
mkdir -p "$BACKUP_DIR"
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED} Erreur: Docker n'est pas démarré${NC}"
    echo "Veuillez démarrer Docker Desktop et réessayer."
    exit 1
fi

if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${RED} Erreur: Le conteneur $DB_CONTAINER n'est pas démarré${NC}"
    echo "Démarrez les conteneurs avec: docker-compose up -d"
    exit 1
fi

echo -e "${YELLOW}📦 Début de la sauvegarde...${NC}"
echo ""

#  Sauvegarde de la base de données PostgreSQL
echo -e "${YELLOW}[1/3] Sauvegarde de la base de données PostgreSQL...${NC}"
DB_BACKUP="$BACKUP_DIR/odoo_backup_${TIMESTAMP}.sql"
if docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" > "$DB_BACKUP"; then
    DB_SIZE=$(du -h "$DB_BACKUP" | cut -f1)
    echo -e "${GREEN}✓ Base de données sauvegardée: $DB_BACKUP ($DB_SIZE)${NC}"
else
    echo -e "${RED}✗ Échec de la sauvegarde de la base de données${NC}"
    exit 1
fi

# Sauvegarde des modules personnalisés
echo -e "${YELLOW}[2/3] Sauvegarde des modules personnalisés...${NC}"
ADDONS_BACKUP="$BACKUP_DIR/custom_addons_backup_${TIMESTAMP}.tar.gz"
if tar -czf "$ADDONS_BACKUP" custom_addons/ 2>/dev/null; then
    ADDONS_SIZE=$(du -h "$ADDONS_BACKUP" | cut -f1)
    echo -e "${GREEN}✓ Modules sauvegardés: $ADDONS_BACKUP ($ADDONS_SIZE)${NC}"
else
    echo -e "${RED}✗ Échec de la sauvegarde des modules${NC}"
fi

# Sauvegarde du filestore Odoo (fichiers uploadés)
echo -e "${YELLOW}[3/3] Sauvegarde des fichiers Odoo (pièces jointes, images...)${NC}"
FILESTORE_BACKUP="$BACKUP_DIR/odoo_filestore_backup_${TIMESTAMP}.tar.gz"
if docker run --rm -v odoo_ccdoc_odoo_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar -czf /backup/odoo_filestore_backup_${TIMESTAMP}.tar.gz -C /data . 2>/dev/null; then
    FILESTORE_SIZE=$(du -h "$FILESTORE_BACKUP" | cut -f1)
    echo -e "${GREEN}✓ Filestore sauvegardé: $FILESTORE_BACKUP ($FILESTORE_SIZE)${NC}"
else
    echo -e "${RED}✗ Échec de la sauvegarde du filestore${NC}"
fi

echo ""
echo -e "${GREEN}======================================"
echo -e "  ✓ Sauvegarde terminée avec succès!"
echo -e "======================================${NC}"
echo ""
echo "Emplacement: $BACKUP_DIR"
echo " Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Fichiers créés:"
ls -lh "$BACKUP_DIR" | grep "$TIMESTAMP"
echo ""


echo -e "${YELLOW}🧹 Nettoyage des anciennes sauvegardes (conservation des 7 dernières)...${NC}"
cd "$BACKUP_DIR" || exit
ls -t odoo_backup_*.sql 2>/dev/null | tail -n +8 | xargs -r rm
ls -t custom_addons_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
ls -t odoo_filestore_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
echo -e "${GREEN}✓ Nettoyage terminé${NC}"
echo ""
