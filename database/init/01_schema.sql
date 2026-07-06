-- Schéma PostgreSQL — P13 Effectifs scolaires Rennes Métropole

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Référentiel communes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS communes (
    code_insee       VARCHAR(5) PRIMARY KEY,
    nom_commune      VARCHAR(100) NOT NULL,
    code_departement VARCHAR(3),
    departement      VARCHAR(50),
    region           VARCHAR(50),
    epci             VARCHAR(100),
    population       INTEGER,
    superficie_km2   NUMERIC(10, 2),
    densite_hab_km2  NUMERIC(10, 2)
);

-- ---------------------------------------------------------------------------
-- Statistiques communales (sans géométrie lourde)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stats_communes (
    code_insee           VARCHAR(5) PRIMARY KEY REFERENCES communes(code_insee),
    nom_commune          VARCHAR(100),
    geo_point            VARCHAR(50),
    pop_1968             INTEGER,
    pop_1975             INTEGER,
    pop_1982             INTEGER,
    pop_1990             INTEGER,
    pop_1999             INTEGER,
    pop_2009             INTEGER,
    pop_2014             INTEGER,
    pop_2020             INTEGER,
    pop_2021             INTEGER,
    pop_estim_2023       INTEGER,
    pop_proj_2030        INTEGER,
    pop_proj_2040        INTEGER,
    cat_0_14_2020        NUMERIC(5, 2),
    cat_15_29_2020       NUMERIC(5, 2),
    cat_30_44_2020       NUMERIC(5, 2),
    cat_45_59_2020       NUMERIC(5, 2),
    cat_60_74_2020       NUMERIC(5, 2),
    cat_75_plus_2020     NUMERIC(5, 2),
    densite_2021         NUMERIC(10, 2),
    mortalite_2022       NUMERIC(6, 2),
    natalite_2022        NUMERIC(6, 2),
    cat_15_plus_2020     INTEGER,
    emploi_2018          INTEGER,
    emploi_2021          INTEGER,
    ecole_mat_ele        INTEGER,
    college              INTEGER,
    lycee                INTEGER,
    log_collectif        INTEGER,
    log_individuel       INTEGER,
    plh_nb_log_a_const   INTEGER
);

-- ---------------------------------------------------------------------------
-- Effectifs scolaires (agrégés par commune / année / secteur)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ecoles_effectifs (
    id                   SERIAL PRIMARY KEY,
    rentree              INTEGER NOT NULL,
    code_insee           VARCHAR(5) REFERENCES communes(code_insee),
    nom_commune          VARCHAR(100),
    numero_ecole         VARCHAR(20),
    denomination         VARCHAR(200),
    type_ecole           VARCHAR(30),   -- MATERNELLE | ELEMENTAIRE | PRIMAIRE
    secteur              VARCHAR(20),
    rep                  SMALLINT DEFAULT 0,  -- 1 = Réseau Education Prioritaire
    rep_plus             SMALLINT DEFAULT 0,  -- 1 = REP+
    nb_classes           NUMERIC(6, 1),
    nb_eleves_total      NUMERIC(8, 1),
    nb_eleves_maternelle NUMERIC(8, 1),
    nb_eleves_elementaire NUMERIC(8, 1),
    nb_eleves_cp         NUMERIC(8, 1),
    nb_eleves_ce1        NUMERIC(8, 1),
    nb_eleves_ce2        NUMERIC(8, 1),
    nb_eleves_cm1        NUMERIC(8, 1),
    nb_eleves_cm2        NUMERIC(8, 1)
);

CREATE INDEX IF NOT EXISTS idx_ecoles_rentree ON ecoles_effectifs(rentree);
CREATE INDEX IF NOT EXISTS idx_ecoles_commune ON ecoles_effectifs(code_insee);

-- Vue agrégée commune / année (toutes écoles confondues)
CREATE OR REPLACE VIEW v_effectifs_commune_annee AS
SELECT
    e.rentree,
    e.code_insee,
    c.nom_commune,
    SUM(e.nb_classes)                                       AS nb_classes,
    SUM(e.nb_eleves_total)                                  AS nb_eleves_total,
    SUM(e.nb_eleves_maternelle)                             AS nb_eleves_maternelle,
    SUM(e.nb_eleves_elementaire)                            AS nb_eleves_elementaire,
    -- Agrégats par type d'école
    SUM(CASE WHEN e.type_ecole = 'MATERNELLE' THEN e.nb_eleves_maternelle  ELSE 0 END) AS nb_eleves_ecoles_mat,
    SUM(CASE WHEN e.type_ecole = 'ELEMENTAIRE' THEN e.nb_eleves_elementaire ELSE 0 END) AS nb_eleves_ecoles_elem,
    -- Indicateurs REP
    COUNT(CASE WHEN e.rep = 1 THEN 1 END)                  AS nb_ecoles_rep,
    COUNT(CASE WHEN e.rep_plus = 1 THEN 1 END)             AS nb_ecoles_rep_plus,
    COUNT(*)                                                AS nb_ecoles
