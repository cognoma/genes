import os
import collections

import pandas


def create_history_df(path):
    """
    Process `gene_history.gz` for Project Cognoma. Returns a dataframe which
    maps old GeneIDs to new GeneIDs. GeneIDs are not mapped to themselves, so
    make sure not to filter all genes without an old GeneID when using this
    dataset.
    """

    renamer = collections.OrderedDict([
        ('Discontinued_GeneID', 'old_entrez_gene_id'),
        ('GeneID', 'new_entrez_gene_id'),
        ('Discontinue_Date', 'date'),
        ('#tax_id', 'tax_id'),
    ])

    history_df = (
        pandas.read_table(path, compression='gzip', na_values='-')
        [list(renamer)]
        .rename(columns=renamer)
        .query("tax_id == 9606")
        .drop(['tax_id'], axis='columns')
        .dropna(subset=['new_entrez_gene_id'])
        .sort_values('old_entrez_gene_id')
    )
    history_df.new_entrez_gene_id = history_df.new_entrez_gene_id.astype(int)

    return history_df


def get_gene_info(path, renamer):
    """
    Read in and process gene information file. Filters genes to Homo sapiens
    with `tax_id == 9606` to remove Neanderthals et al.
    """
    gene_df = (
        pandas.read_table(path,
                          compression='gzip',
                          na_values='-',
                          low_memory=False)
        [list(renamer)]
        .rename(columns=renamer)
        .query("tax_id == 9606")
        .drop(['tax_id'], axis='columns')
        .sort_values('entrez_gene_id')
    )

    return gene_df


def create_gene_df(path):
    """
    Process `Homo_sapiens.gene_info.gz` for Project Cognoma.
    """

    renamer = collections.OrderedDict([
        ('GeneID', 'entrez_gene_id'),
        ('Symbol', 'symbol'),
        ('dbXrefs', 'other_id'),
        ('description', 'description'),
        ('chromosome', 'chromosome'),
        ('type_of_gene', 'gene_type'),
        ('Synonyms', 'synonyms'),
        ('Other_designations', 'aliases'),
        ('#tax_id', 'tax_id'),
    ])

    gene_df = get_gene_info(path=path, renamer=renamer)

    return gene_df


def create_gene_xref_df(path):
    """
    Extract xrefs from `Homo_sapiens.gene_info.gz` for Project Cognoma. Will
    output long data frame of entrez_gene_id by xref identifier.
    """

    renamer = collections.OrderedDict([
        ('GeneID', 'entrez_gene_id'),
        ('dbXrefs', 'other_ids'),
        ('#tax_id', 'tax_id')
    ])

    gene_df = get_gene_info(path=path, renamer=renamer)

    # Isolate each dbXref independently and match to entrez_gene_id
    gene_df = gene_df.pipe(tidy_split, column='other_ids', keep=False)

    # Expand the other ids by first colon delimiter
    other_ids = gene_df['other_ids'].str.split(pat=':', n=1, expand=True)

    # Merge entrez genes to other identifiers
    gene_df = (
        gene_df
        .merge(other_ids, left_index=True, right_index=True)
        .drop(['other_ids'], axis='columns')
        )

    # Rename columns before outputing
    gene_df.columns = ['entrez_gene_id', 'resource', 'identifier']

    return gene_df


def tidy_split(df, column, sep='|', keep=False):
    """
    Split the values of a column and expand so the new DataFrame has one split
    value per row. Filters rows where the column is missing.

    Params
    ------
    df : pandas.DataFrame
        dataframe with the column to split and expand
    column : str
        the column to split and expand
    sep : str
        the string used to split the column's values
    keep : bool
        whether to retain the presplit value as it's own row

    Returns
    -------
    pandas.DataFrame
        Returns a dataframe with the same columns as `df`.
    """
    indexes = list()
    new_values = list()
    df = df.dropna(subset=[column])
    for i, presplit in enumerate(df[column].astype(str)):
        values = presplit.split(sep)
        if keep and len(values) > 1:
            indexes.append(i)
            new_values.append(presplit)
        for value in values:
            indexes.append(i)
            new_values.append(value)
    new_df = df.iloc[indexes, :].copy()
    new_df[column] = new_values
    return new_df


def get_chr_symbol_map(gene_df):
    """
    Create a dataframe for mapping genes to Entrez where all is known is the
    chromosome and symbol. Symbol-chromosome pairs are unique. All approved
    symbols should map and the majority of synonyms should also map. Only
    synonyms that are ambigious within a chromosome are removed.
    """
    primary_df = (
        gene_df
        .loc[:, ['entrez_gene_id', 'chromosome', 'symbol']]
        .pipe(tidy_split, column='chromosome', keep=True)
        )

    synonym_df = (
        gene_df
        .loc[:, ['entrez_gene_id', 'chromosome', 'synonyms']]
        .rename(columns={'synonyms': 'symbol'})
        .pipe(tidy_split, column='symbol', keep=False)
        .pipe(tidy_split, column='chromosome', keep=True)
        .drop_duplicates(['chromosome', 'symbol'], keep=False)
    )

    map_df = (
        primary_df
        .append(synonym_df)
        .drop_duplicates(subset=['chromosome', 'symbol'], keep='first')
        .loc[:, ['symbol', 'chromosome', 'entrez_gene_id']]
        .sort_values(['symbol', 'chromosome'])
    )

    return map_df


if __name__ == '__main__':

    # History mapper
    path = os.path.join('download', 'gene_history.gz')
    history_df = create_history_df(path)

    path = os.path.join('data', 'updater.tsv')
    history_df.to_csv(path, index=False, sep='\t')

    # Genes data
    info_path = os.path.join('download', 'Homo_sapiens.gene_info.gz')
    gene_df = create_gene_df(info_path)

    path = os.path.join('data', 'genes.tsv')
    gene_df.to_csv(path, index=False, sep='\t')

    # Genes xref data
    gene_xref_df = create_gene_xref_df(info_path)

    path = os.path.join('data', 'genes-xrefs.tsv')
    gene_xref_df.to_csv(path, index=False, sep='\t')

    # Chromosome-Symbol Map
    map_df = get_chr_symbol_map(gene_df)
    path = os.path.join('data', 'chromosome-symbol-mapper.tsv')
    map_df.to_csv(path, index=False, sep='\t')
