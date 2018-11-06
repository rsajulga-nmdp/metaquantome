from metaquant.util import stats, utils
from metaquant.analysis import functional_analysis as fa
import numpy as np
from metaquant.databases.NCBITaxonomyDb import NCBITaxonomyDb


def function_taxonomy_analysis(df, func_colname, pep_colname, ontology, overwrite, slim_down,
                               lca_colname, query_rank, samp_grps, func_data_dir, tax_data_dir):
    """
    Runs the function-taxonomy interaction analysis. The use of GO terms is required.
    The process is as follows:
    1. Reduce provided dataframe
    2. Normalize dataframe, so each GO term has its own row
    3. (optionally) Map each GO term to its slim version - new column
    4. Drop duplicated peptide-GO (slim) combinations (so we don't double count)
    5. Drop rows with peptides that have an LCA taxon at a higher rank than the desired rank (`des_rank`)
    6. Map each taxon to its desired rank - new column
    7. Group by the new taxon column and the new GO term column
    :param df: joined taxonomy, intensity, and function tables
    :param cog_name: name of COG column in dataframe
    :param lca_colname: name of LCA column in dataframe.
    :param samp_grps: a SampleGroups object for this analysis
    :return: dataframe with taxon-function pairs and their associated total intensity
    """
    # ontology must be go
    if ontology != 'go':
        ValueError('ontology must be "go" for function-taxonomy analysis')

    godb, norm_df = fa.clean_function_df(func_data_dir, df, func_colname, ontology, overwrite, slim_down)
    if slim_down:
        norm_df = fa.slim_down_df(godb, norm_df, func_colname)
    # remove peptide/go-term duplicates
    dedup_df = norm_df.\
        reset_index().\
        drop_duplicates(subset=[pep_colname, func_colname], keep='first').\
        set_index(pep_colname)

    # ---- get rank of lca ----- #

    if not tax_data_dir:
        tax_data_dir = utils.define_ontology_data_dir('taxonomy')

    # load ncbi database
    ncbi = NCBITaxonomyDb(tax_data_dir)
    dedup_df['des_rank'] = dedup_df[lca_colname].apply(lambda x: des_rank_mapper(query_rank, x, ncbi))

    # filter out peptides that are less specific than query rank
    dedup_df = dedup_df[dedup_df['des_rank'] > 0]

    # group by go and new des_rank column - sum by intensity

    # select columns for adding purposes
    df_int = dedup_df[samp_grps.all_intcols + [func_colname, 'des_rank']]

    # group by both cog and lca and add
    grouped = df_int.groupby(by=[func_colname, 'des_rank']).sum(axis=1)

    results = stats.calc_means(grouped, samp_grps)

    # take log of intensities for return
    results[results == 0] = np.nan
    results[samp_grps.all_intcols] = np.log2(results[samp_grps.all_intcols])

    # split the cog/lca index back into 2 columns
    results.reset_index(inplace=True)

    # add go description
    gos = [godb.gofull[x] for x in results[func_colname]]
    results['name'] = [x.name for x in gos]
    results['namespace'] = [x.namespace for x in gos]

    # # translate ids back to names
    taxids = results['des_rank']

    # get ranks
    results['rank'] = [ncbi.get_rank(int(elem)) for elem in taxids]
    results['taxon_name'] = ncbi.convert_taxid_to_name(taxids)

    return results

def des_rank_mapper(des_rank, taxid, ncbi):
    """
    function for mapping a taxid to a desired rank.
    if des_rank is lower than rank of taxid, 0 is returned (to be filtered out later)
    :param des_rank:
    :param taxid:
    :param ncbi:
    :return:
    """
    dict_mapper = ncbi.map_id_to_desired_ranks([des_rank], int(taxid))
    if len(dict_mapper) == 1:
        return dict_mapper[des_rank]
    else:
        return 0


