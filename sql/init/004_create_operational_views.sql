-- Couche operational alignee sur le dump PostgreSQL restaure dans la base source.
-- Les noms sont normalises pour simplifier les scripts ETL.

CREATE SCHEMA IF NOT EXISTS operational;

CREATE OR REPLACE VIEW operational.consultation AS
SELECT
    c."Num_consultation"::TEXT AS id_consultation,
    c."Id_patient"::TEXT AS id_patient,
    c."Date" AS date_consultation,
    c."Code_diag"::TEXT AS diagnostic,
    COALESCE(s."Id_salle", c."Id_prof_sante")::TEXT AS id_etablissement,
    0::NUMERIC(12, 2) AS montant
FROM public."Consultation" c
LEFT JOIN public."Salle" s
    ON s."Num_consultation" = c."Num_consultation";

CREATE OR REPLACE VIEW operational.patient AS
SELECT
    p."Id_patient"::TEXT AS id_patient,
    p."Sexe" AS sexe,
    p."Age" AS age,
    p."Ville" AS ville,
    p."Pays" AS pays
FROM public."Patient" p;

CREATE OR REPLACE VIEW operational.diagnostic AS
SELECT
    d."Code_diag"::TEXT AS code_diag,
    d."Diagnostic" AS libelle
FROM public."Diagnostic" d;

CREATE OR REPLACE VIEW operational.professionnel_de_sante AS
SELECT
    ps."Identifiant"::TEXT AS id_professionnel,
    ps."Nom" AS nom,
    ps."Prenom" AS prenom,
    ps."Profession" AS profession,
    ps."Code_specialite"::TEXT AS code_specialite
FROM public."Professionnel_de_sante" ps;

CREATE OR REPLACE VIEW operational.salle AS
SELECT
    s."Id_salle"::TEXT AS id_salle,
    s."Num_consultation" AS num_consultation,
    s."Code_bloc" AS code_bloc,
    s."Num_etage" AS num_etage,
    s."Num_salle" AS num_salle
FROM public."Salle" s;

CREATE OR REPLACE VIEW operational.mutuelle AS
SELECT
    m."Id_Mut"::INT AS id_mutuelle,
    m."Nom" AS nom,
    m."Adresse" AS adresse
FROM public."Mutuelle" m;