FROM ecoles_effectifs e
LEFT JOIN communes c ON c.code_insee = e.code_insee
GROUP BY e.rentree, e.code_insee, c.nom_commune;

-- ---------------------------------------------------------------------------
-- Population 2014 par tranche d'âge
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS population_2014 (
    id              SERIAL PRIMARY KEY,
    code_insee      VARCHAR(5) REFERENCES communes(code_insee),
    tranche_age     VARCHAR(50),
    nationalite     VARCHAR(30),
    sexe            VARCHAR(10),
    effectif        NUMERIC(12, 2)
);

-- ---------------------------------------------------------------------------
-- Mutations immobilières DVF
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mutations_dvf (
    id                  SERIAL PRIMARY KEY,
    idmutation          BIGINT,
    annee               INTEGER,
    date_mutation       DATE,
    type_bien           VARCHAR(100),
    surface_terrain     NUMERIC(12, 2),
    surface_batie       NUMERIC(12, 2),
    valeur_fonciere     NUMERIC(14, 2),
    prix_bati_m2        NUMERIC(12, 2),
    nb_maison           INTEGER,
    nb_appart           INTEGER,
    nom_commune         VARCHAR(100),
    code_insee          VARCHAR(5) REFERENCES communes(code_insee),
    periode_construction VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_dvf_commune ON mutations_dvf(code_insee);
CREATE INDEX IF NOT EXISTS idx_dvf_annee ON mutations_dvf(annee);

-- ---------------------------------------------------------------------------
-- Permis de construire
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS permis_construire (
    id                  SERIAL PRIMARY KEY,
    commune             VARCHAR(100),
    code_insee          VARCHAR(5),
    date_autorisation   DATE,
    etat_projet         VARCHAR(50),
    superficie_terrain  VARCHAR(30),
    logements_crees     INTEGER,
    logements_collectifs INTEGER,
    logements_1p        INTEGER,
    logements_2p        INTEGER,
    logements_3p        INTEGER,
    logements_4p        INTEGER,
    logements_5p        INTEGER,
    surface_habitable   VARCHAR(30),
    type_habitation     VARCHAR(100)
);

-- ---------------------------------------------------------------------------
-- Logements par parcelle (sans géométrie)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS logements_parcelle (
    id              SERIAL PRIMARY KEY,
    parcelle        VARCHAR(30),
    nb_logement     INTEGER,
    type_logement   VARCHAR(50)
);

-- ---------------------------------------------------------------------------
-- Référentiel bâtiment (colonnes essentielles)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS referentiel_batiment (
    id                  SERIAL PRIMARY KEY,
    id_bati3d           VARCHAR(30),
    parcelle            VARCHAR(30),
    jannat              INTEGER,
    niveau              INTEGER,
    nb_logement         INTEGER,
    nb_maison           INTEGER,
    nb_appart           INTEGER,
    surf_locaux_hab     NUMERIC(12, 2),
    nb_occ_theorique    NUMERIC(8, 2),
    nb_piece            INTEGER
);

-- ---------------------------------------------------------------------------
-- Dataset ML : features par commune pour entraînement
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ml_dataset_commune (
    id                      SERIAL PRIMARY KEY,
    code_insee              VARCHAR(5) REFERENCES communes(code_insee),
    rentree                 INTEGER,
    nb_eleves_maternelle    NUMERIC(10, 2),
    nb_eleves_elementaire   NUMERIC(10, 2),
    nb_classes              NUMERIC(10, 2),
    population              INTEGER,
    pop_0_14_pct            NUMERIC(6, 2),
    natalite                NUMERIC(6, 2),
    densite                 NUMERIC(10, 2),
    log_collectif           INTEGER,
    log_individuel          INTEGER,
    plh_logements           INTEGER,
    nb_mutations            INTEGER,
    nb_logements_parcelle   INTEGER,
    nb_batiments            INTEGER,
    nb_permis_logements     INTEGER
);

-- ---------------------------------------------------------------------------
-- Métadonnées chargement
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS etl_runs (
    id          SERIAL PRIMARY KEY,
    table_name  VARCHAR(100),
    rows_loaded INTEGER,
    status      VARCHAR(20),
    message     TEXT,
    loaded_at   TIMESTAMP DEFAULT NOW()
);
