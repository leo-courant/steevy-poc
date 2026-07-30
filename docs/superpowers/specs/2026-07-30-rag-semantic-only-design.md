# RAG sémantique uniquement — suppression des restes d'exact-search

**Date** : 2026-07-30 · **Statut** : approuvé

## Objectif

Retirer du pipeline RAG tout ce qui servait la recherche exacte (désactivée puis
partiellement supprimée au commit c414b3f), en conservant la recherche
sémantique et les métadonnées de citation affichées dans l'UI.

## Décisions

- **Supprimé** : `Record.metadata`, `_element_fields()` (parsing) ;
  `Chunk.metadata` (chunking) ; clé payload `"fields"` et bloc commenté
  `_lookup_values` (ingest) ; imports Qdrant morts (`FieldCondition`, `Filter`,
  `MatchValue`, `PayloadSchemaType`) et champ mort `SearchHit.record_id`
  (store) ; code commenté d'exact-search, `_unique_hits`, paramètre `retrieval`
  et champ `record=` de `_format_hits` (rag_search).
- **Conservé** : `_element_text()` (les étiquettes `tag: valeur` dans le texte
  embarqué portent la sémantique) ; payload de citation `text`, `source_file`,
  `tag`, `chunk_index` ; affichage source + score dans l'UI Chainlit.
- **Tests** : `test_rag_parsing.py` (2 échecs pré-existants dus à l'ancienne
  API `record.record_id`/`record.metadata`) réécrits vers le contrat
  sémantique.

## Post-déploiement

Relancer `make index` : l'ancienne collection Qdrant contient encore la clé
`fields` dans ses payloads.
