# Genes for Project Cognoma

This repository creates the set of genes to be used in Project Cognoma. The human subset of Entrez Gene is the basis of Cognoma genes. All genes in Cognoma should be converted to Entrez GeneIDs (using a preferred variable name of `entrez_gene_id`).

When encountering genes in Project Cognoma, identify which of the following approach should be applied:

+ If the input genes are only in symbols, open an issue to discuss mapping options.
+ If the input genes contain chromosome and symbol information, use [`chromosome-symbol-map.tsv`](data/chromosome-symbol-map.tsv) to map the genes to Entrez GeneIDs.
+ If the genes are already encoded as Entrez GeneIDs, update the Gene_IDs to their most recent versions using [`updater.tsv`](data/updater.tsv) and remove GeneIDs that are not in [`genes.tsv`](data/genes.tsv).

## Downloads and data

The raw (downloaded) data is stored in the [`download`](download) directory. [`versions.json`](donwload/versions.json) contains timestamps for the raw data. The raw data is tracked since the Entrez Gene FTP site doesn't version and archive files.

Created data is stored in the [`data`](data) directory. Applications should use the processed data rather than the raw data, if possible. Applications are strongly encouraged to use versioned (commit-hash-containing) links when accessing data from this repository.

## Execution

Use the following commands to run the analysis, inside the environment specified by [`environment.yml`](environment.yml):

```sh
# To run the entire analysis
python 1.download.py
python 2.process.py

# To run just the data processing
python 2.process.py
```

In general, we don't anticipate redownloading the data frequently. If you submit a pull request to create additional datasets, please do not execute `1.download.py`.
